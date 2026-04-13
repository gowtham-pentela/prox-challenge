def build_system_prompt() -> str:
    return """
You are a technical manual reasoning agent for the Vulcan OmniPro 220 welding system.

You must answer using only the provided context.
Do not invent specifications, steps, settings, polarity details, troubleshooting guidance, or visual details that are not supported by the provided context.

Rules:
- If the answer is fully supported by the context, answer clearly and directly.
- If the answer is only partially supported, provide the available information and clearly state what is missing.
- If the context is insufficient, say so clearly.
- Do not repeat manual boilerplate such as phone numbers, headers, navigation labels, or product footer text.
- Do not mention internal tools, routing, retrieval, renderers, prompts, or implementation details.

Formatting rules:
- For step_by_step: provide concise numbered steps.
- For table: provide a clean structured summary using markdown table when appropriate.
- For diagram: provide a visual-style explanation grounded in the provided context. If useful, include a simple ASCII diagram.
- For image_plus_text: explain the relevant components/issues clearly in structured prose.
- For troubleshooting: use sections like Problem, Likely Causes, and Actions.
- Mention page numbers only when they are supported by the provided context.
""".strip()


def build_user_prompt(
    query: str,
    router_output: dict,
    plan: dict,
    render_output: dict,
    retrieved_chunks: list,
) -> str:
    chunk_summaries = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        chunk_summaries.append(
            f"""Chunk {idx}
Section: {chunk.get("section_title")}
Page: {chunk.get("page_number")}
Content Type: {chunk.get("content_type")}
Text:
{chunk.get("text", "")}
"""
        )

    chunks_text = "\n\n".join(chunk_summaries)

    image_results = plan.get("image_results", [])
    image_lines = []
    for idx, img in enumerate(image_results, start=1):
        image_lines.append(
            f"""Image {idx}
Page: {img.get("page_number")}
Section: {img.get("section_title")}
Path: {img.get("path") or img.get("image_path") or img.get("filename")}
Caption/Context: {img.get("caption") or img.get("nearby_text") or img.get("title") or ""}
Vision Score: {img.get("vision_score", 0.0)}
"""
        )

    image_text = "\n\n".join(image_lines) if image_lines else "No matched images."

    return f"""
User question:
{query}

Intent:
{plan.get("intent")}

Required output format:
{plan.get("format")}

Required answer style:
{plan.get("answer_style")}

Planner flags:
- include_table: {plan.get("include_table")}
- include_diagram: {plan.get("include_diagram")}
- include_image: {plan.get("include_image")}

Structured renderer output:
{render_output}

Matched visual references:
{image_text}

Retrieved manual context:
{chunks_text}

Instructions:
- Answer using only the provided context.
- Prefer the retrieved manual chunks over the renderer summary if there is any conflict.
- Use the matched visual references when they help explain controls, diagrams, polarity, setup, or troubleshooting.
- If the answer is partially available, provide the available part and explicitly note what is missing.
- Keep the answer concise, useful, and well-structured.
- Do not copy long raw manual passages unless necessary.
- Do not include phone numbers, repetitive headers, or footer text.
""".strip()