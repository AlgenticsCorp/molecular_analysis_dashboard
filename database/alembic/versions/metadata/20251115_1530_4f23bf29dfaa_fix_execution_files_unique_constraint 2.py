"""fix_execution_files_unique_constraint

Revision ID: 4f23bf29dfaa
Revises: 80835240e483
Create Date: 2025-11-15 15:30:00.000000+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4f23bf29dfaa"
down_revision = "80835240e483"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Restore deterministic conflict target for execution_files upserts."""
    op.execute("""
        WITH duplicate_rows AS (
            SELECT ctid
            FROM (
                SELECT ctid,
                       ROW_NUMBER() OVER (
                           PARTITION BY execution_id, parameter_name, file_type
                           ORDER BY uploaded_at DESC, file_id DESC
                       ) AS rn
                FROM execution_files
                WHERE execution_id IS NOT NULL
            ) ranked
            WHERE rn > 1
        )
        DELETE FROM execution_files ef
        USING duplicate_rows d
        WHERE ef.ctid = d.ctid;
    """)

    op.execute("DROP INDEX IF EXISTS idx_execution_files_execution_context;")

    op.create_unique_constraint(
        "execution_files_execution_id_parameter_name_file_type_key",
        "execution_files",
        ["execution_id", "parameter_name", "file_type"],
    )


def downgrade() -> None:
    """Recreate the partial unique index removed in upgrade."""
    op.drop_constraint(
        "execution_files_execution_id_parameter_name_file_type_key",
        "execution_files",
        type_="unique",
    )

    op.create_index(
        "idx_execution_files_execution_context",
        "execution_files",
        ["execution_id", "parameter_name", "file_type"],
        unique=True,
        postgresql_where=sa.text("execution_id IS NOT NULL"),
    )
