"""add emergency access approval workflow

Revision ID: 43fe0a81819a
Revises: eec904ba7bb0
Create Date: 2026-08-05 14:43:10.524672
"""

from collections.abc import Sequence

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision: str = '43fe0a81819a'
down_revision: str | None = 'eec904ba7bb0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add approval workflow columns to emergency_access table
    op.add_column('emergency_access', sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'))
    op.add_column('emergency_access', sa.Column('reviewed_by', sa.UUID(), nullable=True))
    op.add_column('emergency_access', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('emergency_access', sa.Column('review_notes', sa.Text(), nullable=True))
    
    # Create foreign key constraint for reviewed_by
    op.create_foreign_key(
        'fk_emergency_access_reviewed_by',
        'emergency_access', 'users',
        ['reviewed_by'], ['id']
    )
    
    # Create index on status for filtering
    op.create_index('ix_emergency_access_status', 'emergency_access', ['status'])


def downgrade() -> None:
    # Remove the columns and constraints
    op.drop_index('ix_emergency_access_status', table_name='emergency_access')
    op.drop_constraint('fk_emergency_access_reviewed_by', 'emergency_access', type_='foreignkey')
    op.drop_column('emergency_access', 'review_notes')
    op.drop_column('emergency_access', 'reviewed_at')
    op.drop_column('emergency_access', 'reviewed_by')
    op.drop_column('emergency_access', 'status')
