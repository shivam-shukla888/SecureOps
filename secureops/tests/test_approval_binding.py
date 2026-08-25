import asyncio
import pytest
from app.schemas.decision import IntentEnum, RiskEnum, PolicyDecision, DecisionEnum
from app.tools.registry import ToolRegistry
from app.tools.permissions import ToolPermissionEngine
from app.approval.repository import in_memory_approval_repo


def test_delete_data_without_approval_rejected():
    tool_def = ToolRegistry.get_tool_for_intent(IntentEnum.DELETE_DATA)
    policy = PolicyDecision(
        intent=IntentEnum.DELETE_DATA,
        resource="db_prod",
        ai_risk=RiskEnum.HIGH,
        policy_risk=RiskEnum.HIGH,
        requires_approval=True,
        decision=DecisionEnum.REQUIRE_APPROVAL,
    )

    with pytest.raises(Exception) as exc:
        ToolPermissionEngine.validate_tool_execution_permission(
            tool_def=tool_def,
            policy_decision=policy,
            approval_ticket=None,
        )
    assert exc.value.status_code == 403
    assert "requires a valid approved ticket ID" in exc.value.detail


def test_approval_resource_binding_mismatch_rejected():
    tool_def = ToolRegistry.get_tool_for_intent(IntentEnum.DELETE_DATA)
    policy = PolicyDecision(
        intent=IntentEnum.DELETE_DATA,
        resource="resource_B",
        ai_risk=RiskEnum.HIGH,
        policy_risk=RiskEnum.HIGH,
        requires_approval=True,
        decision=DecisionEnum.REQUIRE_APPROVAL,
    )

    # Ticket approved for resource_A
    ticket = asyncio.run(
        in_memory_approval_repo.create_ticket(
            approval_id="appr_binding_1",
            request_id="req_binding_1",
            requester_id="user_alice",
            intent="DELETE_DATA",
            resource="resource_A",
            policy_risk="HIGH",
        )
    )
    ticket.status = "APPROVED"

    with pytest.raises(Exception) as exc:
        ToolPermissionEngine.validate_tool_execution_permission(
            tool_def=tool_def,
            policy_decision=policy,
            approval_ticket=ticket,
            user_id="user_alice",
            request_id="req_binding_1",
            target_resource="resource_B",
        )
    assert exc.value.status_code == 403
    assert "Ticket was approved for resource 'resource_A', not 'resource_B'" in exc.value.detail


def test_approval_request_id_binding_mismatch_rejected():
    tool_def = ToolRegistry.get_tool_for_intent(IntentEnum.DELETE_DATA)
    policy = PolicyDecision(
        intent=IntentEnum.DELETE_DATA,
        resource="resource_A",
        ai_risk=RiskEnum.HIGH,
        policy_risk=RiskEnum.HIGH,
        requires_approval=True,
        decision=DecisionEnum.REQUIRE_APPROVAL,
    )

    ticket = asyncio.run(
        in_memory_approval_repo.create_ticket(
            approval_id="appr_binding_2",
            request_id="req_original",
            requester_id="user_alice",
            intent="DELETE_DATA",
            resource="resource_A",
            policy_risk="HIGH",
        )
    )
    ticket.status = "APPROVED"

    with pytest.raises(Exception) as exc:
        ToolPermissionEngine.validate_tool_execution_permission(
            tool_def=tool_def,
            policy_decision=policy,
            approval_ticket=ticket,
            user_id="user_alice",
            request_id="req_unauthorized_different",
            target_resource="resource_A",
        )
    assert exc.value.status_code == 403
    assert "issued for request 'req_original', not 'req_unauthorized_different'" in exc.value.detail
