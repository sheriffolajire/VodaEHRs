"""Add nursing_tasks table

Revision ID: c85d14a05388
Revises: 65fc754e8e00
Create Date: 2026-08-30 18:35:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c85d14a05388'
down_revision: str | None = '65fc754e8e00'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    
    # Create enums using raw SQL with IF NOT EXISTS
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_type') THEN
                CREATE TYPE task_type AS ENUM ('vitals', 'medication', 'wound_care', 'patient_education', 'assessment', 'documentation', 'other');
            END IF;
        END $$;
    """))
    
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_status') THEN
                CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled');
            END IF;
        END $$;
    """))
    
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'task_priority') THEN
                CREATE TYPE task_priority AS ENUM ('low', 'normal', 'high', 'urgent');
            END IF;
        END $$;
    """))
    
    # Check if table exists before creating
    result = conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'nursing_tasks'"))
    if not result.scalar():
        # Create nursing_tasks table using raw SQL for enum columns
        conn.execute(sa.text("""
            CREATE TABLE nursing_tasks (
                id UUID NOT NULL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                task_type task_type NOT NULL,
                status task_status NOT NULL DEFAULT 'pending',
                priority task_priority NOT NULL DEFAULT 'normal',
                patient_id UUID NOT NULL REFERENCES patients(id),
                assigned_to UUID NOT NULL REFERENCES users(id),
                assigned_by UUID NOT NULL REFERENCES users(id),
                due_date TIMESTAMP WITH TIME ZONE,
                completed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            );
        """))
    # ### end Alembic commands ###


def downgrade() -> None:
    conn = op.get_bind()
    
    # Drop table if exists
    result = conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'nursing_tasks'"))
    if result.scalar():
        op.drop_table('nursing_tasks')
    
    # Drop enums if they exist
    for enum_name in ['task_type', 'task_status', 'task_priority']:
        result = conn.execute(sa.text(f"SELECT 1 FROM pg_type WHERE typname = '{enum_name}'"))
        if result.scalar():
            sa.Enum(name=enum_name).drop(op.get_bind())
    # ### end Alembic commands ###
