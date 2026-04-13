import json
import re
from typing import List, Dict, Any

from app.config import DATA_DIR


class FigureMatcher:
    def __init__(self):
        self.manifest_path = DATA_DIR / "processed" / "images_manifest.json"
        self.images = self._load_manifest()

    def _load_manifest(self) -> List[Dict[str, Any]]:
        if not self.manifest_path.exists():
            print(f"[FigureMatcher] No image manifest found at: {self.manifest_path}")
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

    def _score_image(self, query: str, image: Dict[str, Any]) -> float:
        query_norm = self._normalize(query)
        query_tokens = set(self._tokenize(query_norm))
        image_text = self._normalize(self._get_image_text(image))
        image_tokens = set(self._tokenize(image_text))

        score = 0.0

        overlap = query_tokens & image_tokens
        score += len(overlap) * 2.0

        if any(term in query_norm for term in ["diagram", "polarity", "wiring", "connection", "socket"]):
            if any(term in image_text for term in ["diagram", "polarity", "wiring", "socket", "positive", "negative"]):
                score += 4.0

        if any(term in query_norm for term in ["front panel", "control", "knob", "display"]):
            if any(term in image_text for term in ["front panel", "controls", "knob", "display", "button"]):
                score += 4.0

        if any(term in query_norm for term in ["wire spool", "feed roller", "feed tensioner", "idler arm"]):
            if any(term in image_text for term in ["wire spool", "feed roller", "feed tensioner", "idler arm", "spool"]):
                score += 4.0

        if any(term in query_norm for term in ["troubleshooting", "problem", "burn-through", "weld"]):
            if any(term in image_text for term in ["troubleshooting", "diagnosis", "weld", "penetration", "burn-through"]):
                score += 4.0

        if any(term in query_norm for term in ["duty cycle", "240v", "120v", "amperage", "current"]):
            if any(term in image_text for term in ["duty cycle", "duration of use", "overheats", "warning screen"]):
                score += 4.0

        if image.get("page_number") is not None:
            score += 0.5

        if image.get("section_title"):
            score += 0.5

        return score

    def _deduplicate(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []

        for img in images:
            caption = (img.get("caption") or img.get("nearby_text") or "")[:120]
            key = (
                img.get("page_number"),
                self._normalize(caption),
            )
            if key not in seen:
                seen.add(key)
                unique.append(img)

        return unique

    def match(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.images:
            return []

        scored = []
        for image in self.images:
            score = self._score_image(query, image)
            if score > 0:
                enriched = image.copy()
                enriched["vision_score"] = round(score, 4)
                scored.append(enriched)

        scored.sort(key=lambda x: x["vision_score"], reverse=True)
        scored = self._deduplicate(scored)
        return scored[:top_k]