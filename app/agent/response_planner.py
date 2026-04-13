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
    ) -> Dict[str, Any]:
        intent = router_output.get("intent", "general_qa")
        expected_output = router_output.get("expected_output", "text")

        ranked_chunks = self.filter_chunks_for_intent(intent, hybrid_results)
        max_chunks = self.choose_chunk_count(intent)
        selected_chunks = ranked_chunks[:max_chunks]

        primary_chunk = selected_chunks[0] if selected_chunks else None
        supporting_chunks = selected_chunks[1:] if len(selected_chunks) > 1 else []

        plan = {
            "intent": intent,
            "format": expected_output,
            "answer_style": self.infer_answer_style(intent),
            "chunks_to_use": selected_chunks,
            "primary_chunk": primary_chunk,
            "supporting_chunks": supporting_chunks,
            "include_table": router_output.get("needs_table", False),
            "include_diagram": router_output.get("needs_diagram", False),
            "include_image": router_output.get("needs_image", False),
            "max_chunks": max_chunks,
            "process_tags": router_output.get("process_tags", []),
            "voltage_tags": router_output.get("voltage_tags", []),
        }

        return plan


def main():
    from app.agent.query_router import QueryRouter
    from app.retrieval.hybrid_search import HybridSearch

    router = QueryRouter()
    hybrid = HybridSearch()
    planner = ResponsePlanner()

    queries = [
        "duty cycle MIG 240V",
        "polarity setup flux cored",
        "front panel controls",
        "wire spool installation",
        "welder does not function troubleshooting",
    ]

    for query in queries:
        print("\n" + "=" * 80)
        print(f"QUERY: {query}")

        router_output = router.route(query)
        hybrid_results = hybrid.search(query, top_k=5)
        plan = planner.plan(router_output, hybrid_results)

        print("\n[Router Output]")
        print(router_output)

        print("\n[Plan Summary]")
        print({
            "intent": plan["intent"],
            "format": plan["format"],
            "answer_style": plan["answer_style"],
            "include_table": plan["include_table"],
            "include_diagram": plan["include_diagram"],
            "include_image": plan["include_image"],
            "max_chunks": plan["max_chunks"],
            "primary_chunk_id": plan["primary_chunk"]["chunk_id"] if plan["primary_chunk"] else None,
            "supporting_chunk_ids": [c["chunk_id"] for c in plan["supporting_chunks"]],
        })


if __name__ == "__main__":
    main()