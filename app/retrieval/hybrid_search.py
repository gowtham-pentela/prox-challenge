from typing import Dict, List, Any

from app.retrieval.keyword_search import KeywordSearch
from app.retrieval.vector_store import VectorStore


class HybridSearch:
    def __init__(self):
        self.keyword_search = KeywordSearch()
        self.vector_store = VectorStore()
        self.vector_store.load_index()

    def normalize_vector_score(self, distance: float) -> float:
        # Lower FAISS L2 distance is better.
        # Convert to a similarity-like score.
        return 1.0 / (1.0 + distance)

    def metadata_boost(self, query: str, chunk: Dict[str, Any]) -> float:
        query_lower = query.lower()
        boost = 0.0

        if chunk.get("source_priority") == "primary":
            boost += 0.15

        section_title = chunk.get("section_title", "")
        if section_title:
            section_lower = section_title.lower()
            for token in query_lower.split():
                if token in section_lower:
                    boost += 0.05

        for topic in chunk.get("topics", []):
            if topic.replace("_", " ") in query_lower:
                boost += 0.08

        for process_tag in chunk.get("process_tags", []):
            if process_tag.replace("_", " ") in query_lower:
                boost += 0.06

        for voltage_tag in chunk.get("voltage_tags", []):
            if voltage_tag.replace("_", " ") in query_lower:
                boost += 0.06

        content_type = chunk.get("content_type", "")
        if "control" in query_lower or "panel" in query_lower:
            if content_type == "diagram":
                boost += 0.12
        if "troubleshooting" in query_lower or "problem" in query_lower:
            if content_type == "troubleshooting":
                boost += 0.12
        if "setup" in query_lower or "install" in query_lower:
            if content_type == "procedure":
                boost += 0.10
        if "duty" in query_lower or "power" in query_lower or "current" in query_lower:
            if content_type == "specification":
                boost += 0.12
        if chunk.get("content_type") == "specification":
            if any(x in query_lower for x in ["duty", "power", "current", "voltage"]):
                boost += 0.15
        return boost

    def search(self, query: str, top_k: int = 5, keyword_k: int = 8, vector_k: int = 8) -> List[Dict[str, Any]]:
        keyword_results = self.keyword_search.search(query, top_k=keyword_k)
        vector_results = self.vector_store.search(query, top_k=vector_k)

        merged: Dict[str, Dict[str, Any]] = {}

        # Add keyword results
        for rank, chunk in enumerate(keyword_results):
            chunk_id = chunk["chunk_id"]
            keyword_score = 1.0 / (rank + 1)

            if chunk_id not in merged:
                merged[chunk_id] = chunk.copy()
                merged[chunk_id]["keyword_score"] = 0.0
                merged[chunk_id]["vector_score"] = 0.0

            merged[chunk_id]["keyword_score"] = max(
                merged[chunk_id]["keyword_score"], keyword_score
            )

        # Add vector results
        for chunk in vector_results:
            chunk_id = chunk["chunk_id"]
            vector_score = self.normalize_vector_score(chunk["vector_distance"])

            if chunk_id not in merged:
                merged[chunk_id] = chunk.copy()
                merged[chunk_id]["keyword_score"] = 0.0
                merged[chunk_id]["vector_score"] = 0.0

            merged[chunk_id]["vector_score"] = max(
                merged[chunk_id]["vector_score"], vector_score
            )

        # Final combined score
        final_results = []
        for chunk_id, chunk in merged.items():
            keyword_score = chunk.get("keyword_score", 0.0)
            vector_score = chunk.get("vector_score", 0.0)
            boost = self.metadata_boost(query, chunk)

            # Weighting:
            # keyword is strong for exact technical/manual terms
            # vector is strong for semantics/paraphrases
            combined_score = (
                        0.40 * keyword_score +
                        0.60 * vector_score +
                        boost
                    )

            chunk["combined_score"] = combined_score
            final_results.append(chunk)

        final_results.sort(key=lambda x: x["combined_score"], reverse=True)
        return final_results[:top_k]


def main():
    hs = HybridSearch()

    queries = [
        "duty cycle MIG 240V",
        "polarity setup flux cored",
        "front panel controls",
        "wire spool installation",
        "welder does not function troubleshooting",
    ]

    for query in queries:
        print(f"\n\n=== QUERY: {query} ===")
        results = hs.search(query, top_k=3)

        for r in results:
            print("\n---")
            print(r.get("section_title"))
            print(f"Page {r['page_number']}")
            print(f"Combined Score: {r['combined_score']:.4f}")
            print(f"Keyword Score: {r.get('keyword_score', 0):.4f}")
            print(f"Vector Score: {r.get('vector_score', 0):.4f}")
            print(r["text"][:350])


if __name__ == "__main__":
    main()