import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone, timedelta
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.approval.repository import in_memory_approval_repo


def test_valid_approval_workflow(client, auth_headers):
    mock_res = ClassifierResult(
        intent=IntentEnum.DELETE_DATA,
        resource="test_table",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_res, True, "gemini", False)

        resp = client.post(
            "/v1/requests",
            json={"user_id": "requester_alice", "request": "Delete test_table"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "REQUIRE_APPROVAL"
        approval_id = data["approval_id"]
        assert approval_id is not None

        approve_resp = client.post(
            f"/v1/approvals/{approval_id}/approve",
            json={"approver_id": "security_officer_bob"},
            headers=auth_headers,
        )
        assert approve_resp.status_code == 200
        approve_data = approve_resp.json()
        assert approve_data["decision"] == "APPROVED"
        assert approve_data["approver_id"] == "security_officer_bob"


def test_self_approval_prevention_returns_403(client, auth_headers):
    mock_res = ClassifierResult(
        intent=IntentEnum.DELETE_DATA,
        resource="test_table",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_res, True, "gemini", False)

        resp = client.post(
            "/v1/requests",
            json={"user_id": "requester_alice", "request": "Delete test_table"},
            headers=auth_headers,
        )
        approval_id = resp.json()["approval_id"]

        approve_resp = client.post(
            f"/v1/approvals/{approval_id}/approve",
            json={"approver_id": "requester_alice"},
            headers=auth_headers,
        )
        assert approve_resp.status_code == 403
        assert "requester cannot self-approve" in approve_resp.json()["error"]["message"].lower()


def test_double_approval_returns_400(client, auth_headers):
    mock_res = ClassifierResult(
        intent=IntentEnum.UPDATE_DATA,
        resource="users/12",
        risk=RiskEnum.MEDIUM,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_res, True, "gemini", False)

        resp = client.post(
            "/v1/requests",
            json={"user_id": "requester_alice", "request": "Update user 12"},
            headers=auth_headers,
        )
        approval_id = resp.json()["approval_id"]

        client.post(
            f"/v1/approvals/{approval_id}/approve",
            json={"approver_id": "security_officer_bob"},
            headers=auth_headers,
        )

        approve_2 = client.post(
            f"/v1/approvals/{approval_id}/approve",
            json={"approver_id": "security_officer_charlie"},
            headers=auth_headers,
        )
        assert approve_2.status_code == 400
        assert "already been approved" in approve_2.json()["error"]["message"]


def test_reject_then_approve_returns_400(client, auth_headers):
    mock_res = ClassifierResult(
        intent=IntentEnum.SEND_DOCUMENT,
        resource="secret.pdf",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_res, True, "gemini", False)

        resp = client.post(
            "/v1/requests",
            json={"user_id": "requester_alice", "request": "Send secret.pdf"},
            headers=auth_headers,
        )
        approval_id = resp.json()["approval_id"]

        client.post(
            f"/v1/approvals/{approval_id}/reject",
            json={"approver_id": "security_officer_bob"},
            headers=auth_headers,
        )

        approve_resp = client.post(
            f"/v1/approvals/{approval_id}/approve",
            json={"approver_id": "security_officer_charlie"},
            headers=auth_headers,
        )
        assert approve_resp.status_code == 400
        assert "was rejected and cannot be reused" in approve_resp.json()["error"]["message"]


def test_expired_approval_returns_400(client, auth_headers):
    mock_res = ClassifierResult(
        intent=IntentEnum.UPDATE_DATA,
        resource="config",
        risk=RiskEnum.MEDIUM,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_res, True, "gemini", False)

        resp = client.post(
            "/v1/requests",
            json={"user_id": "requester_alice", "request": "Update config"},
            headers=auth_headers,
        )
        approval_id = resp.json()["approval_id"]

        # Manually expire ticket in repository
        ticket = asyncio.run(in_memory_approval_repo.get_ticket(approval_id))
        ticket.expires_at = datetime.now(timezone.utc) - timedelta(minutes=10)

        approve_resp = client.post(
            f"/v1/approvals/{approval_id}/approve",
            json={"approver_id": "security_officer_bob"},
            headers=auth_headers,
        )
        assert approve_resp.status_code == 400
        assert "expired" in approve_resp.json()["error"]["message"]


def test_unauthorized_approval_returns_401(client):
    response = client.post(
        "/v1/approvals/appr_12345/approve",
        json={"approver_id": "bob"},
    )
    assert response.status_code == 401
