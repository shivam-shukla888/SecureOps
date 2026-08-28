import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.registry import agent_registry
from app.db.session import get_db_session
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse, AgentListResponse
from app.security.auth import verify_api_key
from app.security.rbac import require_role, RoleEnum, TenantUserContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/agents", tags=["Agent Registry"])


@router.post(
    "",
    response_model=AgentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new AI Agent",
    description="Registers an AI agent within the authenticated tenant context."
)
async def register_agent(
    agent_data: AgentCreate,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.ADMIN, RoleEnum.OPERATOR, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    logger.info(f"Registering new agent '{agent_data.name}' for tenant '{ctx.tenant_id}' (provider: {agent_data.provider})")
    agent = await agent_registry.create_agent(tenant_id=ctx.tenant_id, data=agent_data, db=db)
    return agent


@router.get(
    "",
    response_model=AgentListResponse,
    summary="List all registered AI Agents",
    description="Lists all AI agents registered under the authenticated tenant."
)
async def list_agents(
    request: Request,
    enabled_only: bool = False,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.VIEWER, RoleEnum.OPERATOR, RoleEnum.APPROVER, RoleEnum.ADMIN, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    agents = await agent_registry.list_agents(tenant_id=ctx.tenant_id, enabled_only=enabled_only, db=db)
    return AgentListResponse(agents=agents, total=len(agents))


@router.get(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Get details of a specific AI Agent",
    description="Retrieves registration and policy configuration for a specific agent."
)
async def get_agent(
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
    return agent


@router.patch(
    "/{agent_id}",
    response_model=AgentResponse,
    summary="Update AI Agent configuration",
    description="Updates configuration, enabled status, or tool permissions for an existing agent."
)
async def update_agent(
    agent_id: str,
    update_data: AgentUpdate,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.ADMIN, RoleEnum.OPERATOR, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    agent = await agent_registry.update_agent(tenant_id=ctx.tenant_id, agent_id=agent_id, data=update_data, db=db)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found or access denied."
        )
    return agent


@router.delete(
    "/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an AI Agent registration",
    description="Deletes an agent registration from the registry."
)
async def delete_agent(
    agent_id: str,
    request: Request,
    api_key: str = Depends(verify_api_key),
    ctx: TenantUserContext = Depends(require_role([RoleEnum.ADMIN, RoleEnum.OWNER])),
    db: AsyncSession = Depends(get_db_session),
):
    deleted = await agent_registry.delete_agent(tenant_id=ctx.tenant_id, agent_id=agent_id, db=db)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found or access denied."
        )
    return None
