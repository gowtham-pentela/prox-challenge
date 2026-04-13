from typing import Dict, Any, List


class TableRenderer:
    def __init__(self):
        pass

    def render(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        chunks = plan.get("chunks_to_use", [])

        rows: List[Dict[str, Any]] = []
        for chunk in chunks:
            rows.append({
                "section_title": chunk.get("section_title"),
                "page_number": chunk.get("page_number"),
                "content_type": chunk.get("content_type"),
                "text_preview": " ".join(chunk.get("text", "").split())[:250],
            })

        return {
            "render_type": "table",
            "title": f"{plan.get('intent', 'specification').replace('_', ' ').title()} Table",
            "content": rows,
            "metadata": {
                "answer_style": plan.get("answer_style"),
                "chunk_count": len(chunks),
                "columns": ["section_title", "page_number", "content_type", "text_preview"],
            },
        }