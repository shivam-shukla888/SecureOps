"""Add agent_benchmarks and benchmark_findings tables

Revision ID: 004_agent_benchmarks
Revises: 003_agent_security_gateway
Create Date: 2026-08-28 18:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '004_agent_benchmarks'
down_revision: Union[str, None] = '003_agent_security_gateway'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_benchmarks table
    op.create_table(
        'agent_benchmarks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('benchmark_id', sa.String(length=64), nullable=False),
        sa.Column('agent_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('benchmark_name', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='COMPLETED'),
        sa.Column('total_tests', sa.Integer(), nullable=False),
        sa.Column('passed', sa.Integer(), nullable=False),
        sa.Column('failed', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False),
        sa.Column('risk_level', sa.String(length=32), nullable=False),
        sa.Column('category_scores', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_benchmarks_benchmark_id'), 'agent_benchmarks', ['benchmark_id'], unique=True)
    op.create_index(op.f('ix_agent_benchmarks_agent_id'), 'agent_benchmarks', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_benchmarks_tenant_id'), 'agent_benchmarks', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_agent_benchmarks_created_at'), 'agent_benchmarks', ['created_at'], unique=False)

    # Create benchmark_findings table
    op.create_table(
        'benchmark_findings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('finding_id', sa.String(length=64), nullable=False),
        sa.Column('benchmark_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False),
        sa.Column('test_id', sa.String(length=64), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('attack_input', sa.Text(), nullable=False),
        sa.Column('expected_behavior', sa.String(length=32), nullable=False),
        sa.Column('actual_behavior', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('evidence', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_benchmark_findings_finding_id'), 'benchmark_findings', ['finding_id'], unique=True)
    op.create_index(op.f('ix_benchmark_findings_benchmark_id'), 'benchmark_findings', ['benchmark_id'], unique=False)
    op.create_index(op.f('ix_benchmark_findings_tenant_id'), 'benchmark_findings', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_benchmark_findings_created_at'), 'benchmark_findings', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_table('benchmark_findings')
    op.drop_table('agent_benchmarks')
