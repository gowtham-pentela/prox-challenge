import json
import re
from pathlib import Path
from typing import Optional

from app.config import CHUNKS_DIR, PAGES_DIR, PROCESSED_DIR, ensure_directories
from app.schemas import ManualChunk


def load_inventory():
    path = PROCESSED_DIR / "manual_inventory.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_section(page_number, source_file, inventory):
    for entry in inventory:
        if entry["source_file"] != source_file:
            continue
        if entry["page_start"] <= page_number <= entry["page_end"]:
            return entry
    return None


def detect_source_priority(source_file: str) -> str:
    if source_file == "owner-manual.pdf":
        return "primary"
    return "secondary"


def detect_tags(text: str):
    lowered = text.lower()

    process_tags = []
    for p in ["mig", "flux", "tig", "stick"]:
        if p in lowered:
            if p == "flux":
                process_tags.append("flux_cored")
            else:
                process_tags.append(p)

    voltage_tags = []
    if "120v" in lowered or "120 vac" in lowered:
        voltage_tags.append("120v")
    if "240v" in lowered or "240 vac" in lowered:
        voltage_tags.append("240v")

    topics = []
    if "polarity" in lowered:
        topics.append("polarity")
    if "duty cycle" in lowered:
        topics.append("duty_cycle")
    if "wire feed" in lowered or "spool" in lowered:
        topics.append("wire_feed")
    if "troubleshooting" in lowered or "possible causes" in lowered:
        topics.append("troubleshooting")
    if "specifications" in lowered or "power input" in lowered:
        topics.append("specification")
    if "controls" in lowered:
        topics.append("controls")
    if "setup" in lowered or "installation" in lowered:
        topics.append("setup")

    return process_tags, voltage_tags, topics


def infer_content_type(text: str, section_title: Optional[str]) -> str:
    lowered = text.lower()

    if section_title:
        lowered_section = section_title.lower()
        if "specification" in lowered_section:
            return "specification"
        if "troubleshooting" in lowered_section:
            return "troubleshooting"
        if "controls" in lowered_section:
            return "diagram"
        if "welding" in lowered_section or "setup" in lowered_section:
            return "procedure"

    if "possible causes" in lowered:
        return "troubleshooting"
    if "setup" in lowered or "installation" in lowered:
        return "procedure"
    if "diagram" in lowered or "front panel" in lowered or "interior controls" in lowered:
        return "diagram"

    return "overview"


def split_text(text: str, max_chars: int = 1800):
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    paragraphs = re.split(r"\n\s*\n", text)

    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        candidate = f"{current}\n\n{para}".strip() if current else para

        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


def main():
    ensure_directories()

    inventory = load_inventory()

    output_path = CHUNKS_DIR / "chunks.jsonl"

    pages = []
    for path in sorted(PAGES_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            pages.append(json.load(f))

    with open(output_path, "w", encoding="utf-8") as out_f:
        for page in pages:
            page_number = page["page_number"]
            source_file = page["source_file"]
            text = page["text"]

            if not text.strip():
                continue

            section_entry = find_section(page_number, source_file, inventory)
            section_title = section_entry["section_title"] if section_entry else None
            source_priority = detect_source_priority(source_file)

            text_chunks = split_text(text)

            for idx, chunk_text in enumerate(text_chunks, start=1):
                process_tags, voltage_tags, topics = detect_tags(chunk_text)
                content_type = infer_content_type(chunk_text, section_title)

                chunk = ManualChunk(
                    chunk_id=f"{Path(source_file).stem}_p{page_number:03d}_c{idx:02d}",
                    page_number=page_number,
                    source_file=source_file,
                    section_title=section_title,
                    content_type=content_type,
                    topics=topics,
                    process_tags=process_tags,
                    voltage_tags=voltage_tags,
                    text=chunk_text,
                    source_path=None,
                )

                chunk_dict = chunk.model_dump()
                chunk_dict["source_priority"] = source_priority

                out_f.write(json.dumps(chunk_dict, ensure_ascii=False) + "\n")

    print(f"Saved improved chunks to: {output_path}")


if __name__ == "__main__":
    main()