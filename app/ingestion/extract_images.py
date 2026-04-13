import json
from pathlib import Path

import fitz

from app.config import ALL_MANUAL_PATHS, IMAGES_DIR, ensure_directories
from app.schemas import ManualImage


def extract_images_from_pdf(pdf_path: Path) -> list[dict]:
    doc = fitz.open(pdf_path)
    pdf_stem = pdf_path.stem
    manifest = []

    for page_index, page in enumerate(doc, start=1):
        image_list = page.get_images(full=True)
        page_text = page.get_text("text").strip()

        for img_idx, img in enumerate(image_list, start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]

            image_filename = f"{pdf_stem}_page_{page_index:03d}_img_{img_idx:02d}.{ext}"
            image_path = IMAGES_DIR / image_filename

            with open(image_path, "wb") as f:
                f.write(image_bytes)

            image_obj = ManualImage(
                image_id=f"{pdf_stem}_page_{page_index:03d}_img_{img_idx:02d}",
                page_number=page_index,
                source_file=pdf_path.name,
                section_title=None,
                image_path=str(image_path),
                caption=None,
                nearby_text=page_text[:1000] if page_text else None,
            )

            manifest.append(image_obj.model_dump())

    doc.close()
    return manifest


def main() -> None:
    ensure_directories()
    all_images = []

    for pdf_path in ALL_MANUAL_PATHS:
        if not pdf_path.exists():
            print(f"Skipping missing file: {pdf_path}")
            continue

        print(f"Extracting images from: {pdf_path.name}")
        all_images.extend(extract_images_from_pdf(pdf_path))

    manifest_path = IMAGES_DIR.parent / "images_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(all_images, f, indent=2, ensure_ascii=False)

    print(f"Saved image manifest to: {manifest_path}")
    print(f"Extracted {len(all_images)} images total.")


if __name__ == "__main__":
    main()