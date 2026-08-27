"""Add tenant_id, indexes, api_credentials, and idempotency_records tables for production hardening

Revision ID: 002_production_tables
Revises: 001_initial_tables
Create Date: 2026-08-26 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_production_tables'
down_revision: Union[str, None] = '001_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tenant_id and indexes to audit_logs
    op.add_column('audit_logs', sa.Column('tenant_id', sa.String(length=128), nullable=False, server_default='tenant_default'))
    op.create_index(op.f('ix_audit_logs_tenant_id'), 'audit_logs', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_timestamp'), 'audit_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_audit_logs_final_decision'), 'audit_logs', ['final_decision'], unique=False)

    # Add tenant_id and indexes to approval_tickets
    op.add_column('approval_tickets', sa.Column('tenant_id', sa.String(length=128), nullable=False, server_default='tenant_default'))
    op.create_index(op.f('ix_approval_tickets_tenant_id'), 'approval_tickets', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_approval_tickets_created_at'), 'approval_tickets', ['created_at'], unique=False)

    # Create api_credentials table
    op.create_table(
        'api_credentials',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('credential_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('key_hash', sa.String(length=128), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('credential_id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_credentials_credential_id'), 'api_credentials', ['credential_id'], unique=True)
    op.create_index(op.f('ix_api_credentials_tenant_id'), 'api_credentials', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_api_credentials_user_id'), 'api_credentials', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_credentials_key_hash'), 'api_credentials', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_credentials_created_at'), 'api_credentials', ['created_at'], unique=False)

    # Create idempotency_records table
    op.create_table(
        'idempotency_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('composite_key', sa.String(length=256), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('response_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('composite_key')
    )
    op.create_index(op.f('ix_idempotency_records_composite_key'), 'idempotency_records', ['composite_key'], unique=True)
    op.create_index(op.f('ix_idempotency_records_tenant_id'), 'idempotency_records', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_idempotency_records_user_id'), 'idempotency_records', ['user_id'], unique=False)
    op.create_index(op.f('ix_idempotency_records_idempotency_key'), 'idempotency_records', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_idempotency_records_created_at'), 'idempotency_records', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('idempotency_records')
    op.drop_table('api_credentials')
    op.drop_index(op.f('ix_approval_tickets_created_at'), table_name='approval_tickets')
    op.drop_index(op.f('ix_approval_tickets_tenant_id'), table_name='approval_tickets')
    op.drop_column('approval_tickets', 'tenant_id')
    op.drop_index(op.f('ix_audit_logs_final_decision'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_timestamp'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_tenant_id'), table_name='audit_logs')
    op.drop_column('audit_logs', 'tenant_id')
