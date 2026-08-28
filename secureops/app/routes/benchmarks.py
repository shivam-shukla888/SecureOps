import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import agent_registry
from app.db.session import get_db_session
from app.security.auth import verify_api_key
from app.security.benchmarks.engine import agent_benchmark_engine, AgentBenchmarkResponse
from app.security.rbac import require_role, RoleEnum, TenantUserContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/agents/{agent_id}/benchmarks", tags=["Agent Security Benchmarks"])


class RunBenchmarkRequest(BaseModel):
    benchmark: str = Field("security-baseline-v1", description="Standard benchmark suite identifier (e.g. security-baseline-v1)")
    adaptive: bool = Field(False, description="Enable adaptive testing loop to trigger targeted follow-up scenarios based on initial findings")


@router.post(
    "",
    response_model=AgentBenchmarkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run standardized security benchmark for an AI Agent",
    description="Executes the standardized security-baseline-v1 benchmark suite against an agent, generating a deterministic SecureOps Security Scorecard."
)
async def run_agent_benchmark(
    agent_id: str,
    benchmark_req: RunBenchmarkRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.ADMIN, RoleEnum.OPERATOR, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    agent = await agent_registry.get_agent(tenant_id=ctx.tenant_id, agent_id=agent_id, db=db)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found or access denied."
        )

    logger.info(f"Triggering benchmark '{benchmark_req.benchmark}' (adaptive={benchmark_req.adaptive}) for agent '{agent_id}' by role '{ctx.role.value}'")
    benchmark = await agent_benchmark_engine.run_benchmark(
        agent=agent,
        benchmark_name=benchmark_req.benchmark,
        adaptive=benchmark_req.adaptive,
        tenant_id=ctx.tenant_id,
        db=db,
    )
    return benchmark



@router.get(
    "",
    response_model=List[AgentBenchmarkResponse],
    summary="List all benchmark runs for an AI Agent",
    description="Retrieves history of standardized benchmark runs and scorecards for a specific agent."
)
async def list_agent_benchmarks(
    agent_id: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.VIEWER, RoleEnum.OPERATOR, RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    agent = await agent_registry.get_agent(tenant_id=ctx.tenant_id, agent_id=agent_id, db=db)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found or access denied."
        )

    benchmarks = await agent_benchmark_engine.list_benchmarks(tenant_id=ctx.tenant_id, agent_id=agent_id, db=db)
    return benchmarks


@router.get(
    "/{benchmark_id}",
    response_model=AgentBenchmarkResponse,
    summary="Get details and scorecard of a specific benchmark run",
    description="Retrieves category breakdown, risk score, and evidence for a specific benchmark run."
)
async def get_agent_benchmark(
    agent_id: str,
    benchmark_id: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.VIEWER, RoleEnum.OPERATOR, RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    benchmark = await agent_benchmark_engine.get_benchmark(tenant_id=ctx.tenant_id, benchmark_id=benchmark_id, db=db)
    if not benchmark or benchmark.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Benchmark '{benchmark_id}' not found for agent '{agent_id}'."
        )
    return benchmark
