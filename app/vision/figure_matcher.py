import json
import re
from typing import List, Dict, Any, Optional

from app.config import DATA_DIR


class FigureMatcher:
    def __init__(self):
        self.manifest_path = DATA_DIR / "processed" / "images_manifest.json"
        self.images = self._load_manifest()

    def _load_manifest(self) -> List[Dict[str, Any]]:
        if not self.manifest_path.exists():
            print("[FigureMatcher] No image manifest found at: {0}".format(self.manifest_path))
            return []

        with open(self.manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if "images" in data and isinstance(data["images"], list):
                return data["images"]

            flattened = []
            for _, value in data.items():
                if isinstance(value, list):
                    flattened.extend(value)
            return flattened

        return []

    def _normalize(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = re.sub(r"\s+", " ", text)
        return text

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9_+-]+", self._normalize(text))

    def _get_image_text(self, image: Dict[str, Any]) -> str:
        candidates = [
            image.get("caption"),
            image.get("nearby_text"),
            image.get("ocr_text"),
            image.get("section_title"),
            image.get("title"),
            image.get("image_name"),
            image.get("filename"),
            image.get("path"),
        ]
        return " ".join([str(x) for x in candidates if x])

    def _score_token_overlap(self, query_tokens: set, image_tokens: set) -> float:
        overlap = query_tokens & image_tokens
        return float(len(overlap)) * 2.0

    def _score_category_boosts(self, combined_query: str, image_text: str, desired_render: str = "") -> float:
        score = 0.0
        reasons = []

        diagram_query_terms = ["diagram", "polarity", "wiring", "connection", "socket", "dcen", "dcep", "ground clamp", "positive", "negative"]
        diagram_image_terms = ["diagram", "polarity", "wiring", "socket", "positive", "negative", "ground clamp", "dcen", "dcep"]

        controls_query_terms = ["front panel", "control", "knob", "display", "button", "screen"]
        controls_image_terms = ["front panel", "controls", "knob", "display", "button", "screen"]

        spool_query_terms = ["wire spool", "feed roller", "feed tensioner", "idler arm", "spool", "wire feed"]
        spool_image_terms = ["wire spool", "feed roller", "feed tensioner", "idler arm", "spool", "wire feed"]

        troubleshoot_query_terms = ["troubleshooting", "problem", "burn-through", "burn through", "weld", "spatter", "porosity", "undercut", "defect"]
        troubleshoot_image_terms = ["troubleshooting", "diagnosis", "weld", "penetration", "burn-through", "burn through", "spatter", "porosity", "undercut", "defect"]

        specs_query_terms = ["duty cycle", "240v", "120v", "amperage", "current", "voltage", "specification"]
        specs_image_terms = ["duty cycle", "duration of use", "overheats", "warning screen", "current", "voltage", "specification"]

        if any(term in combined_query for term in diagram_query_terms):
            if any(term in image_text for term in diagram_image_terms):
                score += 4.0
                reasons.append("diagram/polarity match")

        if any(term in combined_query for term in controls_query_terms):
            if any(term in image_text for term in controls_image_terms):
                score += 4.0
                reasons.append("controls match")

        if any(term in combined_query for term in spool_query_terms):
            if any(term in image_text for term in spool_image_terms):
                score += 4.0
                reasons.append("spool/feed match")

        if any(term in combined_query for term in troubleshoot_query_terms):
            if any(term in image_text for term in troubleshoot_image_terms):
                score += 4.0
                reasons.append("troubleshooting match")

        if any(term in combined_query for term in specs_query_terms):
            if any(term in image_text for term in specs_image_terms):
                score += 4.0
                reasons.append("specification match")

        if desired_render == "diagram" and any(term in image_text for term in diagram_image_terms):
            score += 2.5
            reasons.append("diagram render preference")

        if desired_render == "image_plus_text" and any(
            term in image_text for term in controls_image_terms + troubleshoot_image_terms + spool_image_terms
        ):
            score += 2.0
            reasons.append("image-plus-text render preference")

        return score, reasons

    def _score_metadata_quality(self, image: Dict[str, Any]) -> float:
        score = 0.0
        if image.get("page") is not None or image.get("page_number") is not None:
            score += 0.5
        if image.get("section_title"):
            score += 0.5
        if image.get("caption"):
            score += 0.5
        return score

    def _deduplicate(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []

        for img in images:
            caption = (img.get("caption") or img.get("nearby_text") or "")[:120]
            key = (
                img.get("page") or img.get("page_number"),
                self._normalize(caption),
                img.get("path"),
            )
            if key not in seen:
                seen.add(key)
                unique.append(img)

        return unique

    def _build_match_reason(self, overlap_terms: List[str], category_reasons: List[str]) -> str:
        parts = []

        if overlap_terms:
            parts.append("token overlap: {0}".format(", ".join(overlap_terms[:6])))

        if category_reasons:
            parts.append(" | ".join(category_reasons))

        return "; ".join(parts) if parts else "general relevance"

    def match(
        self,
        query: str,
        top_k: int = 3,
        visual_analysis: str = "",
        desired_render: str = "",
    ) -> List[Dict[str, Any]]:
        if not self.images:
            return []

        combined_query = self._normalize(
            "{0} {1}".format(query or "", visual_analysis or "")
        )
        query_tokens = set(self._tokenize(combined_query))

        scored = []
        for image in self.images:
            image_text = self._normalize(self._get_image_text(image))
            image_tokens = set(self._tokenize(image_text))

            overlap_terms = sorted(list(query_tokens & image_tokens))
            score = self._score_token_overlap(query_tokens, image_tokens)

            category_score, category_reasons = self._score_category_boosts(
                combined_query=combined_query,
                image_text=image_text,
                desired_render=desired_render,
            )
            score += category_score
            score += self._score_metadata_quality(image)

            if score <= 0:
                continue

            enriched = {
                "path": image.get("path"),
                "page": image.get("page") or image.get("page_number"),
                "section_title": image.get("section_title"),
                "caption": image.get("caption") or image.get("nearby_text") or image.get("title"),
                "ocr_text": image.get("ocr_text"),
                "score": round(score, 4),
                "match_reason": self._build_match_reason(overlap_terms, category_reasons),
                "raw": image,
            }
            scored.append(enriched)

        scored.sort(key=lambda x: x["score"], reverse=True)
        scored = self._deduplicate(scored)
        return scored[:top_k]