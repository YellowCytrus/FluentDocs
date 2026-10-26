"""
Generate Typst fragment for a title page. Insert between preamble and main document body.
When ignore_document_styles=True: wrap in block with #set overrides to isolate from preamble.
Output: #let for variables + place() calls (flow onto first page) + #pagebreak()
"""

from typing import Any

from app.models.pydantic.page_editor import (
    Element,
    PaperSize,
    TextElement,
    VariableElement,
    LineElement,
)
from app.utils.typst_preamble import _typst_bool, _typst_font, _typst_str

TEXT_SIZE_PT = 12
VARIABLE_FONT_SIZE_PT = 10
TEXT_FILL = "black"
FONT_FAMILY = "Libertinus Serif"
VARIABLE_BOX_FILL = 'rgb("#ffffff")'
DY_OFFSET_MM = 0


def _element_text_args(
    style: dict[str, Any] | None,
    default_size: float,
    default_font: str,
    default_fill: str,
) -> list[str]:
    """Build #text(...) args from element text_style dict, with defaults."""
    if not style:
        return [
            f"size: {default_size}pt",
            f"font: {_typst_str(_typst_font(default_font))}",
            f"fill: {default_fill}",
        ]
    size = style.get("font_size")
    if size is None:
        size = default_size
    args = [f"size: {float(size)}pt"]
    font = style.get("font")
    font_str = _typst_font(str(font) if font else default_font)
    args.append(f"font: {_typst_str(font_str)}")
    weight = style.get("weight")
    if weight and str(weight) != "regular":
        args.append(f"weight: {_typst_str(str(weight))}")
    text_style = style.get("style")
    if text_style and str(text_style) != "normal":
        args.append(f"style: {_typst_str(str(text_style))}")
    fill = style.get("fill")
    if fill is not None and str(fill):
        args.append(f"fill: {fill}")
    else:
        args.append(f"fill: {default_fill}")
    lang = style.get("lang")
    if lang and str(lang) != "en":
        args.append(f"lang: {_typst_str(str(lang))}")
    region = style.get("region")
    if region is not None and str(region):
        args.append(f"region: {_typst_str(str(region))}")
    tracking = style.get("tracking")
    if tracking is not None and float(tracking) != 0.0:
        args.append(f"tracking: {float(tracking)}pt")
    word_spacing = style.get("word_spacing")
    if word_spacing is not None and float(word_spacing) != 100.0:
        args.append(f"spacing: {float(word_spacing)}%")
    hyphenate = style.get("hyphenate")
    if hyphenate is not None:
        if isinstance(hyphenate, str):
            args.append(f"hyphenate: {hyphenate}")
        else:
            args.append(f"hyphenate: {_typst_bool(hyphenate)}")
    ligatures = style.get("ligatures")
    if ligatures is False:
        args.append("ligatures: false")
    number_type = style.get("number_type")
    if number_type and str(number_type) != "auto":
        args.append(f"number-type: {_typst_str(str(number_type))}")
    number_width = style.get("number_width")
    if number_width and str(number_width) != "auto":
        args.append(f"number-width: {_typst_str(str(number_width))}")
    return args


def _mm(x: float) -> str:
    v = round(x, 2)
    return f"{int(v)}mm" if v == int(v) else f"{v}mm"


def _escape_typst_string(s: str) -> str:
    return s.replace("\\", "\\\\").replace("#", "\\#").replace("]", "\\]")


def _render_element(e: Element, variables: dict[str, str]) -> str:
    if isinstance(e, TextElement):
        content = _escape_typst_string(e.content)
        text_args = _element_text_args(e.text_style, TEXT_SIZE_PT, FONT_FAMILY, TEXT_FILL)
        text_call = f"#text({', '.join(text_args)})[{content}]"
        return (
            f"place(top + left, dx: {_mm(e.x_mm)}, dy: {_mm(e.y_mm + DY_OFFSET_MM)}, [{text_call}])"
        )
    if isinstance(e, VariableElement):
        text_args = _element_text_args(e.text_style, VARIABLE_FONT_SIZE_PT, FONT_FAMILY, TEXT_FILL)
        text_call = f"#text({', '.join(text_args)})[#{e.var_name}]"
        align_val = (e.text_style or {}).get("align", "left")
        typst_align = {
            "left": "left",
            "center": "center",
            "right": "right",
            "justify": "justify",
        }.get(str(align_val), "left")
        if typst_align == "justify":
            inner = f"#block(width: 100%)[#set par(justify: true) {text_call}]"
        else:
            inner = f"#align({typst_align})[{text_call}]"
        return (
            f"place(top + left, dx: {_mm(e.x_mm)}, dy: {_mm(e.y_mm + DY_OFFSET_MM)}, "
            f"box(width: {_mm(e.width_mm)}, height: auto, fill: {VARIABLE_BOX_FILL}, "
            f"[{inner}])"
        )
    if isinstance(e, LineElement):
        dx = e.x2_mm - e.x1_mm
        dy = e.y2_mm - e.y1_mm
        return (
            f"place(top + left, dx: {_mm(e.x1_mm)}, dy: {_mm(e.y1_mm + DY_OFFSET_MM)}, "
            f"line(end: ({_mm(dx)}, {_mm(dy)}), stroke: 1pt))"
        )
    raise TypeError(f"Unknown element type: {type(e)}")


_STYLE_OVERRIDES = """
  #set text(size: 12pt, font: "Libertinus Serif", fill: black)
  #set par(leading: 1.2em)
  #set list(marker: [—])
  #set enum(numbering: "1.")
  #set heading(numbering: none)
  #set figure(placement: auto)
  #set table(stroke: 0.5pt)
  #set strong(delta: 300)
"""


def generate_fragment(
    elements: list[Element],
    paper: PaperSize,
    variables: dict[str, str] | None = None,
    ignore_document_styles: bool = True,
) -> str:
    """
    Generate Typst fragment for insertion after preamble.
    When ignore_document_styles=True, wrap in block with #set overrides so the title page
    ignores all preamble styles (Typst has no unset; inner #set overrides outer until block end).
    """
    var_map = variables or {}
    place_calls = [_render_element(e, var_map) for e in elements]

    var_names = {e.var_name for e in elements if isinstance(e, VariableElement)}
    let_block = "\n".join(
        f"#let {name} = [{_escape_typst_string(var_map.get(name, ''))}]"
        for name in sorted(var_names)
    )
    if let_block:
        let_block += "\n"

    inner = "\n".join(f"#{p}" for p in place_calls)

    if ignore_document_styles and place_calls:
        # #page() isolates margins and numbering from preamble; body is positional
        body = f"{let_block}{_STYLE_OVERRIDES}  {inner}"
        page_content = (
            "#page(\n"
            "  margin: (top: 0pt, bottom: 0pt, left: 0pt, right: 0pt),\n"
            "  numbering: none,\n"
            "  header: none,\n"
            "  footer: none,\n"
            ")[\n"
            f"{body}\n"
            "]\n"
        )
    else:
        if let_block:
            page_content = let_block + "\n"
        else:
            page_content = ""
        if place_calls:
            page_content += inner + "\n"

    return f"{page_content}#pagebreak()\n"
