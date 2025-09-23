"""Initial metadata database schema

Revision ID: 001_meta
Revises:
Create Date: 2025-09-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_meta'
down_revision = None
branch_labels = ('metadata',)
depends_on = None


def upgrade() -> None:
    """Create initial metadata database schema."""

    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # Create organizations table
    op.create_table(
        'organizations',
        sa.Column('org_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('quotas', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('settings', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('profile', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )

    # Create memberships table (user-organization relationship)
    op.create_table(
        'memberships',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id', 'org_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ondelete='CASCADE'),
    )

    # Create roles table
    op.create_table(
        'roles',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('org_id', 'name', name='uq_roles_org_name'),
    )

    # Create role_permissions table
    op.create_table(
        'role_permissions',
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('permission', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('role_id', 'permission'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='CASCADE'),
    )

    # Create membership_roles table
    op.create_table(
        'membership_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('user_id', 'org_id', 'role_id'),
        sa.ForeignKeyConstraint(['user_id', 'org_id'], ['memberships.user_id', 'memberships.org_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id'], ondelete='CASCADE'),
    )

    # Create molecules table
    op.create_table(
        'molecules',
        sa.Column('molecule_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('format', sa.String(10), nullable=False),
        sa.Column('uri', sa.String(500), nullable=False),
        sa.Column('checksum', sa.String(64), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('properties', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visibility', sa.String(20), nullable=False, server_default='private'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.user_id'], ondelete='CASCADE'),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['org_id'], ['organizations.org_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='SET NULL'),
    )

    # Create indexes for performance
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_memberships_user_org', 'memberships', ['user_id', 'org_id'])
    op.create_index('idx_membership_roles_org_user', 'membership_roles', ['org_id', 'user_id'])
    op.create_index('idx_molecules_org_created', 'molecules', ['org_id', 'created_at'])
    op.create_index('idx_audit_logs_org_ts', 'audit_logs', ['org_id', 'ts'])
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])


def downgrade() -> None:
    """Drop metadata database schema."""
    op.drop_table('audit_logs')
    op.drop_table('molecules')
    op.drop_table('membership_roles')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('memberships')
    op.drop_table('users')
    op.drop_table('organizations')
