import json
from pathlib import Path

from app.config import PAGES_DIR, TABLES_DIR, ensure_directories
from app.schemas import ManualTable


TABLE_PAGE_KEYWORDS = [
    "specifications",
    "rated duty cycles",
    "power input",
    "welding current range",
    "possible causes",
    "corrective actions",
    "troubleshooting",
]


def load_pages() -> list[dict]:
    pages = []
    for path in sorted(PAGES_DIR.glob("*.json")):
        with open(path, "r", encoding="utf-8") as f:
            pages.append(json.load(f))
    return pages


def looks_like_table_page(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in TABLE_PAGE_KEYWORDS)


def detect_topics(text: str) -> tuple[list[str], list[str], list[str]]:
    lowered = text.lower()

    process_tags = []
    if "mig" in lowered:
        process_tags.append("mig")
    if "flux-cored" in lowered or "flux cored" in lowered or "flux" in lowered:
        process_tags.append("flux_cored")
    if "tig" in lowered:
        process_tags.append("tig")
    if "stick" in lowered:
        process_tags.append("stick")

    voltage_tags = []
    if "120v" in lowered or "120 vac" in lowered:
        voltage_tags.append("120v")
    if "240v" in lowered or "240 vac" in lowered:
        voltage_tags.append("240v")

    topics = []
    if "duty cycle" in lowered:
        topics.append("duty_cycle")
    if "specification" in lowered or "power input" in lowered:
        topics.append("specification")
    if "troubleshooting" in lowered or "possible causes" in lowered:
        topics.append("troubleshooting")

    return process_tags, voltage_tags, topics


def make_simple_rows(text: str) -> list[list[str]]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rows = []

    for line in lines:
        rows.append([line])

    return rows


def infer_headers(text: str) -> list[str]:
    lowered = text.lower()

    if "power input" in lowered and "welding current range" in lowered:
        return ["raw_spec_rows"]
    if "possible causes" in lowered or "corrective" in lowered:
        return ["raw_troubleshooting_rows"]
    return ["raw_rows"]


def main() -> None:
    ensure_directories()
    pages = load_pages()
    output_path = TABLES_DIR / "tables.jsonl"

    with open(output_path, "w", encoding="utf-8") as out_f:
        for page in pages:
            text = page["text"]
            if not text or not looks_like_table_page(text):
                continue

            process_tags, voltage_tags, topics = detect_topics(text)
            headers = infer_headers(text)
            rows = make_simple_rows(text)

            table = ManualTable(
                table_id=f"{Path(page['source_file']).stem}_p{page['page_number']:03d}_t01",
                page_number=page["page_number"],
                source_file=page["source_file"],
                section_title=None,
                topics=topics,
                process_tags=process_tags,
                voltage_tags=voltage_tags,
                headers=headers,
                rows=rows,
                raw_text=text,
            )

            out_f.write(json.dumps(table.model_dump(), ensure_ascii=False) + "\n")

    print(f"Saved tables to: {output_path}")


if __name__ == "__main__":
    main()