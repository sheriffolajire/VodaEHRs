"""add missing audit priority enum values

Revision ID: a90d1f4c8e2b
Revises: c76410270f52
Create Date: 2026-08-13
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a90d1f4c8e2b"
down_revision: str | None = "c76410270f52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add enum labels emitted by the LOW/MEDIUM audit-priority model.

    The preceding migration added audit categories but did not update the
    existing ``auditpriority`` PostgreSQL enum, which still contains only
    ``NORMAL`` and ``HIGH``. Keep ``NORMAL`` intact because it is included in
    existing audit-entry hashes; this migration only adds the missing labels.
    """

    op.execute("ALTER TYPE auditpriority ADD VALUE IF NOT EXISTS 'LOW'")
    op.execute("ALTER TYPE auditpriority ADD VALUE IF NOT EXISTS 'MEDIUM'")


def downgrade() -> None:
    """Leave added PostgreSQL enum labels in place.

    PostgreSQL does not safely support removing enum values, and deleting them
    could invalidate persisted audit data. Older application versions continue
    to work while the additional labels remain unused.
    """
