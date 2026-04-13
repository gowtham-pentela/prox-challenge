from typing import Dict, Any, List


class ImageAnalysis:
    def __init__(self):
        pass

    def summarize_images(self, images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        summaries = []

        for image in images:
            summaries.append({
                "page_number": image.get("page_number"),
                "section_title": image.get("section_title"),
                "path": image.get("path") or image.get("image_path") or image.get("filename"),
                "caption": image.get("caption") or image.get("nearby_text") or image.get("title") or "",
                "vision_score": image.get("vision_score", 0.0),
            })

        return summaries