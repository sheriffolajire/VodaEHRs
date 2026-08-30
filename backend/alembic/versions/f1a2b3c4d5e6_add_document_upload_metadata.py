"""Add document upload metadata fields

Revision ID: f1a2b3c4d5e6
Revises: 43fe0a81819a
Create Date: 2026-08-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '43fe0a81819a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add upload purpose and target tracking fields."""
    
    # Create enum types first
    op.execute("CREATE TYPE uploadpurpose AS ENUM ('lab_results', 'prescriptions', 'imaging', 'consent_forms', 'general')")
    op.execute("CREATE TYPE uploadedfortype AS ENUM ('patient', 'department', 'external_provider', 'internal_reference')")
    
    # Add new columns to medical_documents table
    op.add_column(
        'medical_documents',
        sa.Column(
            'upload_purpose',
            sa.Enum('lab_results', 'prescriptions', 'imaging', 'consent_forms', 'general', name='uploadpurpose'),
            nullable=False,
            server_default='general'
        )
    )
    
    op.add_column(
        'medical_documents',
        sa.Column('uploaded_for', sa.String(255), nullable=True)
    )
    
    op.add_column(
        'medical_documents',
        sa.Column(
            'uploaded_for_type',
            sa.Enum('patient', 'department', 'external_provider', 'internal_reference', name='uploadedfortype'),
            nullable=True
        )
    )
    
    # Add index for common queries
    op.create_index(
        'ix_medical_documents_upload_purpose',
        'medical_documents',
        ['upload_purpose']
    )
    
    op.create_index(
        'ix_medical_documents_uploaded_for',
        'medical_documents',
        ['uploaded_for']
    )


def downgrade() -> None:
    """Remove upload metadata fields."""
    
    # Drop indexes
    op.drop_index('ix_medical_documents_uploaded_for')
    op.drop_index('ix_medical_documents_upload_purpose')
    
    # Drop columns
    op.drop_column('medical_documents', 'uploaded_for_type')
    op.drop_column('medical_documents', 'uploaded_for')
    op.drop_column('medical_documents', 'upload_purpose')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS uploadedfortype')
    op.execute('DROP TYPE IF EXISTS uploadpurpose')
