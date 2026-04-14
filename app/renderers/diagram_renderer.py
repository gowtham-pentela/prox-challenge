from typing import Dict, Any, List, Optional


class DiagramRenderer:
    def __init__(self):
        pass

    def _normalize_page(self, chunk: Dict[str, Any]) -> Optional[int]:
        return chunk.get("page") or chunk.get("page_number")

    def _get_reference_pages(self, plan: Dict[str, Any]) -> List[int]:
        pages = []
        primary = plan.get("primary_chunk")
        supporting = plan.get("supporting_chunks", [])

        if primary and self._normalize_page(primary) is not None:
            pages.append(self._normalize_page(primary))

        for chunk in supporting:
            page = self._normalize_page(chunk)
            if page is not None and page not in pages:
                pages.append(page)

        return pages

    def _infer_process(self, query: str, plan: Dict[str, Any]) -> str:
        query_lower = (query or "").lower()
        process_tags = [str(tag).lower() for tag in plan.get("process_tags", [])]

        if "flux" in query_lower or "flux-cored" in query_lower or "fcaw" in query_lower:
            return "flux_cored"
        if "mig" in query_lower:
            return "mig"
        if "stick" in query_lower:
            return "stick"
        if "tig" in query_lower:
            return "tig"

        for tag in process_tags:
            if "flux" in tag:
                return "flux_cored"
            if tag == "mig":
                return "mig"
            if tag == "stick":
                return "stick"
            if tag == "tig":
                return "tig"

        primary = plan.get("primary_chunk") or {}
        text = (primary.get("text", "") or "").lower()

        if "dcen" in text or "flux-cored" in text:
            return "flux_cored"
        if "dcep" in text and "mig" in text:
            return "mig"
        if "electrode holder" in text:
            return "stick"
        if "torch" in text and "gas" in text:
            return "tig"

        return "generic"

    def _build_flux_cored_diagram(self) -> Dict[str, Any]:
        ascii_diagram = """
Flux-Cored Polarity Setup (DCEN)

        FRONT OF WELDER
   ┌───────────────────────────┐
   │         (+)     (−)       │
   └──────────┬───────┬────────┘
              │       │
              │       └──────── Wire Feed Power Cable
              │                 → MIG Gun
              │
              └──────────────── Ground Clamp Cable
                                → Workpiece

Polarity:
- Ground Clamp Cable → Positive (+)
- Wire Feed Power Cable → Negative (−)
- Mode: DCEN
""".strip()

        return {
            "process": "flux_cored",
            "polarity": "DCEN",
            "connections": [
                {
                    "component": "Ground Clamp Cable",
                    "connect_to": "Positive (+)",
                    "role": "Work return path",
                },
                {
                    "component": "Wire Feed Power Cable",
                    "connect_to": "Negative (-)",
                    "role": "Feeds electrode through MIG gun",
                },
            ],
            "ascii_diagram": ascii_diagram,
        }

    def _build_mig_diagram(self) -> Dict[str, Any]:
        ascii_diagram = """
MIG Polarity Setup (DCEP)

        FRONT OF WELDER
   ┌───────────────────────────┐
   │         (+)     (−)       │
   └──────────┬───────┬────────┘
              │       │
              │       └──────── Ground Clamp Cable
              │                 → Workpiece
              │
              └──────────────── Wire Feed Power Cable
                                → MIG Gun

Polarity:
- Wire Feed Power Cable → Positive (+)
- Ground Clamp Cable → Negative (−)
- Mode: DCEP
""".strip()

        return {
            "process": "mig",
            "polarity": "DCEP",
            "connections": [
                {
                    "component": "Wire Feed Power Cable",
                    "connect_to": "Positive (+)",
                    "role": "Electrode positive for MIG welding",
                },
                {
                    "component": "Ground Clamp Cable",
                    "connect_to": "Negative (-)",
                    "role": "Work return path",
                },
            ],
            "ascii_diagram": ascii_diagram,
        }

    def _build_stick_diagram(self) -> Dict[str, Any]:
        ascii_diagram = """
Stick Welding Setup

        FRONT OF WELDER
   ┌───────────────────────────┐
   │         (+)     (−)       │
   └──────────┬───────┬────────┘
              │       │
              │       └──────── Ground Clamp Cable
              │                 → Workpiece
              │
              └──────────────── Electrode Holder Cable
                                → Stick Electrode

Note:
- Actual polarity may depend on electrode type.
- Confirm electrode recommendation before welding.
""".strip()

        return {
            "process": "stick",
            "polarity": "Depends on electrode",
            "connections": [
                {
                    "component": "Electrode Holder Cable",
                    "connect_to": "Typically Positive (+), depending on electrode",
                    "role": "Carries current to stick electrode",
                },
                {
                    "component": "Ground Clamp Cable",
                    "connect_to": "Opposite terminal",
                    "role": "Work return path",
                },
            ],
            "ascii_diagram": ascii_diagram,
        }

    def _build_tig_diagram(self) -> Dict[str, Any]:
        ascii_diagram = """
TIG Setup Overview

        FRONT OF WELDER
   ┌───────────────────────────┐
   │         (+)     (−)       │
   └──────────┬───────┬────────┘
              │       │
              │       └──────── TIG Torch / Power Lead
              │                 + shielding gas
              │
              └──────────────── Ground Clamp Cable
                                → Workpiece

Note:
- Confirm exact polarity and gas setup from the selected TIG mode.
""".strip()

        return {
            "process": "tig",
            "polarity": "Check selected TIG configuration",
            "connections": [
                {
                    "component": "TIG Torch / Power Lead",
                    "connect_to": "Process-dependent terminal",
                    "role": "Torch current path",
                },
                {
                    "component": "Ground Clamp Cable",
                    "connect_to": "Opposite terminal",
                    "role": "Work return path",
                },
            ],
            "ascii_diagram": ascii_diagram,
        }

    def _build_generic_diagram(self) -> Dict[str, Any]:
        ascii_diagram = """
Generic Connection View

        FRONT OF WELDER
   ┌───────────────────────────┐
   │         (+)     (−)       │
   └──────────┬───────┬────────┘
              │       │
              │       └──────── Output Cable B
              │
              └──────────────── Output Cable A

Check process-specific polarity in the manual before welding.
""".strip()

        return {
            "process": "generic",
            "polarity": "Unknown",
            "connections": [
                {
                    "component": "Output Cable A",
                    "connect_to": "One output terminal",
                    "role": "Process-specific",
                },
                {
                    "component": "Output Cable B",
                    "connect_to": "Other output terminal",
                    "role": "Process-specific",
                },
            ],
            "ascii_diagram": ascii_diagram,
        }

    def _build_steps(self, process: str) -> List[str]:
        if process == "flux_cored":
            return [
                "Set the machine for flux-cored welding.",
                "Connect the Ground Clamp Cable to Positive (+).",
                "Connect the Wire Feed Power Cable to Negative (-).",
                "Lock both cable connectors securely by twisting clockwise.",
                "Verify the feed roller uses the knurled groove for flux-cored wire.",
            ]
        if process == "mig":
            return [
                "Set the machine for MIG welding.",
                "Connect the Wire Feed Power Cable to Positive (+).",
                "Connect the Ground Clamp Cable to Negative (-).",
                "Lock both cable connectors securely by twisting clockwise.",
                "Confirm the feed roller and wire type match the selected MIG setup.",
            ]
        if process == "stick":
            return [
                "Select Stick mode.",
                "Connect the electrode holder cable to the terminal recommended by the electrode.",
                "Connect the ground clamp to the opposite terminal.",
                "Attach the ground clamp securely to the workpiece.",
            ]
        if process == "tig":
            return [
                "Select TIG mode.",
                "Connect the TIG torch lead as required by the selected TIG configuration.",
                "Connect the ground clamp to the opposite terminal.",
                "Verify shielding gas connection before welding.",
            ]
        return [
            "Identify the active welding process.",
            "Check the manual for the correct polarity.",
            "Connect each output cable to the correct terminal.",
            "Lock connectors securely before operation.",
        ]

    def render(
        self,
        plan: Dict[str, Any],
        hybrid_results: Optional[List[Dict[str, Any]]] = None,
        query: str = "",
        image_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        hybrid_results = hybrid_results or []
        image_paths = image_paths or []

        process = self._infer_process(query, plan)

        if process == "flux_cored":
            diagram_payload = self._build_flux_cored_diagram()
        elif process == "mig":
            diagram_payload = self._build_mig_diagram()
        elif process == "stick":
            diagram_payload = self._build_stick_diagram()
        elif process == "tig":
            diagram_payload = self._build_tig_diagram()
        else:
            diagram_payload = self._build_generic_diagram()

        reference_pages = self._get_reference_pages(plan)

        evidence_preview = []
        for chunk in (plan.get("chunks_to_use") or hybrid_results)[:3]:
            evidence_preview.append({
                "chunk_id": chunk.get("chunk_id"),
                "section_title": chunk.get("section_title"),
                "page": self._normalize_page(chunk),
                "content_type": chunk.get("content_type"),
                "text_preview": " ".join((chunk.get("text", "") or "").split())[:220],
            })

        return {
            "render_type": "diagram",
            "title": "{0} Connection Diagram".format(
                process.replace("_", " ").title()
            ),
            "query": query,
            "diagram_kind": "polarity_connection",
            "diagram": diagram_payload,
            "steps": self._build_steps(process),
            "reference_pages": reference_pages,
            "evidence_preview": evidence_preview,
            "instructions_for_llm": [
                "Preserve the polarity mapping exactly.",
                "Prefer the diagram over prose for the main explanation.",
                "Use the steps to explain setup order.",
                "If manual evidence is incomplete, clearly say which part is inferred versus confirmed.",
            ],
            "metadata": {
                "include_diagram": True,
                "answer_style": plan.get("answer_style"),
                "chunk_count": len(plan.get("chunks_to_use", [])),
                "num_user_images": len(image_paths),
            },
        }