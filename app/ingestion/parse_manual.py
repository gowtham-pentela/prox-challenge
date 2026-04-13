import json
import re
from pathlib import Path

import fitz

from app.config import ALL_MANUAL_PATHS, PAGES_DIR, ensure_directories
from app.schemas import ManualPage


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_pages_from_pdf(pdf_path: Path) -> None:
    doc = fitz.open(pdf_path)
    pdf_stem = pdf_path.stem

    for idx, page in enumerate(doc, start=1):
        raw_text = page.get_text("text")
        cleaned_text = normalize_text(raw_text)

        page_obj = ManualPage(
            page_number=idx,
            source_file=pdf_path.name,
            text=cleaned_text,
            section_title=None,
            metadata={},
        )

        output_path = PAGES_DIR / f"{pdf_stem}_page_{idx:03d}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(page_obj.model_dump(), f, indent=2, ensure_ascii=False)

    doc.close()


def main() -> None:
    ensure_directories()

    for pdf_path in ALL_MANUAL_PATHS:
        if not pdf_path.exists():
            print(f"Skipping missing file: {pdf_path}")
            continue

        print(f"Parsing: {pdf_path.name}")
        extract_pages_from_pdf(pdf_path)

    print("Done parsing manuals.")


if __name__ == "__main__":
    main()