import json

from app.config import PROCESSED_DIR, ensure_directories
from app.schemas import InventoryEntry


def build_inventory() -> list[dict]:
    inventory = [
        InventoryEntry(
            page_start=1,
            page_end=1,
            source_file="owner-manual.pdf",
            section_title="Cover and title page",
            content_types=["overview"],
            topics=["product_identity"],
            notes="Manual cover page with product identity.",
        ),
        InventoryEntry(
            page_start=2,
            page_end=6,
            source_file="owner-manual.pdf",
            section_title="Safety and symbols",
            content_types=["overview", "warning", "specification"],
            topics=["safety", "grounding", "symbols"],
            notes="Safety information, grounding, warning definitions, symbology.",
        ),
        InventoryEntry(
            page_start=7,
            page_end=7,
            source_file="owner-manual.pdf",
            section_title="Specifications",
            content_types=["table", "specification"],
            topics=["mig", "tig", "stick", "duty_cycle", "voltage", "materials"],
            notes="Specifications table for MIG, TIG, Stick processes.",
        ),
        InventoryEntry(
            page_start=8,
            page_end=8,
            source_file="owner-manual.pdf",
            section_title="Front panel controls",
            content_types=["diagram"],
            topics=["controls", "front_panel", "sockets"],
            notes="Labeled front panel control diagram.",
        ),
        InventoryEntry(
            page_start=9,
            page_end=9,
            source_file="owner-manual.pdf",
            section_title="Interior controls",
            content_types=["diagram"],
            topics=["controls", "wire_feed", "spool", "foot_pedal"],
            notes="Interior controls and feed mechanism diagram.",
        ),
        InventoryEntry(
            page_start=10,
            page_end=23,
            source_file="owner-manual.pdf",
            section_title="MIG and Flux-Cored wire welding",
            content_types=["procedure", "diagram"],
            topics=["mig", "flux_cored", "setup", "wire_feed", "polarity"],
            notes="Wire spool setup, wire feed, MIG/Flux-Cored operations.",
        ),
        InventoryEntry(
            page_start=24,
            page_end=33,
            source_file="owner-manual.pdf",
            section_title="TIG and Stick welding",
            content_types=["procedure", "diagram"],
            topics=["tig", "stick", "setup", "polarity", "cable_setup"],
            notes="TIG and Stick setup and operation.",
        ),
        InventoryEntry(
            page_start=34,
            page_end=40,
            source_file="owner-manual.pdf",
            section_title="Welding tips and troubleshooting",
            content_types=["troubleshooting", "diagnosis_image", "table"],
            topics=["weld_defect", "troubleshooting", "settings", "technique"],
            notes="Weld diagnosis, troubleshooting guidance, process tips.",
        ),
        InventoryEntry(
            page_start=41,
            page_end=45,
            source_file="owner-manual.pdf",
            section_title="Maintenance",
            content_types=["procedure"],
            topics=["maintenance", "cleaning"],
            notes="Maintenance procedures and inspection guidance.",
        ),
        InventoryEntry(
            page_start=46,
            page_end=47,
            source_file="owner-manual.pdf",
            section_title="Parts list and diagram",
            content_types=["parts_reference", "diagram"],
            topics=["parts", "components"],
            notes="Parts list and exploded or reference diagrams.",
        ),
        InventoryEntry(
            page_start=48,
            page_end=48,
            source_file="owner-manual.pdf",
            section_title="Warranty",
            content_types=["overview"],
            topics=["warranty"],
            notes="Warranty page.",
        ),
        InventoryEntry(
            page_start=1,
            page_end=2,
            source_file="quick-start-guide.pdf",
            section_title="Quick start guide",
            content_types=["diagram", "procedure"],
            topics=["setup", "spool_loading", "cable_setup", "mig", "flux_cored", "tig", "stick"],
            notes="Fast setup guide with spool loading and cable diagrams.",
        ),
        InventoryEntry(
            page_start=1,
            page_end=1,
            source_file="selection-chart.pdf",
            section_title="Welding process selection chart",
            content_types=["diagram", "table"],
            topics=["process_selection", "mig", "flux_cored", "tig", "stick", "materials"],
            notes="Visual chart for choosing welding process by use case.",
        ),
    ]

    return [entry.model_dump() for entry in inventory]


def main() -> None:
    ensure_directories()
    output_path = PROCESSED_DIR / "manual_inventory.json"

    inventory = build_inventory()

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(inventory, f, indent=2, ensure_ascii=False)

    print(f"Saved inventory to: {output_path}")


if __name__ == "__main__":
    main()