"""Merge heads

Revision ID: 65fc754e8e00
Revises: f1a2b3c4d5e6, a90d1f4c8e2b
Create Date: 2026-08-30 18:31:04.039638
"""

from collections.abc import Sequence

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision: str = '65fc754e8e00'
down_revision: str | None = ('f1a2b3c4d5e6', 'a90d1f4c8e2b')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
