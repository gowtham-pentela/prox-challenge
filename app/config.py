from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
MANUALS_DIR = RAW_DIR / "manuals"

PROCESSED_DIR = DATA_DIR / "processed"
PAGES_DIR = PROCESSED_DIR / "pages"
IMAGES_DIR = PROCESSED_DIR / "images"
CHUNKS_DIR = PROCESSED_DIR / "chunks"
TABLES_DIR = PROCESSED_DIR / "tables"

INDEXES_DIR = DATA_DIR / "indexes"
NOTES_DIR = ROOT_DIR / "notes"