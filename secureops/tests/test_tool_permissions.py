import pytest
from app.schemas.decision import IntentEnum, RiskEnum, PolicyDecision, DecisionEnum
from app.tools.registry import ToolRegistry
from app.tools.permissions import ToolPermissionEngine


def test_unauthorized_execution_endpoint_returns_401(client):
    payload = {
        "request_id": "req_123",
        "user_id": "user1",
        "tool_input": {"intent": "SEARCH_DOCUMENT", "query": "test"},
    }
    response = client.post("/v1/executions", json=payload)
    assert response.status_code == 401


def test_unknown_intent_tool_lookup_returns_none():
    tool = ToolRegistry.get_tool_for_intent(IntentEnum.UNKNOWN)
    assert tool is None


def test_tool_permission_engine_blocks_policy_block():
    tool_def = ToolRegistry.get_tool_for_intent(IntentEnum.SEARCH_DOCUMENT)
    blocked_policy = PolicyDecision(
        intent=IntentEnum.SEARCH_DOCUMENT,
        resource="doc1",
        ai_risk=RiskEnum.HIGH,
        policy_risk=RiskEnum.HIGH,
        requires_approval=False,
        decision=DecisionEnum.BLOCK,
        reason="Security block override",
    )

    with pytest.raises(Exception) as exc_info:
        ToolPermissionEngine.validate_tool_execution_permission(
            tool_def=tool_def,
            policy_decision=blocked_policy,
        )
    assert exc_info.value.status_code == 403
    assert "Operation rejected by security policy" in exc_info.value.detail


def test_tool_permission_engine_rejects_intent_mismatch():
    tool_def = ToolRegistry.get_tool_for_intent(IntentEnum.SEARCH_DOCUMENT)
    mismatched_policy = PolicyDecision(
        intent=IntentEnum.DELETE_DATA,
        resource="db1",
        ai_risk=RiskEnum.HIGH,
        policy_risk=RiskEnum.HIGH,
        requires_approval=True,
        decision=DecisionEnum.REQUIRE_APPROVAL,
    )

    with pytest.raises(Exception) as exc_info:
        ToolPermissionEngine.validate_tool_execution_permission(
            tool_def=tool_def,
            policy_decision=mismatched_policy,
        )
    assert exc_info.value.status_code == 403
    assert "Permission denied: Tool 'search_document' requires intent" in exc_info.value.detail
