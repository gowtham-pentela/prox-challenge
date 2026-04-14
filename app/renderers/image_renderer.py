from typing import Dict, Any, List, Optional


class ImageRenderer:
    def __init__(self):
        pass

    def _normalize_page(self, chunk: Dict[str, Any]) -> Optional[int]:
        return chunk.get("page") or chunk.get("page_number")

    def _build_chunk_block(self, chunk: Dict[str, Any], max_chars: int = 280) -> Dict[str, Any]:
        raw_text = chunk.get("text", "") or ""
        compact_text = " ".join(raw_text.split())

        return {
            "chunk_id": chunk.get("chunk_id"),
            "section_title": chunk.get("section_title", "Unknown Section"),
            "page": self._normalize_page(chunk),
            "content_type": chunk.get("content_type", "unknown"),
            "text_preview": compact_text[:max_chars],
        }

    def _summarize_manual_images(self, image_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        summarized = []

        for item in image_results[:4]:
            summarized.append({
                "path": item.get("path"),
                "page": item.get("page") or item.get("page_number"),
                "caption": item.get("caption") or item.get("label") or item.get("reason") or "Relevant manual image",
                "score": item.get("score"),
            })

        return summarized

    def _summarize_user_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        return [{"path": path, "source": "user_input"} for path in image_paths[:4]]

    def _build_focus_points(self, plan: Dict[str, Any]) -> List[str]:
        intent = plan.get("intent", "")
        answer_style = plan.get("answer_style", "")
        focus_points = []

        if intent == "troubleshooting":
            focus_points.extend([
                "Identify visible symptom from image evidence",
                "Map symptom to likely causes from manual",
                "Recommend corrective action grounded in manual",
            ])
        elif intent == "controls_lookup":
            focus_points.extend([
                "Identify visible control or panel component",
                "Map visible component to manual section",
                "Explain function and usage clearly",
            ])
        elif intent == "procedure":
            focus_points.extend([
                "Use image evidence to validate current setup",
                "Compare visible setup against manual procedure",
                "Explain mismatch or confirm correctness",
            ])
        else:
            focus_points.extend([
                "Use image evidence as supporting context",
                "Anchor explanation in retrieved manual evidence",
            ])

        if answer_style:
            focus_points.append("Preferred answer style: {0}".format(answer_style))

        return focus_points

    def render(
        self,
        plan: Dict[str, Any],
        hybrid_results: Optional[List[Dict[str, Any]]] = None,
        query: str = "",
        image_paths: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        hybrid_results = hybrid_results or []
        image_paths = image_paths or []

        primary = plan.get("primary_chunk")
        supporting = plan.get("supporting_chunks", [])
        image_results = plan.get("image_results", [])

        evidence_blocks: List[Dict[str, Any]] = []

        if primary:
            evidence_blocks.append(self._build_chunk_block(primary, max_chars=320))

        for chunk in supporting[:3]:
            evidence_blocks.append(self._build_chunk_block(chunk, max_chars=240))

        if not evidence_blocks and hybrid_results:
            for chunk in hybrid_results[:3]:
                evidence_blocks.append(self._build_chunk_block(chunk, max_chars=240))

        return {
            "render_type": "image_plus_text",
            "title": "{0} Visual Response".format(
                plan.get("intent", "visual_lookup").replace("_", " ").title()
            ),
            "query": query,
            "summary": {
                "intent": plan.get("intent"),
                "format": plan.get("format"),
                "answer_style": plan.get("answer_style"),
            },
            "visual_inputs": {
                "user_images": self._summarize_user_images(image_paths),
                "matched_manual_images": self._summarize_manual_images(image_results),
            },
            "evidence": evidence_blocks,
            "focus_points": self._build_focus_points(plan),
            "instructions_for_llm": [
                "Use manual evidence as the source of truth.",
                "Use image evidence to interpret what the user may be seeing.",
                "If the image shows an incorrect setup or defect, explain what looks wrong and what the manual recommends.",
                "Prefer a practical explanation over generic prose.",
            ],
            "metadata": {
                "include_image": True,
                "chunk_count": len(plan.get("chunks_to_use", [])),
                "num_user_images": len(image_paths),
                "num_manual_images": len(image_results),
            },
        }