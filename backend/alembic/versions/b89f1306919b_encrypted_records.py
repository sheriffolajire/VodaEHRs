"""phase4 encrypted records and signed documents

Revision ID: b89f1306919b
Revises: bf3fb467d9a3
Create Date: 2026-07-29

Adds encryption support for medical records and digital signatures.

IMPORTANT:
- This migration DOES NOT remove plaintext medical record content.
- Existing data remains untouched.
- A later backfill process encrypts all records.
- After verification, a later migration will enforce NOT NULL
  constraints and remove plaintext content.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b89f1306919b"
down_revision: str | None = "bf3fb467d9a3"
branch_labels: str |Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    ####################################################################
    # USER KEYS
    ####################################################################

    op.create_table(
        "user_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("encrypted_private_key", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_index(
        "ix_user_keys_user_id",
        "user_keys",
        ["user_id"],
    )

    ####################################################################
    # MEDICAL RECORDS
    ####################################################################

    #
    # DO NOT DROP content HERE.
    #
    # It remains until every existing record has been encrypted.
    #

    op.add_column(
        "medical_records",
        sa.Column(
            "encrypted_data",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_records",
        sa.Column(
            "encrypted_aes_key",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_records",
        sa.Column(
            "nonce",
            sa.String(255),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_records",
        sa.Column(
            "auth_tag",
            sa.String(255),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_records",
        sa.Column(
            "hash",
            sa.String(64),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_records",
        sa.Column(
            "title",
            sa.String(255),
            nullable=False,
            server_default="Untitled",
        ),
    )

    op.add_column(
        "medical_records",
        sa.Column(
            "summary",
            sa.Text(),
            nullable=False,
            server_default="",
        ),
    )

    #
    # Remove server defaults so future inserts
    # must explicitly provide values.
    #

    op.alter_column(
        "medical_records",
        "title",
        server_default=None,
    )

    op.alter_column(
        "medical_records",
        "summary",
        server_default=None,
    )

    ####################################################################
    # MEDICAL DOCUMENTS
    ####################################################################

    op.add_column(
        "medical_documents",
        sa.Column(
            "encrypted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "medical_documents",
        sa.Column(
            "nonce",
            sa.LargeBinary(),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_documents",
        sa.Column(
            "auth_tag",
            sa.LargeBinary(),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_documents",
        sa.Column(
            "wrapped_aes_key",
            sa.LargeBinary(),
            nullable=True,
        ),
    )

    op.add_column(
        "medical_documents",
        sa.Column(
            "aes_key_hash",
            sa.String(64),
            nullable=True,
        ),
    )

    op.alter_column(
        "medical_documents",
        "encrypted",
        server_default=None,
    )

    ####################################################################
    # DIGITAL SIGNATURES
    ####################################################################

    op.create_table(
        "signatures",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("record_id", sa.Uuid(), nullable=False),
        sa.Column("signer_id", sa.Uuid(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=False),
        sa.Column("algorithm", sa.String(50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["record_id"],
            ["medical_records.id"],
        ),
        sa.ForeignKeyConstraint(
            ["signer_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_signatures_record_id",
        "signatures",
        ["record_id"],
    )

    op.create_index(
        "ix_signatures_signer_id",
        "signatures",
        ["signer_id"],
    )


def downgrade() -> None:

    ####################################################################
    # SIGNATURES
    ####################################################################

    op.drop_index(
        "ix_signatures_signer_id",
        table_name="signatures",
    )

    op.drop_index(
        "ix_signatures_record_id",
        table_name="signatures",
    )

    op.drop_table("signatures")

    ####################################################################
    # MEDICAL DOCUMENTS
    ####################################################################

    op.drop_column("medical_documents", "aes_key_hash")
    op.drop_column("medical_documents", "wrapped_aes_key")
    op.drop_column("medical_documents", "auth_tag")
    op.drop_column("medical_documents", "nonce")
    op.drop_column("medical_documents", "encrypted")

    ####################################################################
    # MEDICAL RECORDS
    ####################################################################

    #
    # Plaintext content still exists,
    # so we simply remove the new columns.
    #

    op.drop_column("medical_records", "summary")
    op.drop_column("medical_records", "title")
    op.drop_column("medical_records", "hash")
    op.drop_column("medical_records", "auth_tag")
    op.drop_column("medical_records", "nonce")
    op.drop_column("medical_records", "encrypted_aes_key")
    op.drop_column("medical_records", "encrypted_data")

    ####################################################################
    # USER KEYS
    ####################################################################

    op.drop_index(
        "ix_user_keys_user_id",
        table_name="user_keys",
    )

    op.drop_table("user_keys")