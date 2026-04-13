from app.renderers import TextRenderer, TableRenderer, ImageRenderer, DiagramRenderer


def get_renderer(format_name: str):
    if format_name == "table":
        return TableRenderer()
    if format_name == "diagram":
        return DiagramRenderer()
    if format_name == "image_plus_text":
        return ImageRenderer()
    return TextRenderer()