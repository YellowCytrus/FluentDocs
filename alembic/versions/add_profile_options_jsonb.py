"""profile options JSONB and schema version

Revision ID: a9b8c7d6e5f4
Revises: f7a8b9c0d1e2
Create Date: 2026-10-25

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision: str = "a9b8c7d6e5f4"
down_revision: Union[str, Sequence[str], None] = "f7a8b9c0d1e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "profiles" not in insp.get_table_names():
        return
    columns = {column["name"] for column in insp.get_columns("profiles")}
    if "options_schema_version" not in columns:
        op.add_column(
            "profiles",
            sa.Column(
                "options_schema_version",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("1"),
            ),
        )
    if "options" not in columns:
        op.add_column(
            "profiles",
            sa.Column(
                "options",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = inspect(conn)
    if "profiles" not in insp.get_table_names():
        return
    columns = {column["name"] for column in insp.get_columns("profiles")}
    if "options" in columns:
        op.drop_column("profiles", "options")
    if "options_schema_version" in columns:
        op.drop_column("profiles", "options_schema_version")
