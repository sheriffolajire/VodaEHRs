"""Phase 5: consent, emergency_access, record_versions, audit_logs

Revision ID: eec904ba7bb0
Revises: b89f1306919b
Create Date: 2026-08-04 21:45:07.124227
"""

from collections.abc import Sequence

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401

revision: str = 'eec904ba7bb0'
down_revision: str | None = 'b89f1306919b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Phase 5 tables: consent, emergency_access, record_versions, audit_logs."""
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=True),
        sa.Column('patient_id', sa.Uuid(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('priority', sa.Enum('NORMAL', 'HIGH', name='auditpriority'), nullable=False),
        sa.Column('prev_hash', sa.String(length=64), nullable=True),
        sa.Column('entry_hash', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('entry_hash')
    )
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_action_created', 'audit_logs', ['action', 'created_at'], unique=False)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_logs_patient_id'), 'audit_logs', ['patient_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_priority'), 'audit_logs', ['priority'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    
    # Create consents table
    op.create_table(
        'consents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.Uuid(), nullable=False),
        sa.Column('clinician_id', sa.Uuid(), nullable=False),
        sa.Column('record_type', sa.String(length=50), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['clinician_id'], ['users.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consents_clinician_id'), 'consents', ['clinician_id'], unique=False)
    op.create_index(op.f('ix_consents_patient_id'), 'consents', ['patient_id'], unique=False)
    
    # Create emergency_access table
    op.create_table(
        'emergency_access',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('clinician_id', sa.Uuid(), nullable=False),
        sa.Column('patient_id', sa.Uuid(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_by', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['clinician_id'], ['users.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emergency_access_clinician_id'), 'emergency_access', ['clinician_id'], unique=False)
    op.create_index(op.f('ix_emergency_access_patient_id'), 'emergency_access', ['patient_id'], unique=False)
    
    # Create record_versions table
    op.create_table(
        'record_versions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('record_id', sa.Uuid(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('encrypted_data', sa.LargeBinary(), nullable=False),
        sa.Column('encrypted_aes_key', sa.LargeBinary(), nullable=False),
        sa.Column('nonce', sa.LargeBinary(), nullable=False),
        sa.Column('auth_tag', sa.LargeBinary(), nullable=False),
        sa.Column('hash', sa.String(length=64), nullable=False),
        sa.Column('created_by', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['record_id'], ['medical_records.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_record_versions_record_id'), 'record_versions', ['record_id'], unique=False)
    op.create_index('ix_record_versions_record_id_version', 'record_versions', ['record_id', 'version'], unique=False)


def downgrade() -> None:
    """Drop Phase 5 tables."""
    # Drop in reverse order to handle foreign keys
    op.drop_index('ix_record_versions_record_id_version', table_name='record_versions')
    op.drop_index(op.f('ix_record_versions_record_id'), table_name='record_versions')
    op.drop_table('record_versions')
    
    op.drop_index(op.f('ix_emergency_access_patient_id'), table_name='emergency_access')
    op.drop_index(op.f('ix_emergency_access_clinician_id'), table_name='emergency_access')
    op.drop_table('emergency_access')
    
    op.drop_index(op.f('ix_consents_patient_id'), table_name='consents')
    op.drop_index(op.f('ix_consents_clinician_id'), table_name='consents')
    op.drop_table('consents')
    
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_priority'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_patient_id'), table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action_created', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_table('audit_logs')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS auditpriority")
