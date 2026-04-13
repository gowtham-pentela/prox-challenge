import json
from typing import List, Dict, Any

from app.agent.query_router import QueryRouter
from app.agent.response_planner import ResponsePlanner
from app.agent.orchestrator import AgentOrchestrator
from app.retrieval.keyword_search import KeywordSearch
from app.retrieval.vector_store import VectorStore
from app.retrieval.hybrid_search import HybridSearch
from app.renderers import TextRenderer, TableRenderer, ImageRenderer, DiagramRenderer
from app.vision.figure_matcher import FigureMatcher
from app.vision.image_analysis import ImageAnalysis


TEST_QUERIES = [
    "duty cycle MIG 240V",
    "polarity setup flux cored",
    "front panel controls",
    "wire spool installation",
    "welder does not function troubleshooting",
    "which process should I use for stainless steel",
]

TEXT_PREVIEW_LEN = 300


def print_divider(title: str = "", char: str = "=") -> None:
    width = 80
    if title:
        padded = f" {title} "
        remaining = max(0, width - len(padded))
        left = remaining // 2
        right = remaining - left
        print(f"\n{char * left}{padded}{char * right}")
    else:
        print("\n" + char * width)


def preview_text(text: str, max_len: int = TEXT_PREVIEW_LEN) -> str:
    text = " ".join(text.split())
    return text[:max_len] + ("..." if len(text) > max_len else "")


def safe_get(result: Dict[str, Any], key: str, default: Any = None) -> Any:
    return result.get(key, default)


def get_renderer_for_format(format_name: str):
    if format_name == "table":
        return TableRenderer()
    if format_name == "diagram":
        return DiagramRenderer()
    if format_name == "image_plus_text":
        return ImageRenderer()
    if format_name == "step_by_step":
        return TextRenderer()
    return TextRenderer()


def print_router_output(router_output: Dict[str, Any]) -> None:
    print_divider("Router Output", "-")
    print(json.dumps(router_output, indent=2, ensure_ascii=False))


def print_plan_output(plan: Dict[str, Any]) -> None:
    summary = {
        "intent": plan.get("intent"),
        "format": plan.get("format"),
        "answer_style": plan.get("answer_style"),
        "include_table": plan.get("include_table"),
        "include_diagram": plan.get("include_diagram"),
        "include_image": plan.get("include_image"),
        "max_chunks": plan.get("max_chunks"),
        "process_tags": plan.get("process_tags", []),
        "voltage_tags": plan.get("voltage_tags", []),
        "primary_chunk_id": plan["primary_chunk"]["chunk_id"] if plan.get("primary_chunk") else None,
        "supporting_chunk_ids": [
            chunk["chunk_id"] for chunk in plan.get("supporting_chunks", [])
        ],
        "num_image_results": len(plan.get("image_results", [])),
    }

    print_divider("Response Plan", "-")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def print_render_output(render_output: Dict[str, Any]) -> None:
    print_divider("Render Output", "-")
    print(json.dumps(render_output, indent=2, ensure_ascii=False))


def print_image_results(image_results: List[Dict[str, Any]]) -> None:
    print_divider("Vision Matches", "-")
    if not image_results:
        print("No matched images.")
        return
    print(json.dumps(image_results, indent=2, ensure_ascii=False))


def print_search_results(
    label: str,
    results: List[Dict[str, Any]],
    extra_fields: List[str] = None,
) -> None:
    extra_fields = extra_fields or []
    print_divider(label, "-")

    if not results:
        print("No results.")
        return

    for idx, result in enumerate(results, start=1):
        print(f"\nResult #{idx}")
        print(f"chunk_id:        {safe_get(result, 'chunk_id')}")
        print(f"section_title:   {safe_get(result, 'section_title')}")
        print(f"page_number:     {safe_get(result, 'page_number')}")
        print(f"source_file:     {safe_get(result, 'source_file')}")
        print(f"content_type:    {safe_get(result, 'content_type')}")
        print(f"source_priority: {safe_get(result, 'source_priority')}")
        print(f"topics:          {safe_get(result, 'topics', [])}")
        print(f"process_tags:    {safe_get(result, 'process_tags', [])}")
        print(f"voltage_tags:    {safe_get(result, 'voltage_tags', [])}")

        for field in extra_fields:
            if field in result:
                value = result[field]
                if isinstance(value, float):
                    print(f"{field}: {value:.4f}")
                else:
                    print(f"{field}: {value}")

        print("text_preview:")
        print(preview_text(safe_get(result, "text", "")))


