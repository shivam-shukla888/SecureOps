import asyncio
import pytest
from fastapi import HTTPException
from app.adapters.base import AgentExecutionRequest
from app.adapters.factory import get_agent_adapter
from app.adapters.http_adapter import GenericHTTPAgentAdapter
from app.adapters.simulated_adapter import SimulatedAgentAdapter
from app.schemas.agent import AgentResponse
from datetime import datetime, timezone


def test_http_adapter_ssrf_rejection():
    # Cloud metadata endpoint must be rejected by SSRF validator in GenericHTTPAgentAdapter
    with pytest.raises(HTTPException) as exc_info:
        GenericHTTPAgentAdapter(endpoint_url="http://169.254.169.254/latest/meta-data/")
    assert exc_info.value.status_code == 400
    assert "Security Violation" in exc_info.value.detail


def test_simulated_agent_adapter_execution():
    adapter = SimulatedAgentAdapter(agent_name="TestSupportBot")
    req = AgentExecutionRequest(
        agent_id="agent_123",
        tenant_id="tenant_default",
        user_id="user_1",
        prompt="Please help me read_data user_records",
    )

    res = asyncio.run(adapter.execute(req))
    assert res.agent_id == "agent_123"
    assert "TestSupportBot" in res.output_text
    assert len(res.tool_calls) == 1
    assert res.tool_calls[0].tool_name == "read_data"


def test_adapter_factory():
    agent_sim = AgentResponse(
        agent_id="ag_1",
        tenant_id="tenant_1",
        name="SimAgent",
        provider="custom",
        enabled=True,
        risk_level="LOW",
        allowed_tools=["search"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    adapter = get_agent_adapter(agent_sim)
    assert isinstance(adapter, SimulatedAgentAdapter)
