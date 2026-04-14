from typing import Dict, List, Any, Optional


class ResponsePlanner:
    def __init__(self):
        pass

    def filter_chunks_for_intent(
        self,
        intent: str,
        results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not results:
            return []

        if intent == "specification":
            preferred_types = {"specification"}
        elif intent == "procedure":
            preferred_types = {"procedure"}
        elif intent == "troubleshooting":
            preferred_types = {"troubleshooting"}
        elif intent == "diagram":
            preferred_types = {"diagram", "procedure"}
        elif intent == "controls_lookup":
            preferred_types = {"diagram", "procedure"}
        elif intent == "selection_guidance":
            preferred_types = {"specification", "diagram"}
        else:
            preferred_types = set()

        if not preferred_types:
            return results

        preferred = [
            chunk for chunk in results
            if chunk.get("content_type") in preferred_types
        ]
        fallback = [
            chunk for chunk in results
            if chunk.get("content_type") not in preferred_types
        ]

        return preferred + fallback

    def choose_chunk_count(self, intent: str) -> int:
        if intent == "specification":
            return 2
        if intent == "procedure":
            return 3
        if intent == "troubleshooting":
            return 3
        if intent == "diagram":
            return 2
        if intent == "controls_lookup":
            return 2
        if intent == "selection_guidance":
            return 2
        return 2

    def infer_answer_style(self, intent: str, output_format: str) -> str:
        if output_format == "diagram":
            return "visual_explanatory"
        if output_format == "table":
            return "concise_explanatory"
        if output_format == "image_plus_text":
            if intent == "troubleshooting":
                return "diagnostic"
            if intent == "controls_lookup":
                return "component_explanatory"
            return "visual_explanatory"

        if intent == "specification":
            return "concise_explanatory"
        if intent == "procedure":
            return "instructional"
        if intent == "troubleshooting":
            return "diagnostic"
        if intent == "diagram":
            return "visual_explanatory"
        if intent == "controls_lookup":
            return "component_explanatory"
        if intent == "selection_guidance":
            return "recommendation"

        return "general_explanatory"

    def _normalize_image_results(
        self,
        image_results: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, Any]]:
        return image_results or []

    def _query_suggests_diagram(self, query: str) -> bool:
        query_lower = (query or "").lower()

        diagram_terms = [
            "polarity",
            "wiring",
            "wire setup",
            "cable setup",
            "connection diagram",
            "show connections",
            "how do i connect",
            "dcen",
            "dcep",
            "ground clamp",
            "electrode negative",
            "electrode positive",
            "socket connection",
        ]
        return any(term in query_lower for term in diagram_terms)

    def _query_suggests_image_support(self, query: str) -> bool:
        query_lower = (query or "").lower()

        image_terms = [
            "what is this",
            "what am i looking at",
            "identify",
            "does this look right",
            "defect",
            "weld bead",
            "spatter",
            "porosity",
            "undercut",
            "front panel",
            "control",
            "display",
            "button",
            "knob",
        ]
        return any(term in query_lower for term in image_terms)

    def _decide_format(
        self,
        intent: str,
        expected_output: str,
        query: str,
        include_image: bool,
        include_diagram: bool,
        include_table: bool,
    ) -> str:
        if include_diagram or self._query_suggests_diagram(query):
            return "diagram"

        if include_table:
            return "table"

        if include_image and intent in {"troubleshooting", "controls_lookup", "procedure"}:
            return "image_plus_text"

        if expected_output and expected_output != "text":
            return expected_output

        if intent == "specification":
            return "table"
        if intent == "procedure":
            return "step_by_step"
        if intent == "troubleshooting":
            return "image_plus_text" if include_image else "diagnostic"
        if intent == "controls_lookup":
            return "image_plus_text" if include_image else "text"
        if intent == "diagram":
            return "diagram"
        if intent == "selection_guidance":
            return "table"

        return "text"

    def _build_notes(
        self,
        intent: str,
        final_format: str,
        include_image: bool,
        include_diagram: bool,
        include_table: bool,
        query: str,
    ) -> str:
        notes = []

        if final_format == "diagram":
            notes.append("Prefer diagram-style answer over prose.")
        if final_format == "table":
            notes.append("Prefer structured visual table output.")
        if include_image:
            notes.append("Include image-aware reasoning in final answer.")
        if intent == "troubleshooting":
            notes.append("Emphasize symptom, likely cause, and corrective action.")
        if intent == "procedure":
            notes.append("Keep steps ordered and operational.")
        if self._query_suggests_diagram(query):
            notes.append("Query explicitly suggests connection or polarity visualization.")
        if include_table:
            notes.append("Render settings/spec matrix visually where possible.")
        if include_diagram:
            notes.append("Manual or generated diagram should be prioritized.")

        return " ".join(notes).strip()

    def plan(
        self,
        query: str,
        router_output: Dict[str, Any],
        hybrid_results: List[Dict[str, Any]],
        image_paths: Optional[List[str]] = None,
        image_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        image_paths = image_paths or []
        image_results = self._normalize_image_results(image_results)

        intent = router_output.get("intent", "general_lookup")
        expected_output = router_output.get("expected_output", "text")

        ranked_chunks = self.filter_chunks_for_intent(intent, hybrid_results)
        max_chunks = self.choose_chunk_count(intent)
        selected_chunks = ranked_chunks[:max_chunks]

        primary_chunk = selected_chunks[0] if selected_chunks else None
        supporting_chunks = selected_chunks[1:] if len(selected_chunks) > 1 else []

        include_image = (
            router_output.get("needs_image", False)
            or len(image_results) > 0
            or len(image_paths) > 0
            or self._query_suggests_image_support(query)
        )

        include_diagram = (
            router_output.get("needs_diagram", False)
            or intent == "diagram"
            or self._query_suggests_diagram(query)
        )

        include_table = (
            router_output.get("needs_table", False)
            or intent == "specification"
            or intent == "selection_guidance"
        )

        final_format = self._decide_format(
            intent=intent,
            expected_output=expected_output,
            query=query,
            include_image=include_image,
            include_diagram=include_diagram,
            include_table=include_table,
        )

        answer_style = self.infer_answer_style(intent, final_format)

        plan = {
            "intent": intent,
            "format": final_format,
            "answer_style": answer_style,
            "chunks_to_use": selected_chunks,
            "primary_chunk": primary_chunk,
            "primary_chunk_id": primary_chunk.get("chunk_id") if primary_chunk else None,
            "supporting_chunks": supporting_chunks,
            "include_table": include_table,
            "include_diagram": include_diagram,
            "include_image": include_image,
            "max_chunks": max_chunks,
            "process_tags": router_output.get("process_tags", []),
            "voltage_tags": router_output.get("voltage_tags", []),
            "image_results": image_results,
            "num_image_results": len(image_results) + len(image_paths),
            "generation_mode": "claude",
            "notes": self._build_notes(
                intent=intent,
                final_format=final_format,
                include_image=include_image,
                include_diagram=include_diagram,
                include_table=include_table,
                query=query,
            ),
        }

        return plan