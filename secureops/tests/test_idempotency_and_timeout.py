import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from app.schemas.decision import IntentEnum, RiskEnum, PolicyDecision, DecisionEnum
from app.security.idempotency import IdempotencyManager
from app.executor.dispatcher import ExecutionDispatcher
from app.tools.registry import ToolRegistry, ToolDefinition
from app.tools.schemas import SearchDocumentInput


def test_idempotency_caching_returns_duplicate_result():
    async def _run():
        mgr = IdempotencyManager()
        user_id = "user_idempotent_1"
        key = "idem_key_999"
        payload = {"execution_id": "exec_1", "status": "executed", "data": "test"}

        await mgr.save_record(user_id, key, payload)

        cached = await mgr.get_record(user_id, key)
        assert cached == payload
        assert cached["execution_id"] == "exec_1"

    asyncio.run(_run())


def test_tool_execution_timeout_raises_504():
    async def slow_handler(inputs: SearchDocumentInput):
        await asyncio.sleep(2.0)
        return {"status": "executed"}

    slow_tool = ToolDefinition(
        name="slow_tool",
        description="Slow mock tool",
        required_intent=IntentEnum.SEARCH_DOCUMENT,
        minimum_risk=RiskEnum.LOW,
        requires_approval=False,
        input_schema=SearchDocumentInput,
        handler=slow_handler,
    )

    policy = PolicyDecision(
        intent=IntentEnum.SEARCH_DOCUMENT,
        resource="doc1",
        ai_risk=RiskEnum.LOW,
        policy_risk=RiskEnum.LOW,
        requires_approval=False,
        decision=DecisionEnum.ALLOW,
    )

    async def run_test():
        with patch("app.tools.registry.ToolRegistry.get_tool_for_intent", return_value=slow_tool):
            with patch("app.config.settings.EXECUTION_TIMEOUT_SECONDS", 0.1):
                await ExecutionDispatcher.execute_tool(
                    request_id="req_slow",
                    user_id="user1",
                    policy_decision=policy,
                    tool_input={"query": "test search"},
                )

    with pytest.raises(Exception) as exc:
        asyncio.run(run_test())

    assert exc.value.status_code == 504
    assert "Tool execution timed out" in exc.value.detail
