import os
import tempfile
from pathlib import Path
from typing import List

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.agent.orchestrator import Orchestrator


st.set_page_config(
    page_title="Vulcan OmniPro 220 Agent",
    page_icon="⚡",
    layout="wide",
)

SUPPORTED_IMAGE_TYPES = ["png", "jpg", "jpeg", "webp"]


@st.cache_resource
def get_orchestrator() -> Orchestrator:
    return Orchestrator()


def save_uploaded_files(uploaded_files) -> List[str]:
    saved_paths = []

    if not uploaded_files:
        return saved_paths

    temp_dir = Path(tempfile.gettempdir()) / "vulcan_agent_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for uploaded_file in uploaded_files:
        suffix = Path(uploaded_file.name).suffix.lower()
        if suffix.replace(".", "") not in SUPPORTED_IMAGE_TYPES:
            continue

        file_path = temp_dir / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        saved_paths.append(str(file_path))

    return saved_paths


def render_plan_summary(plan: dict):
    if not plan:
        return

    st.subheader("Plan Summary")
    st.json(
        {
            "intent": plan.get("intent"),
            "format": plan.get("format"),
            "answer_style": plan.get("answer_style"),
            "include_image": plan.get("include_image"),
            "include_diagram": plan.get("include_diagram"),
            "include_table": plan.get("include_table"),
            "num_image_results": plan.get("num_image_results"),
            "notes": plan.get("notes"),
        }
    )


def render_manual_image_matches(image_results: list):
    if not image_results:
        return

    st.subheader("Matched Manual Figures")

    for idx, item in enumerate(image_results, start=1):
        st.markdown(f"**Figure {idx}**")
        st.write("Page:", item.get("page"))
        st.write("Score:", item.get("score"))
        st.write("Why matched:", item.get("match_reason"))

        image_path = item.get("path")
        raw = item.get("raw", {}) if isinstance(item.get("raw"), dict) else {}
        image_path = image_path or raw.get("image_path")

        if image_path and os.path.exists(image_path):
            st.image(image_path, caption=item.get("caption") or "Matched manual figure", use_container_width=True)
        else:
            st.caption(item.get("caption") or "No preview available")

        st.divider()


def render_uploaded_images(uploaded_files):
    if not uploaded_files:
        return

    st.subheader("Uploaded Images")
    cols = st.columns(min(3, len(uploaded_files)))

    for idx, uploaded_file in enumerate(uploaded_files):
        with cols[idx % len(cols)]:
            st.image(uploaded_file, caption=uploaded_file.name, use_container_width=True)


def main():
    st.title("⚡ Vulcan OmniPro 220 Multimodal Agent")
    st.write(
        "Ask questions about the welder using text, images, or both. "
        "The agent retrieves manual evidence, matches figures, and generates structured answers."
    )

    orchestrator = get_orchestrator()

    with st.sidebar:
        st.header("Input")
        use_claude = st.checkbox("Use Claude for final synthesis", value=True)

        uploaded_files = st.file_uploader(
            "Upload image(s)",
            type=SUPPORTED_IMAGE_TYPES,
            accept_multiple_files=True,
            help="Upload weld photos, front panel photos, setup images, or screenshots.",
        )

        query = st.text_area(
            "Question",
            placeholder="Example: Does this polarity setup look correct?",
            height=120,
        )

        submit = st.button("Run Agent", type="primary", use_container_width=True)

    render_uploaded_images(uploaded_files)

    if submit:
        if not query and not uploaded_files:
            st.warning("Please enter a question, upload an image, or both.")
            return

        with st.spinner("Analyzing input and retrieving manual evidence..."):
            image_paths = save_uploaded_files(uploaded_files)
            safe_query = query.strip() if query else "Analyze the uploaded image and explain what it shows."

            result = orchestrator.answer(
                query=safe_query,
                image_paths=image_paths,
                use_claude=use_claude,
            )

        st.success("Done")

        st.subheader("Final Answer")
        st.markdown(result.get("final_answer", "No answer generated."))

        if result.get("visual_analysis"):
            st.subheader("Visual Analysis")
            st.text(result["visual_analysis"])

        render_plan_summary(result.get("plan", {}))
        render_manual_image_matches(result.get("manual_image_results", []))

        with st.expander("Retrieved Chunks"):
            for idx, chunk in enumerate(result.get("hybrid_results", [])[:5], start=1):
                st.markdown(
                    f"**Chunk {idx}** | "
                    f"Page: {chunk.get('page', chunk.get('page_number', 'unknown'))} | "
                    f"Section: {chunk.get('section_title', 'unknown')}"
                )
                st.code(chunk.get("text", "")[:1500])

        with st.expander("Raw Render Output"):
            st.json(result.get("render_output", {}))


if __name__ == "__main__":
    main()