"""Canonical style defaults shared by Pydantic schemas and SQLAlchemy models.

All length values here are stored in millimeters (mm), which is the canonical
unit in the backend.
"""

# Page
PAGE_MARGIN_MM_DEFAULT = 25.0
"""Base page margin (GOST preset): 25 mm."""

# Document/paragraph rhythm
DOCUMENT_LINE_SPACING_MM_DEFAULT = 5.08
"""Legacy 1.2em at 12pt converted to mm: 1.2 * 12 * (25.4 / 72)."""

PAR_SPACING_MM_DEFAULT = 4.2333333333
"""Legacy 1em at 12pt converted to mm: 12 * (25.4 / 72)."""

# List indents
LIST_BODY_INDENT_MM_DEFAULT = 2.1166666667
"""Legacy 0.5em at 12pt converted to mm: 0.5 * 12 * (25.4 / 72)."""

# Figure
FIGURE_WIDTH_MM_DEFAULT = 4.2333333333
"""Legacy 1em figure width baseline at 12pt, converted to mm."""

FIGURE_GAP_MM_DEFAULT = 2.7516666667
"""Legacy 0.65em figure gap at 12pt, converted to mm."""

# Footnote
FOOTNOTE_CLEARANCE_MM_DEFAULT = 4.2333333333
"""Legacy 1em at 12pt converted to mm."""

FOOTNOTE_GAP_MM_DEFAULT = 2.1166666667
"""Legacy 0.5em at 12pt converted to mm."""

FOOTNOTE_INDENT_MM_DEFAULT = 4.2333333333
"""Legacy 1em at 12pt converted to mm."""

# Quote/terms
QUOTE_INDENT_MM_DEFAULT = 6.35
"""Legacy 1.5em at 12pt converted to mm."""

TERMS_HANGING_INDENT_MM_DEFAULT = 8.4666666667
"""Legacy 2em at 12pt converted to mm."""

# Table
TABLE_STROKE_MM_DEFAULT = 0.1763888889
"""Legacy 0.5pt converted to mm: 0.5 * (25.4 / 72)."""

TABLE_INSET_MM_DEFAULT = 1.7638888889
"""Legacy 5pt converted to mm: 5 * (25.4 / 72)."""

# Misc collection defaults
BULLET_MARKERS_DEFAULT = ["- ", "‣", "–"]
"""Default bullet markers for list nesting levels 1..3."""
