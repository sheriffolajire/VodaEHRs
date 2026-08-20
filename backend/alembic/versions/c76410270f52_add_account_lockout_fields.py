"""add_account_lockout_fields

Revision ID: c76410270f52
Revises: 4cc20641574a
Create Date: 2026-08-09 02:15:47.968892
"""

from collections.abc import Sequence

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision: str = 'c76410270f52'
down_revision: str | None = '4cc20641574a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add account lockout fields to users table."""
    # Add failed_login_attempts column
    op.add_column(
        'users',
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0')
    )
    
    # Add locked_until column
    op.add_column(
        'users',
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Remove account lockout fields from users table."""
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
