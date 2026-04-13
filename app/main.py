import sys
from pathlib import Path

# Ensure project root is on Python path before importing app modules
CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_FILE.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Dict, Any

import streamlit as st

from app.agent.orchestrator import AgentOrchestrator


st.set_page_config(
    page_title="Vulcan OmniPro 220 Agent",
    page_icon="⚡",
    layout="wide",
)


SAMPLE_QUERIES = [
    "duty cycle MIG 240V",
    "polarity setup flux cored",
    "front panel controls",
    "wire spool installation",
    "welder does not function troubleshooting",
    "which process should I use for stainless steel",
]


@st.cache_resource
def get_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator()


def render_header() -> None:
    st.title("Vulcan OmniPro 220 Multimodal Agent")
    st.caption(
        "Ask technical questions about the welder manual. "
        "The system uses intent-aware retrieval, structured planning, and visual grounding."
    )


def render_sidebar() -> Dict[str, Any]:
    st.sidebar.header("Controls")

    selected_sample = st.sidebar.selectbox(
        "Sample queries",
        options=[""] + SAMPLE_QUERIES,
        index=0,
    )

    use_claude = st.sidebar.toggle("Use Claude", value=False)
    show_debug = st.sidebar.toggle("Show debug panels", value=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Example prompts")
    for q in SAMPLE_QUERIES:
        st.sidebar.caption(f"• {q}")

    return {
        "selected_sample": selected_sample,
        "use_claude": use_claude,
        "show_debug": show_debug,
    }


def render_plan_summary(result: Dict[str, Any]) -> None:
    plan = result["plan"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Intent", plan.get("intent", "N/A"))
    col2.metric("Format", plan.get("format", "N/A"))
    col3.metric("Style", plan.get("answer_style", "N/A"))
    col4.metric("Generation", result.get("generation_mode", "N/A"))

    with st.expander("Plan details", expanded=False):
        st.json(
            {
                "intent": plan.get("intent"),
                "format": plan.get("format"),
                "answer_style": plan.get("answer_style"),
                "include_table": plan.get("include_table"),
                "include_diagram": plan.get("include_diagram"),
                "include_image": plan.get("include_image"),
                "process_tags": plan.get("process_tags", []),
                "voltage_tags": plan.get("voltage_tags", []),
                "primary_chunk_id": (
                    plan["primary_chunk"]["chunk_id"]
                    if plan.get("primary_chunk")
                    else None
                ),
                "supporting_chunk_ids": [
                    chunk["chunk_id"] for chunk in plan.get("supporting_chunks", [])
                ],
            }
        )


def render_final_answer(result: Dict[str, Any]) -> None:
    st.subheader("Answer")
    st.markdown(result["final_answer"])


def render_primary_and_supporting_chunks(result: Dict[str, Any]) -> None:
    plan = result["plan"]
    primary = plan.get("primary_chunk")
    supporting = plan.get("supporting_chunks", [])

    st.subheader("Evidence")

    if primary:
        with st.container(border=True):
            st.markdown("**Primary source**")
            st.write(
                f"Section: {primary.get('section_title')} | "
                f"Page: {primary.get('page_number')} | "
                f"Type: {primary.get('content_type')}"
            )
            st.caption(primary.get("chunk_id"))
            st.text(primary.get("text", "")[:1500])

    if supporting:
        st.markdown("**Supporting sources**")
        for chunk in supporting:
            with st.expander(
                f"{chunk.get('section_title')} | Page {chunk.get('page_number')} | {chunk.get('content_type')}",
                expanded=False,
            ):
                st.caption(chunk.get("chunk_id"))
                st.text(chunk.get("text", "")[:1500])


def try_render_image(path_str: str, caption: str) -> None:
    if not path_str:
        st.caption(caption)
        return

    path = Path(path_str)
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.caption(f"{caption}\n\nImage path not found: {path_str}")


def render_visual_references(result: Dict[str, Any]) -> None:
    image_results = result.get("image_results", [])

    st.subheader("Matched Visual References")

    if not image_results:
        st.info("No visual references matched this query.")
        return

    cols = st.columns(min(3, len(image_results)))
    for idx, img in enumerate(image_results):
        caption = (
            f"Page {img.get('page_number', 'N/A')} | "
            f"{img.get('section_title') or 'Visual reference'}"
        )
        with cols[idx % len(cols)]:
            try_render_image(img.get("path"), caption)
            score = img.get("vision_score", None)
            if score is not None:
                st.caption(f"Vision score: {score}")
            raw_caption = img.get("caption", "")
            if raw_caption:
                with st.expander("Caption / OCR context", expanded=False):
                    st.text(raw_caption[:1200])


def render_debug_panels(result: Dict[str, Any]) -> None:
    st.subheader("Debug")

    with st.expander("Router output", expanded=False):
        st.json(result.get("router_output", {}))

    with st.expander("Render output", expanded=False):
        st.json(result.get("render_output", {}))

    with st.expander("Top hybrid results", expanded=False):
        hybrid_results = result.get("hybrid_results", [])
        preview = []
        for item in hybrid_results[:10]:
            preview.append(
                {
                    "chunk_id": item.get("chunk_id"),
                    "section_title": item.get("section_title"),
                    "page_number": item.get("page_number"),
                    "content_type": item.get("content_type"),
                    "keyword_score": item.get("keyword_score"),
                    "vector_score": item.get("vector_score"),
                    "combined_score": item.get("combined_score"),
                    "process_tags": item.get("process_tags", []),
                    "voltage_tags": item.get("voltage_tags", []),
                    "text_preview": item.get("text", "")[:400],
                }
            )
        st.json(preview)


def main() -> None:
    render_header()
    controls = render_sidebar()
    orchestrator = get_orchestrator()

    default_query = controls["selected_sample"] if controls["selected_sample"] else ""

    query = st.text_input(
        "Ask a question about the Vulcan OmniPro 220",
        value=default_query,
        placeholder="Example: duty cycle MIG 240V",
    )

    run = st.button("Run agent", type="primary", use_container_width=True)

    if not run:
        st.info("Enter a question or choose a sample query, then click Run agent.")
        return

    if not query.strip():
        st.warning("Please enter a question.")
        return

    with st.spinner("Running agent..."):
        result = orchestrator.answer(query=query, use_claude=controls["use_claude"])

    render_plan_summary(result)

    left, right = st.columns([1.5, 1])

    with left:
        render_final_answer(result)
        render_primary_and_supporting_chunks(result)

    with right:
        render_visual_references(result)

    if controls["show_debug"]:
        render_debug_panels(result)


if __name__ == "__main__":
    main()