"""outline_styles: структурный отступ вместо строки-выражения

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-10-26

Старое поле ``indent`` хранило произвольную строку Typst и исполнялось через
``eval``. Значение переносится в ``indent_mode``/``indent_mm``, старая колонка
остаётся в БД и больше не читается.
"""

import json
import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, Sequence[str], None] = "a9b8c7d6e5f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_MM_PER_UNIT = {"mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72.0}
# em зависит от кегля; для миграции берём дефолтные 12 pt.
_EM_MM = 12.0 * 25.4 / 72.0


def _parse_indent(value: str) -> tuple[str, float]:
    """Переводит старую строку в (режим, мм) без исполнения кода."""
    text = (value or "").strip()
    if text in {"", "auto"}:
        return "auto", 0.0
    if text == "none":
        return "none", 0.0
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*(mm|cm|in|pt|em)", text)
    if not match:
        return "auto", 0.0
    number = float(match.group(1))
    unit = match.group(2)
    factor = _EM_MM if unit == "em" else _MM_PER_UNIT[unit]
    return "custom", round(number * factor, 6)


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "outline_styles" not in insp.get_table_names():
        return
    columns = {column["name"] for column in insp.get_columns("outline_styles")}
    if "indent_mode" not in columns:
        op.add_column(
            "outline_styles",
            sa.Column(
                "indent_mode",
                sa.String(length=16),
                nullable=False,
                server_default=sa.text("'auto'"),
            ),
        )
    if "indent_mm" not in columns:
        op.add_column(
            "outline_styles",
            sa.Column(
                "indent_mm",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )
    if "indent" not in columns:
        return
    rows = conn.execute(sa.text("SELECT id, indent FROM outline_styles")).fetchall()
    for row_id, old_indent in rows:
        mode, value_mm = _parse_indent(old_indent or "")
        conn.execute(
            sa.text(
                "UPDATE outline_styles "
                "SET indent_mode = :mode, indent_mm = :value_mm WHERE id = :row_id"
            ),
            {"mode": mode, "value_mm": value_mm, "row_id": row_id},
        )

    # Тот же перенос в JSONB: старый ключ outline.indent больше не опция реестра.
    if "profiles" not in insp.get_table_names():
        return
    profile_columns = {column["name"] for column in insp.get_columns("profiles")}
    if "options" not in profile_columns:
        return
    profiles = conn.execute(
        sa.text("SELECT id, options FROM profiles WHERE options ? 'outline'")
    ).fetchall()
    for profile_id, options in profiles:
        if not isinstance(options, dict):
            continue
        outline = options.get("outline")
        if not isinstance(outline, dict) or "indent" not in outline:
            continue
        mode, value_mm = _parse_indent(str(outline.get("indent") or ""))
        outline.setdefault("indent_mode", mode)
        outline.setdefault("indent_mm", value_mm)
        outline.pop("indent", None)
        conn.execute(
            sa.text("UPDATE profiles SET options = CAST(:options AS jsonb) WHERE id = :profile_id"),
            {"options": json.dumps(options), "profile_id": profile_id},
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "outline_styles" not in insp.get_table_names():
        return
    columns = {column["name"] for column in insp.get_columns("outline_styles")}
    if "indent_mm" in columns:
        op.drop_column("outline_styles", "indent_mm")
    if "indent_mode" in columns:
        op.drop_column("outline_styles", "indent_mode")
