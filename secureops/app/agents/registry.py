import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentModel
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse

logger = logging.getLogger(__name__)


class AgentRegistry:
    def __init__(self):
        # In-memory fallback dictionary keyed by (tenant_id, agent_id)
        self._in_memory_agents: Dict[str, AgentResponse] = {}

    async def create_agent(
        self,
        tenant_id: str,
        data: AgentCreate,
        db: Optional[AsyncSession] = None,
    ) -> AgentResponse:
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        allowed_tools_json = json.dumps(data.allowed_tools)

        if db is not None:
            try:
                db_agent = AgentModel(
                    agent_id=agent_id,
                    tenant_id=tenant_id,
                    name=data.name,
                    description=data.description,
                    provider=data.provider.lower(),
                    framework=data.framework.lower() if data.framework else None,
                    endpoint_url=data.endpoint_url,
                    enabled=True,
                    risk_level=data.risk_level.upper(),
                    allowed_tools=allowed_tools_json,
                    created_at=now,
                    updated_at=now,
                )
                db.add(db_agent)
                await db.commit()
                await db.refresh(db_agent)

                response = self._to_response(db_agent)
                self._in_memory_agents[f"{tenant_id}:{agent_id}"] = response
                return response
            except Exception as exc:
                logger.warning(f"Database error creating agent; falling back to in-memory: {exc}")
                await db.rollback()

        response = AgentResponse(
            agent_id=agent_id,
            tenant_id=tenant_id,
            name=data.name,
            provider=data.provider.lower(),
            framework=data.framework.lower() if data.framework else None,
            description=data.description,
            endpoint_url=data.endpoint_url,
            enabled=True,
            risk_level=data.risk_level.upper(),
            allowed_tools=data.allowed_tools,
            created_at=now,
            updated_at=now,
        )
        self._in_memory_agents[f"{tenant_id}:{agent_id}"] = response
        return response

    async def get_agent(
        self,
        tenant_id: str,
        agent_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[AgentResponse]:
        if db is not None:
            try:
                stmt = select(AgentModel).where(
                    AgentModel.tenant_id == tenant_id,
                    AgentModel.agent_id == agent_id,
                )
                result = await db.execute(stmt)
                db_agent = result.scalar_one_or_none()
                if db_agent:
                    return self._to_response(db_agent)
            except Exception as exc:
                logger.warning(f"Database error fetching agent; attempting in-memory fallback: {exc}")

        return self._in_memory_agents.get(f"{tenant_id}:{agent_id}")

    async def list_agents(
        self,
        tenant_id: str,
        enabled_only: bool = False,
        db: Optional[AsyncSession] = None,
    ) -> List[AgentResponse]:
        if db is not None:
            try:
                stmt = select(AgentModel).where(AgentModel.tenant_id == tenant_id)
                if enabled_only:
                    stmt = stmt.where(AgentModel.enabled.is_(True))
                stmt = stmt.order_by(AgentModel.created_at.desc())

                result = await db.execute(stmt)
                db_agents = result.scalars().all()
                if db_agents:
                    return [self._to_response(a) for a in db_agents]
            except Exception as exc:
                logger.warning(f"Database error listing agents; attempting in-memory fallback: {exc}")

        results = []
        prefix = f"{tenant_id}:"
        for key, agent in self._in_memory_agents.items():
            if key.startswith(prefix):
                if not enabled_only or agent.enabled:
                    results.append(agent)
        return sorted(results, key=lambda a: a.created_at, reverse=True)

    async def update_agent(
        self,
        tenant_id: str,
        agent_id: str,
        data: AgentUpdate,
        db: Optional[AsyncSession] = None,
    ) -> Optional[AgentResponse]:
        existing = await self.get_agent(tenant_id, agent_id, db)
        if not existing:
            return None

        now = datetime.now(timezone.utc)
        updated_dict = existing.model_dump()

        if data.name is not None:
            updated_dict["name"] = data.name
        if data.provider is not None:
            updated_dict["provider"] = data.provider.lower()
        if data.framework is not None:
            updated_dict["framework"] = data.framework.lower()
        if data.description is not None:
            updated_dict["description"] = data.description
        if data.endpoint_url is not None:
            updated_dict["endpoint_url"] = data.endpoint_url
        if data.allowed_tools is not None:
            updated_dict["allowed_tools"] = data.allowed_tools
        if data.enabled is not None:
            updated_dict["enabled"] = data.enabled
        if data.risk_level is not None:
            updated_dict["risk_level"] = data.risk_level.upper()
        updated_dict["updated_at"] = now

        new_response = AgentResponse(**updated_dict)
        self._in_memory_agents[f"{tenant_id}:{agent_id}"] = new_response

        if db is not None:
            try:
                update_values = {}
                if data.name is not None: update_values["name"] = data.name
                if data.provider is not None: update_values["provider"] = data.provider.lower()
                if data.framework is not None: update_values["framework"] = data.framework.lower()
                if data.description is not None: update_values["description"] = data.description
                if data.endpoint_url is not None: update_values["endpoint_url"] = data.endpoint_url
                if data.allowed_tools is not None: update_values["allowed_tools"] = json.dumps(data.allowed_tools)
                if data.enabled is not None: update_values["enabled"] = data.enabled
                if data.risk_level is not None: update_values["risk_level"] = data.risk_level.upper()
                update_values["updated_at"] = now

                stmt = (
                    update(AgentModel)
                    .where(AgentModel.tenant_id == tenant_id, AgentModel.agent_id == agent_id)
                    .values(**update_values)
                )
                await db.execute(stmt)
                await db.commit()
            except Exception as exc:
                logger.warning(f"Database error updating agent: {exc}")
                await db.rollback()

        return new_response

    async def delete_agent(
        self,
        tenant_id: str,
        agent_id: str,
        db: Optional[AsyncSession] = None,
    ) -> bool:
        existed = f"{tenant_id}:{agent_id}" in self._in_memory_agents
        self._in_memory_agents.pop(f"{tenant_id}:{agent_id}", None)

        if db is not None:
            try:
                stmt = delete(AgentModel).where(
                    AgentModel.tenant_id == tenant_id,
                    AgentModel.agent_id == agent_id,
                )
                res = await db.execute(stmt)
                await db.commit()
                if res.rowcount > 0:
                    existed = True
            except Exception as exc:
                logger.warning(f"Database error deleting agent: {exc}")
                await db.rollback()

        return existed

    def _to_response(self, model: AgentModel) -> AgentResponse:
        try:
            tools = json.loads(model.allowed_tools) if model.allowed_tools else []
        except Exception:
            tools = []

        return AgentResponse(
            agent_id=model.agent_id,
            tenant_id=model.tenant_id,
            name=model.name,
            provider=model.provider,
            framework=model.framework,
            description=model.description,
            endpoint_url=model.endpoint_url,
            enabled=model.enabled,
            risk_level=model.risk_level,
            allowed_tools=tools,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


agent_registry = AgentRegistry()
