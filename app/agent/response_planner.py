from typing import Dict, List, Any


class ResponsePlanner:
    def __init__(self):
        pass

    def filter_chunks_for_intent(self, intent: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
            preferred_types = {"diagram"}
        elif intent == "selection_guidance":
            preferred_types = {"specification", "diagram"}
        else:
            preferred_types = set()

        if not preferred_types:
            return results

        preferred = [chunk for chunk in results if chunk.get("content_type") in preferred_types]
        fallback = [chunk for chunk in results if chunk.get("content_type") not in preferred_types]

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

    def infer_answer_style(self, intent: str) -> str:
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

    def plan(
        self,
        router_output: Dict[str, Any],
        hybrid_results: List[Dict[str, Any]],
        image_results: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        image_results = image_results or []

        intent = router_output.get("intent", "general_qa")
        expected_output = router_output.get("expected_output", "text")

        ranked_chunks = self.filter_chunks_for_intent(intent, hybrid_results)
        max_chunks = self.choose_chunk_count(intent)
        selected_chunks = ranked_chunks[:max_chunks]

        primary_chunk = selected_chunks[0] if selected_chunks else None
        supporting_chunks = selected_chunks[1:] if len(selected_chunks) > 1 else []

        # Vision-aware flags
        include_image = router_output.get("needs_image", False) or len(image_results) > 0
        include_diagram = router_output.get("needs_diagram", False)
        include_table = router_output.get("needs_table", False)

        plan = {
            "intent": intent,
            "format": expected_output,
            "answer_style": self.infer_answer_style(intent),
            "chunks_to_use": selected_chunks,
            "primary_chunk": primary_chunk,
            "supporting_chunks": supporting_chunks,
            "include_table": include_table,
            "include_diagram": include_diagram,
            "include_image": include_image,
            "max_chunks": max_chunks,
            "process_tags": router_output.get("process_tags", []),
            "voltage_tags": router_output.get("voltage_tags", []),
            "image_results": image_results,
        }

        return plan