def basic_assertions(
    query: str,
    router_output: Dict[str, Any],
    keyword_results: List[Dict[str, Any]],
    vector_results: List[Dict[str, Any]],
    hybrid_results: List[Dict[str, Any]],
    image_results: List[Dict[str, Any]],
    plan: Dict[str, Any],
    render_output: Dict[str, Any],
    orchestrator_output: Dict[str, Any],
) -> None:
    print_divider("Basic Assertions", "-")

    assert "intent" in router_output
    assert "expected_output" in router_output

    assert isinstance(keyword_results, list)
    assert isinstance(vector_results, list)
    assert isinstance(hybrid_results, list)
    assert isinstance(image_results, list)

    if vector_results:
        assert "vector_distance" in vector_results[0]

    if hybrid_results:
        assert "combined_score" in hybrid_results[0]

    assert "format" in plan
    assert "answer_style" in plan
    assert "chunks_to_use" in plan

    assert "render_type" in render_output
    assert "title" in render_output
    assert "content" in render_output

    assert "final_answer" in orchestrator_output
    assert isinstance(orchestrator_output["final_answer"], str)
    assert len(orchestrator_output["final_answer"]) > 0

    q = query.lower()

    if "duty cycle" in q:
        assert router_output["intent"] == "specification"
        assert plan["format"] == "table"
        assert render_output["render_type"] == "table"

    if "polarity" in q:
        assert router_output["intent"] == "diagram"
        assert plan["format"] == "diagram"
        assert render_output["render_type"] == "diagram"

    if "front panel" in q:
        assert router_output["intent"] == "controls_lookup"
        assert plan["format"] == "image_plus_text"
        assert render_output["render_type"] == "image_plus_text"

    if "wire spool" in q:
        assert router_output["intent"] == "procedure"
        assert plan["format"] == "step_by_step"
        assert render_output["render_type"] == "text"

    if "welder does not function" in q or "troubleshooting" in q:
        assert router_output["intent"] == "troubleshooting"
        assert plan["format"] == "image_plus_text"
        assert render_output["render_type"] == "image_plus_text"

    if "which process" in q:
        assert router_output["intent"] == "selection_guidance"
        assert plan["format"] == "table"
        assert render_output["render_type"] == "table"

    print("All basic assertions passed.")


def run_query(
    query: str,
    router: QueryRouter,
    planner: ResponsePlanner,
    keyword_search: KeywordSearch,
    vector_store: VectorStore,
    hybrid_search: HybridSearch,
    figure_matcher: FigureMatcher,
    image_analysis: ImageAnalysis,
    orchestrator: AgentOrchestrator,
) -> None:
    print_divider(f"QUERY: {query}")

    router_output = router.route(query)
    keyword_results = keyword_search.search(query, top_k=3)
    vector_results = vector_store.search(query, top_k=3)
    hybrid_results = hybrid_search.search(
    query,
    router_output=router_output,
    top_k=5
)
    
    raw_image_results = figure_matcher.match(query, top_k=3)
    image_results = image_analysis.summarize_images(raw_image_results)

    plan = planner.plan(router_output, hybrid_results, image_results=image_results)

    renderer = get_renderer_for_format(plan["format"])
    render_output = renderer.render(plan)

    orchestrator_output = orchestrator.answer(query, use_claude=False)

    print_router_output(router_output)
    print_search_results("Keyword Search Results", keyword_results)
    print_search_results("Vector Search Results", vector_results, extra_fields=["vector_distance"])
    print_search_results(
        "Hybrid Search Results",
        hybrid_results,
        extra_fields=["keyword_score", "vector_score", "combined_score"],
    )
    print_image_results(image_results)
    print_plan_output(plan)
    print_render_output(render_output)

    print_divider("Orchestrator Final Answer", "-")
    print(orchestrator_output["final_answer"])

    basic_assertions(
        query=query,
        router_output=router_output,
        keyword_results=keyword_results,
        vector_results=vector_results,
        hybrid_results=hybrid_results,
        image_results=image_results,
        plan=plan,
        render_output=render_output,
        orchestrator_output=orchestrator_output,
    )


def main() -> None:
    print_divider("Initializing Components")

    router = QueryRouter()
    planner = ResponsePlanner()
    keyword_search = KeywordSearch()

    vector_store = VectorStore()
    vector_store.load_index()

    hybrid_search = HybridSearch()
    figure_matcher = FigureMatcher()
    image_analysis = ImageAnalysis()
    orchestrator = AgentOrchestrator()

    print("Router initialized.")
    print("Response planner initialized.")
    print("Keyword search initialized.")
    print("Vector store loaded.")
    print("Hybrid search initialized.")
    print("Figure matcher initialized.")
    print("Image analysis initialized.")
    print("Orchestrator initialized.")

    for query in TEST_QUERIES:
        run_query(
            query=query,
            router=router,
            planner=planner,
            keyword_search=keyword_search,
            vector_store=vector_store,
            hybrid_search=hybrid_search,
            figure_matcher=figure_matcher,
            image_analysis=image_analysis,
            orchestrator=orchestrator,
        )

    print_divider("Smoke Test Complete")
    print("Everything ran successfully.")


if __name__ == "__main__":
    main()