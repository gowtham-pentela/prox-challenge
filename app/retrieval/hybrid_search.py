import json
from typing import Dict, List, Any

from app.config import DATA_DIR
from app.retrieval.keyword_search import KeywordSearch
from app.retrieval.vector_store import VectorStore


class HybridSearch:
    def __init__(self):
        self.keyword_search = KeywordSearch()
        self.vector_store = VectorStore()
        self.vector_store.load_index()

        metadata_path = DATA_DIR / "indexes" / "chunks_metadata.json"
        if not metadata_path.exists():
            raise FileNotFoundError(f"Missing metadata file: {metadata_path}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.chunk_metadata = json.load(f)

        self.metadata_by_chunk_id = {
            item["chunk_id"]: item for item in self.chunk_metadata
        }

    def _normalize_vector_distance(self, distance: float) -> float:
        """
        Convert vector distance into a similarity-like score.
        Lower distance becomes higher score.
        """
        return 1.0 / (1.0 + distance)

    def _boost_by_intent(self, result: Dict[str, Any], intent: str) -> float:
        content_type = result.get("content_type")
        boost = 0.0

        if intent == "specification":
            if content_type == "specification":
                boost += 3.0
            elif content_type == "troubleshooting":
                boost -= 1.5

        elif intent == "procedure":
            if content_type == "procedure":
                boost += 2.0
            elif content_type == "troubleshooting":
                boost -= 0.5

        elif intent == "troubleshooting":
            if content_type == "troubleshooting":
                boost += 2.0
            elif content_type == "specification":
                boost -= 0.5

        elif intent == "diagram":
            if content_type == "diagram":
                boost += 2.0
            elif content_type == "procedure":
                boost += 1.0

        elif intent == "controls_lookup":
            if content_type == "diagram":
                boost += 2.0
            elif content_type == "procedure":
                boost += 0.5

        elif intent == "selection_guidance":
            if content_type == "specification":
                boost += 2.0
            elif content_type == "diagram":
                boost += 1.2
            elif content_type == "troubleshooting":
                boost -= 0.5

        return boost

    def _boost_by_tags(
        self,
        result: Dict[str, Any],
        process_tags: List[str],
        voltage_tags: List[str],
    ) -> float:
        boost = 0.0

        result_process_tags = set(result.get("process_tags", []))
        result_voltage_tags = set(result.get("voltage_tags", []))

        for tag in process_tags:
            if tag in result_process_tags:
                boost += 0.8

        for tag in voltage_tags:
            if tag in result_voltage_tags:
                boost += 1.0

        return boost

    def _merge_result(
        self,
        base: Dict[str, Any],
        keyword_score: float,
        vector_score: float,
        combined_score: float,
    ) -> Dict[str, Any]:
        merged = base.copy()
        merged["keyword_score"] = round(keyword_score, 4)
        merged["vector_score"] = round(vector_score, 4)
        merged["combined_score"] = round(combined_score, 4)
        return merged

    def search(
        self,
        query: str,
        router_output: Dict[str, Any] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        router_output = router_output or {}

        intent = router_output.get("intent", "general_qa")
        print("HYBRID INTENT:", intent)

        process_tags = router_output.get("process_tags", [])
        voltage_tags = router_output.get("voltage_tags", [])

        keyword_results = self.keyword_search.search(query, top_k=top_k * 2)
        vector_results = self.vector_store.search(query, top_k=top_k * 2)

        keyword_scores: Dict[str, float] = {}
        vector_scores: Dict[str, float] = {}

        for rank, result in enumerate(keyword_results):
            chunk_id = result["chunk_id"]
            keyword_scores[chunk_id] = 1.0 / (rank + 1)

        for result in vector_results:
            chunk_id = result["chunk_id"]
            distance = result.get("vector_distance", 999.0)
            vector_scores[chunk_id] = self._normalize_vector_distance(distance)

        all_chunk_ids = set(keyword_scores.keys()) | set(vector_scores.keys())
        combined_results: List[Dict[str, Any]] = []

        for chunk_id in all_chunk_ids:
            base = self.metadata_by_chunk_id.get(chunk_id)
            if not base:
                continue

            keyword_score = keyword_scores.get(chunk_id, 0.0)
            vector_score = vector_scores.get(chunk_id, 0.0)

            combined_score = (0.6 * keyword_score) + (0.4 * vector_score)
            combined_score += self._boost_by_intent(base, intent)
            combined_score += self._boost_by_tags(base, process_tags, voltage_tags)

            merged = self._merge_result(
                base=base,
                keyword_score=keyword_score,
                vector_score=vector_score,
                combined_score=combined_score,
            )
            combined_results.append(merged)

        combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
        return combined_results[:top_k]


if __name__ == "__main__":
    from app.agent.query_router import QueryRouter

    router = QueryRouter()
    hybrid = HybridSearch()

    queries = [
        "duty cycle MIG 240V",
        "polarity setup flux cored",
        "front panel controls",
        "wire spool installation",
        "welder does not function troubleshooting",
        "which process should I use for stainless steel",
    ]

    for query in queries:
        print("\n" + "=" * 100)
        print("QUERY:", query)

        router_output = router.route(query)
        print("ROUTER:", router_output)

        results = hybrid.search(query, router_output=router_output, top_k=5)
        for idx, result in enumerate(results, start=1):
            print(
                f"{idx}. {result['chunk_id']} | "
                f"{result.get('section_title')} | "
                f"page {result.get('page_number')} | "
                f"{result.get('content_type')} | "
                f"combined={result.get('combined_score')}"
            )