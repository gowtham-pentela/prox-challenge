from typing import Dict, Any, List


class TextRenderer:
    def __init__(self):
        pass

    def _format_chunk(self, chunk: Dict[str, Any]) -> str:
        section = chunk.get("section_title", "Unknown Section")
        page = chunk.get("page_number", "N/A")
        text = chunk.get("text", "").strip()
        return f"[{section} | Page {page}]\n{text}"

    def render(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        primary = plan.get("primary_chunk")
        supporting = plan.get("supporting_chunks", [])

        content_blocks: List[str] = []

        if primary:
            content_blocks.append(self._format_chunk(primary))

        for chunk in supporting:
            content_blocks.append(self._format_chunk(chunk))

        return {
            "render_type": "text",
            "title": f"{plan.get('intent', 'general_qa').replace('_', ' ').title()} Response",
            "content": "\n\n".join(content_blocks),
            "metadata": {
                "answer_style": plan.get("answer_style"),
                "chunk_count": len(plan.get("chunks_to_use", [])),
            },
        }