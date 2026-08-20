"""add_audit_category_and_update_priority

Revision ID: 4cc20641574a
Revises: 43fe0a81819a
Create Date: 2026-08-09 01:23:39.256835
"""

from collections.abc import Sequence

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401
from sqlalchemy.dialects import postgresql

revision: str = '4cc20641574a'
down_revision: str | None = '43fe0a81819a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add category column to audit_logs and update priority enum."""
    # Create category enum
    category_enum = postgresql.ENUM(
        'AUTH', 'ACCESS', 'MODIFY', 'CONSENT', 'EMERGENCY', 'SECURITY', 'SYSTEM',
        name='auditcategory',
        create_type=False
    )
    category_enum.create(op.get_bind(), checkfirst=True)
    
    # Add category column to audit_logs
    op.add_column(
        'audit_logs',
        sa.Column(
            'category',
            sa.Enum('AUTH', 'ACCESS', 'MODIFY', 'CONSENT', 'EMERGENCY', 'SECURITY', 'SYSTEM', name='auditcategory'),
            nullable=False,
            server_default='ACCESS'
        )
    )
    
    # Create index on category
    op.create_index(op.f('ix_audit_logs_category'), 'audit_logs', ['category'], unique=False)
    
    # Note: Priority enum values (LOW, MEDIUM, HIGH) are already defined in the model
    # The existing values NORMAL and HIGH map to MEDIUM and HIGH respectively
    # We keep the existing data as-is since the model now accepts both old and new values


def downgrade() -> None:
    """Remove category column and revert priority enum."""
    # Drop category index
    op.drop_index(op.f('ix_audit_logs_category'), table_name='audit_logs')
    
    # Drop category column
    op.drop_column('audit_logs', 'category')
    
    # Revert priority values: LOW/MEDIUM -> NORMAL, HIGH -> HIGH
    op.execute("UPDATE audit_logs SET priority = 'NORMAL' WHERE priority IN ('LOW', 'MEDIUM')")
