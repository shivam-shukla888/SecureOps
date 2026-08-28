"""Add agents, agent_evaluations, evaluation_findings, and agent_policies tables

Revision ID: 003_agent_security_gateway
Revises: 002_production_tables
Create Date: 2026-08-28 17:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '003_agent_security_gateway'
down_revision: Union[str, None] = '002_production_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('provider', sa.String(length=64), nullable=False),
        sa.Column('framework', sa.String(length=64), nullable=True),
        sa.Column('endpoint_url', sa.String(length=512), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('risk_level', sa.String(length=32), nullable=False, server_default='LOW'),
        sa.Column('allowed_tools', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_agent_id'), 'agents', ['agent_id'], unique=True)
    op.create_index(op.f('ix_agents_tenant_id'), 'agents', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_agents_created_at'), 'agents', ['created_at'], unique=False)

    # Create agent_evaluations table
    op.create_table(
        'agent_evaluations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('evaluation_id', sa.String(length=64), nullable=False),
        sa.Column('agent_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('test_suite', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='COMPLETED'),
        sa.Column('total_tests', sa.Integer(), nullable=False),
        sa.Column('passed', sa.Integer(), nullable=False),
        sa.Column('failed', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_evaluations_evaluation_id'), 'agent_evaluations', ['evaluation_id'], unique=True)
    op.create_index(op.f('ix_agent_evaluations_agent_id'), 'agent_evaluations', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_evaluations_tenant_id'), 'agent_evaluations', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_agent_evaluations_created_at'), 'agent_evaluations', ['created_at'], unique=False)

    # Create evaluation_findings table
    op.create_table(
        'evaluation_findings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('finding_id', sa.String(length=64), nullable=False),
        sa.Column('evaluation_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('test_id', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('attack_input', sa.Text(), nullable=False),
        sa.Column('expected_behavior', sa.String(length=32), nullable=False),
        sa.Column('actual_behavior', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluation_findings_finding_id'), 'evaluation_findings', ['finding_id'], unique=True)
    op.create_index(op.f('ix_evaluation_findings_evaluation_id'), 'evaluation_findings', ['evaluation_id'], unique=False)
    op.create_index(op.f('ix_evaluation_findings_tenant_id'), 'evaluation_findings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_evaluation_findings_created_at'), 'evaluation_findings', ['created_at'], unique=False)

    # Create agent_policies table
    op.create_table(
        'agent_policies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('policy_id', sa.String(length=64), nullable=False),
        sa.Column('agent_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('max_risk_threshold', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('require_approval_tools', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('blocked_tools', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_policies_policy_id'), 'agent_policies', ['policy_id'], unique=True)
    op.create_index(op.f('ix_agent_policies_agent_id'), 'agent_policies', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_policies_tenant_id'), 'agent_policies', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_table('agent_policies')
    op.drop_table('evaluation_findings')
    op.drop_table('agent_evaluations')
    op.drop_table('agents')
