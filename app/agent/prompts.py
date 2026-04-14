from typing import Any, Dict, List


def build_system_prompt() -> str:
    return """
You are a technical reasoning assistant for the Vulcan OmniPro 220 welding system.

Your job is to produce a final user-facing answer, not to dump retrieved text.

Rules:
- Use the retrieved manual evidence as the primary source of truth.
- Use visual analysis from user images only as supporting evidence.
- Answer the user's actual question directly and clearly.
- Synthesize the evidence into a practical answer.
- Do not paste long raw manual excerpts unless necessary.
- If a table is provided, preserve it and explain it briefly.
- If a diagram is provided, preserve it and explain how to use it.
- If the answer is procedural, provide ordered steps.
- If the answer is troubleshooting-related, explain symptom, likely cause, and corrective action.
- If evidence is insufficient, say so clearly instead of guessing.
- Do not invent technical values or unsupported facts.
""".strip()


def _format_chunk(chunk: Dict[str, Any], index: int) -> str:
    chunk_id = chunk.get("chunk_id", "unknown_chunk")
    page = chunk.get("page", "unknown")
    section_title = chunk.get("section_title", "unknown section")
    content_type = chunk.get("content_type", "unknown")
    text = chunk.get("text", "")

    return (
        "[Chunk {0}]\n"
        "chunk_id: {1}\n"
        "page: {2}\n"
        "section_title: {3}\n"
        "content_type: {4}\n"
        "{5}".format(index + 1, chunk_id, page, section_title, content_type, text)
    )


def build_user_prompt(
    query: str,
    router_output: Dict[str, Any],
    plan: Dict[str, Any],
    render_output: Dict[str, Any],
    retrieved_chunks: List[Dict[str, Any]],
    visual_analysis: str = "",
) -> str:
    formatted_chunks = "\n\n".join(
        [_format_chunk(chunk, idx) for idx, chunk in enumerate(retrieved_chunks)]
    )

    return """
USER QUERY:
{query}

ROUTER OUTPUT:
{router_output}

RESPONSE PLAN:
{plan}

VISUAL ANALYSIS:
{visual_analysis}

STRUCTURED RENDER OUTPUT:
{render_output}

RETRIEVED MANUAL EVIDENCE:
{formatted_chunks}

INSTRUCTIONS:
1. Answer the user's question using the manual evidence as the primary source of truth.
2. Use the visual analysis only to interpret what the user image may show and to connect it to the manual.
3. Keep the answer aligned with the requested response format.
4. If the render output already contains structured content, improve its clarity rather than replacing it with vague prose.
5. When discussing technical values, steps, or polarity, stay faithful to retrieved evidence.
6. If the user image appears inconsistent with the manual's recommended setup, say what looks inconsistent and what the manual recommends.
""".strip().format(
        query=query,
        router_output=router_output,
        plan=plan,
        visual_analysis=visual_analysis if visual_analysis else "No user image provided.",
        render_output=render_output,
        formatted_chunks=formatted_chunks if formatted_chunks else "No chunks retrieved.",
    )