from typing import Dict, Any, List


class ImageRenderer:
    def __init__(self):
        pass

    def render(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        primary = plan.get("primary_chunk")
        supporting = plan.get("supporting_chunks", [])

        content_blocks: List[Dict[str, Any]] = []

        if primary:
            content_blocks.append({
                "section_title": primary.get("section_title"),
                "page_number": primary.get("page_number"),
                "text_preview": " ".join(primary.get("text", "").split())[:300],
            })

        for chunk in supporting:
            content_blocks.append({
                "section_title": chunk.get("section_title"),
                "page_number": chunk.get("page_number"),
                "text_preview": " ".join(chunk.get("text", "").split())[:250],
            })

        return {
            "render_type": "image_plus_text",
            "title": f"{plan.get('intent', 'controls_lookup').replace('_', ' ').title()} Visual Response",
            "content": content_blocks,
            "metadata": {
                "answer_style": plan.get("answer_style"),
                "include_image": True,
                "chunk_count": len(plan.get("chunks_to_use", [])),
            },
        }