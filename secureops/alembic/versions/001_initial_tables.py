"""Initial tables for audit_logs and approval_tickets

Revision ID: 001_initial_tables
Revises: 
Create Date: 2026-08-25 21:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_tables'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=128), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('intent', sa.String(length=64), nullable=False),
        sa.Column('resource', sa.String(length=256), nullable=False),
        sa.Column('ai_risk', sa.String(length=32), nullable=False),
        sa.Column('policy_risk', sa.String(length=32), nullable=False),
        sa.Column('final_decision', sa.String(length=32), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('fallback_used', sa.Boolean(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('error_status', sa.String(length=128), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_request_id'), 'audit_logs', ['request_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)

    op.create_table(
        'approval_tickets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('approval_id', sa.String(length=64), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('requester_id', sa.String(length=128), nullable=False),
        sa.Column('approver_id', sa.String(length=128), nullable=True),
        sa.Column('intent', sa.String(length=64), nullable=False),
        sa.Column('resource', sa.String(length=256), nullable=False),
        sa.Column('policy_risk', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('approval_id')
    )
    op.create_index(op.f('ix_approval_tickets_approval_id'), 'approval_tickets', ['approval_id'], unique=True)
    op.create_index(op.f('ix_approval_tickets_request_id'), 'approval_tickets', ['request_id'], unique=False)
    op.create_index(op.f('ix_approval_tickets_requester_id'), 'approval_tickets', ['requester_id'], unique=False)
    op.create_index(op.f('ix_approval_tickets_status'), 'approval_tickets', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('approval_tickets')
    op.drop_table('audit_logs')
