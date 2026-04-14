from typing import Any, Dict, List


class QueryRouter:
    def __init__(self):
        pass

    def route(self, query: str, visual_analysis: str = "") -> Dict[str, Any]:
        combined = "{0}\n{1}".format(query or "", visual_analysis or "").lower()

        intent = self._infer_intent(combined)
        query_type = self._infer_query_type(combined)
        process_tags = self._extract_process_tags(combined)
        voltage_tags = self._extract_voltage_tags(combined)

        needs_diagram = self._needs_diagram(intent, combined)
        needs_table = self._needs_table(intent, combined)
        needs_image = self._needs_image(intent, combined, bool(visual_analysis.strip()) if visual_analysis else False)

        expected_output = self._infer_expected_output(
            intent=intent,
            text=combined,
            needs_diagram=needs_diagram,
            needs_table=needs_table,
            needs_image=needs_image,
        )

        return {
            "intent": intent,
            "query_type": query_type,
            "expected_output": expected_output,
            "needs_diagram": needs_diagram,
            "needs_table": needs_table,
            "needs_image": needs_image,
            "process_tags": process_tags,
            "voltage_tags": voltage_tags,
            "visual_analysis_used": bool(visual_analysis.strip()) if visual_analysis else False,
            "image_evidence_present": bool(visual_analysis.strip()) if visual_analysis else False,
            "notes": self._build_notes(
                intent=intent,
                text=combined,
                expected_output=expected_output,
                needs_diagram=needs_diagram,
                needs_table=needs_table,
                needs_image=needs_image,
            ),
        }

    def _infer_intent(self, text: str) -> str:
        if any(
            term in text
            for term in [
                "duty cycle",
                "specification",
                "specifications",
                "amp",
                "amperage",
                "voltage range",
                "current input",
                "power input",
                "current output",
                "welding current range",
                "rated duty cycle",
            ]
        ):
            return "specification"

        if any(
            term in text
            for term in [
                "polarity",
                "dcen",
                "dcep",
                "setup",
                "install",
                "wire spool",
                "feed roller",
                "feed tensioner",
                "idler arm",
                "how do i connect",
                "how to connect",
                "procedure",
                "connect the cable",
                "connection setup",
            ]
        ):
            return "procedure"

        if any(
            term in text
            for term in [
                "troubleshooting",
                "does not function",
                "won't start",
                "will not start",
                "warning screen",
                "bad weld",
                "weld defect",
                "spatter",
                "porosity",
                "undercut",
                "burn through",
                "burn-through",
                "problem",
                "issue",
                "not working",
            ]
        ):
            return "troubleshooting"

        if any(
            term in text
            for term in [
                "front panel",
                "control",
                "knob",
                "display",
                "button",
                "socket",
                "controls lookup",
                "what control is this",
                "what am i looking at",
            ]
        ):
            return "controls_lookup"

        if any(term in text for term in ["diagram", "schematic", "wiring", "connection diagram"]):
            return "diagram"

        if any(
            term in text
            for term in [
                "which process",
                "which wire",
                "selection chart",
                "compatibility",
                "recommended setting",
                "recommended process",
            ]
        ):
            return "selection_guidance"

        return "general_lookup"

    def _infer_query_type(self, text: str) -> str:
        if any(term in text for term in ["what", "which", "identify"]):
            return "lookup"

        if any(term in text for term in ["how", "steps", "setup", "install", "connect"]):
            return "instruction"

        if any(term in text for term in ["why", "problem", "does not function", "not working", "issue"]):
            return "diagnostic"

        return "mixed"

    def _extract_process_tags(self, text: str) -> List[str]:
        tags = []

        if "mig" in text:
            tags.append("mig")
        if "flux" in text or "flux-cored" in text or "flux cored" in text:
            tags.append("flux_cored")
        if "tig" in text:
            tags.append("tig")
        if "stick" in text:
            tags.append("stick")

        return tags

    def _extract_voltage_tags(self, text: str) -> List[str]:
        tags = []

        if "120v" in text or "120 v" in text or "120vac" in text or "120 vac" in text:
            tags.append("120V")
        if "240v" in text or "240 v" in text or "240vac" in text or "240 vac" in text:
            tags.append("240V")

        return tags

    def _needs_diagram(self, intent: str, text: str) -> bool:
        if intent == "diagram":
            return True

        if any(
            term in text
            for term in [
                "polarity",
                "wiring",
                "schematic",
                "connection diagram",
                "show connections",
                "how do i connect",
                "dcen",
                "dcep",
                "ground clamp",
                "positive socket",
                "negative socket",
            ]
        ):
            return True

        return False

    def _needs_table(self, intent: str, text: str) -> bool:
        if intent in {"specification", "selection_guidance"}:
            return True

        if any(
            term in text
            for term in [
                "duty cycle",
                "settings matrix",
                "compatibility table",
                "selection chart",
                "specification table",
                "process comparison",
                "voltage comparison",
            ]
        ):
            return True

        return False

    def _needs_image(self, intent: str, text: str, has_visual_analysis: bool) -> bool:
        if has_visual_analysis:
            return True

        if intent in {"controls_lookup", "troubleshooting"}:
            return True

        if any(
            term in text
            for term in [
                "what am i looking at",
                "identify this",
                "does this look right",
                "weld defect",
                "weld bead",
                "front panel",
                "knob",
                "display",
                "button",
                "socket",
                "spatter",
                "porosity",
                "undercut",
            ]
        ):
            return True

        return False

    def _infer_expected_output(
        self,
        intent: str,
        text: str,
        needs_diagram: bool,
        needs_table: bool,
        needs_image: bool,
    ) -> str:
        if needs_diagram:
            return "diagram"

        if needs_table:
            return "table"

        if needs_image and intent in {"controls_lookup", "troubleshooting", "procedure"}:
            return "image_plus_text"

        if intent == "procedure":
            return "step_by_step"

        if intent == "troubleshooting":
            return "diagnostic"

        return "text"

    def _build_notes(
        self,
        intent: str,
        text: str,
        expected_output: str,
        needs_diagram: bool,
        needs_table: bool,
        needs_image: bool,
    ) -> str:
        notes = []

        if intent == "procedure":
            notes.append("Procedure-style query detected.")
        if intent == "troubleshooting":
            notes.append("Troubleshooting flow may need symptom-to-cause mapping.")
        if intent == "specification":
            notes.append("Specification query should stay grounded in manual values.")
        if intent == "controls_lookup":
            notes.append("Controls lookup may benefit from figure grounding.")

        if needs_diagram:
            notes.append("Prefer visual connection diagram over prose.")
        if needs_table:
            notes.append("Prefer structured table or matrix output.")
        if needs_image:
            notes.append("Image-aware reasoning may improve answer quality.")

        if "dcen" in text or "dcep" in text:
            notes.append("Polarity-sensitive query detected.")
        if "240v" in text or "120v" in text:
            notes.append("Voltage-specific retrieval should be preserved.")

        if not notes:
            notes.append("Standard routing applied.")

        return " ".join(notes).strip()