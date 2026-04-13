from typing import Dict, Any, List


class DiagramRenderer:
    def __init__(self):
        pass

    def render(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        primary = plan.get("primary_chunk")
        supporting = plan.get("supporting_chunks", [])

        diagram_nodes: List[Dict[str, Any]] = []
        diagram_edges: List[Dict[str, Any]] = []

        if primary:
            diagram_nodes.append({
                "id": "primary_source",
                "label": primary.get("section_title", "Primary Source"),
                "page": primary.get("page_number"),
            })

        for idx, chunk in enumerate(supporting, start=1):
            node_id = f"support_{idx}"
            diagram_nodes.append({
                "id": node_id,
                "label": chunk.get("section_title", f"Supporting Chunk {idx}"),
                "page": chunk.get("page_number"),
            })
            diagram_edges.append({
                "from": "primary_source",
                "to": node_id,
                "label": "supports",
            })

        return {
            "render_type": "diagram",
            "title": f"{plan.get('intent', 'diagram').replace('_', ' ').title()} Diagram Plan",
            "content": {
                "nodes": diagram_nodes,
                "edges": diagram_edges,
                "primary_text_preview": " ".join(primary.get("text", "").split())[:350] if primary else "",
            },
            "metadata": {
                "answer_style": plan.get("answer_style"),
                "include_diagram": True,
                "chunk_count": len(plan.get("chunks_to_use", [])),
            },
        }