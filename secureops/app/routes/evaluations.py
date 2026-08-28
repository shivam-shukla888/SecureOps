import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import agent_registry
from app.db.session import get_db_session
from app.security.auth import verify_api_key
from app.security.evaluations.engine import agent_evaluation_engine, AgentEvaluationResponse
from app.security.rbac import require_role, RoleEnum, TenantUserContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/agents/{agent_id}/evaluations", tags=["Agent Security Evaluations"])


class RunEvaluationRequest(BaseModel):
    test_suite: str = Field("security-baseline", description="Security test suite identifier (security-baseline, red-team-full, owasp-top-10-llm)")


@router.post(
    "",
    response_model=AgentEvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger security evaluation for an AI Agent",
    description="Executes a suite of red-team security attack scenarios against a registered AI agent and computes risk scores."
)
async def run_agent_evaluation(
    agent_id: str,
    eval_req: RunEvaluationRequest,
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

    logger.info(f"Triggering evaluation '{eval_req.test_suite}' for agent '{agent_id}' by role '{ctx.role.value}'")
    evaluation = await agent_evaluation_engine.run_evaluation(
        agent=agent,
        test_suite=eval_req.test_suite,
        tenant_id=ctx.tenant_id,
        db=db,
    )
    return evaluation


@router.get(
    "",
    response_model=List[AgentEvaluationResponse],
    summary="List all evaluation runs for an AI Agent",
    description="Retrieves history of security evaluation runs for a specific agent."
)
async def list_agent_evaluations(
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

    evaluations = await agent_evaluation_engine.list_evaluations(tenant_id=ctx.tenant_id, agent_id=agent_id, db=db)
    return evaluations


@router.get(
    "/{evaluation_id}",
    response_model=AgentEvaluationResponse,
    summary="Get details of a specific security evaluation run",
    description="Retrieves full test findings and risk score for a specific evaluation run."
)
async def get_agent_evaluation(
    agent_id: str,
    evaluation_id: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.VIEWER, RoleEnum.OPERATOR, RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    evaluation = await agent_evaluation_engine.get_evaluation(tenant_id=ctx.tenant_id, evaluation_id=evaluation_id, db=db)
    if not evaluation or evaluation.agent_id != agent_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation '{evaluation_id}' not found for agent '{agent_id}'."
        )
    return evaluation
