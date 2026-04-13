from app.retrieval.keyword_search import KeywordSearch
from app.retrieval.vector_store import VectorStore
from app.retrieval.hybrid_search import HybridSearch

ks = KeywordSearch()
vs = VectorStore()
vs.load_index()
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

    print("\n[Keyword Search Results]")
    keyword_results = ks.search(query, top_k=2)
    for r in keyword_results:
        print("\n---")
        print(r["section_title"])
        print(f"Page {r['page_number']}")
        print(r["text"][:250])

    print("\n[Vector Search Results]")
    vector_results = vs.search(query, top_k=2)
    for r in vector_results:
        print("\n---")
        print(r["section_title"])
        print(f"Page {r['page_number']}")
        print(f"Distance: {r['vector_distance']:.4f}")
        print(r["text"][:250])

    print("\n[Hybrid Search Results]")
    hybrid_results = hs.search(query, top_k=3)
    for r in hybrid_results:
        print("\n---")
        print(r["section_title"])
        print(f"Page {r['page_number']}")
        print(f"Combined Score: {r['combined_score']:.4f}")
        print(r["text"][:250])