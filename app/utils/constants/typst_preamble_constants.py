"""Constants for Typst preamble generation."""

# Font families that Typst may not have installed mapped to safe built-ins.
FONT_ALIASES: dict[str, str] = {
    "times new roman": "Libertinus Serif",
    "times": "Libertinus Serif",
    "arial": "DejaVu Sans",
    "helvetica": "DejaVu Sans",
    "courier new": "DejaVu Sans Mono",
    "courier": "DejaVu Sans Mono",
}
