import base64
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional


SUPPORTED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


def encode_image_for_claude(image_path: str) -> Dict:
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError("Image not found: {0}".format(image_path))

    media_type, _ = mimetypes.guess_type(str(path))
    if media_type not in SUPPORTED_IMAGE_TYPES:
        raise ValueError(
            "Unsupported image type for Claude: {0}. Supported: png, jpeg, webp".format(media_type)
        )

    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": data,
        },
    }


def build_visual_analysis_prompt(query: str) -> str:
    return """
You are analyzing one or more images related to the Vulcan OmniPro 220 welding system.

User query:
{query}

Your job:
1. Identify what is visible in the image.
2. Determine whether the image most likely shows one of these:
   - front panel controls
   - wiring / polarity setup
   - wire spool or feed mechanism
   - weld bead / weld defect
   - settings display / parameter screen
   - machine label / specifications
   - other relevant welding setup detail
3. Extract visual evidence that can improve retrieval from the manual.
4. Be precise and cautious. Do not guess beyond what is visible.

Return your answer in exactly this structure:

VISIBLE_OBJECTS:
- ...

IMAGE_TYPE:
- ...

LIKELY_RELEVANT_TOPICS:
- ...

TECHNICAL_OBSERVATIONS:
- ...

POSSIBLE_USER_INTENT:
- ...
""".strip().format(query=query)


def analyze_user_images(client, query: str, image_paths: List[str], model: str = "claude-haiku-4-5") -> str:
    if not image_paths:
        return ""

    content = [{"type": "text", "text": build_visual_analysis_prompt(query)}]

    for image_path in image_paths:
        content.append(encode_image_for_claude(image_path))

    response = client.messages.create(
        model=model,
        max_tokens=700,
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    parts = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)

    return "\n".join(parts).strip()


def build_retrieval_query(query: str, visual_analysis: str) -> str:
    if not visual_analysis:
        return query

    return "{0}\n\nVisual evidence from user image:\n{1}".format(query, visual_analysis)


def extract_visual_keywords(visual_analysis: str) -> List[str]:
    if not visual_analysis:
        return []

    keywords = []
    candidates = [
        "front panel",
        "display",
        "control knob",
        "polarity",
        "dcen",
        "dcep",
        "ground clamp",
        "wire feed",
        "spool",
        "feed roller",
        "knurled groove",
        "v-groove",
        "weld bead",
        "weld defect",
        "spatter",
        "porosity",
        "undercut",
        "burn through",
        "voltage",
        "wire speed",
    ]

    analysis_lower = visual_analysis.lower()
    for item in candidates:
        if item in analysis_lower:
            keywords.append(item)

    return keywords