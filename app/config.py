from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]

FILES_DIR = ROOT_DIR / "files"

PRIMARY_MANUAL_PATH = FILES_DIR / "owner-manual.pdf"
SECONDARY_MANUAL_PATHS = [
    FILES_DIR / "quick-start-guide.pdf",
    FILES_DIR / "selection-chart.pdf",
]
ALL_MANUAL_PATHS = [PRIMARY_MANUAL_PATH] + SECONDARY_MANUAL_PATHS

DATA_DIR = ROOT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

PAGES_DIR = PROCESSED_DIR / "pages"
IMAGES_DIR = PROCESSED_DIR / "images"
CHUNKS_DIR = PROCESSED_DIR / "chunks"
TABLES_DIR = PROCESSED_DIR / "tables"
INDEXES_DIR = DATA_DIR / "indexes"

NOTES_DIR = ROOT_DIR / "notes"
TESTS_DIR = ROOT_DIR / "tests"


def ensure_directories() -> None:
    for path in [
        PAGES_DIR,
        IMAGES_DIR,
        CHUNKS_DIR,
        TABLES_DIR,
        INDEXES_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)