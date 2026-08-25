import pytest
from unittest.mock import AsyncMock, patch
from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum, DecisionEnum


def test_api_search_document_allow(client, auth_headers):
    mock_result = ClassifierResult(
        intent=IntentEnum.SEARCH_DOCUMENT,
        resource="doc123",
        risk=RiskEnum.LOW,
        requires_approval=False,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_result, True, "gemini", False)

        response = client.post(
            "/v1/requests",
            json={"user_id": "user1", "request": "Find annual report doc123"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "SEARCH_DOCUMENT"
        assert data["decision"] == "ALLOW"
        assert data["policy_risk"] == "LOW"
        assert data["requires_approval"] is False
        assert data["provider_used"] == "gemini"
        assert data["fallback_used"] is False
        assert data["execution_result"]["status"] == "executed"


def test_api_read_data_allow(client, auth_headers):
    mock_result = ClassifierResult(
        intent=IntentEnum.READ_DATA,
        resource="users_table",
        risk=RiskEnum.LOW,
        requires_approval=False,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_result, True, "gemini", False)

        response = client.post(
            "/v1/requests",
            json={"user_id": "user1", "request": "Read user profiles"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "READ_DATA"
        assert data["decision"] == "ALLOW"


def test_api_update_data_require_approval(client, auth_headers):
    mock_result = ClassifierResult(
        intent=IntentEnum.UPDATE_DATA,
        resource="users_table/456",
        risk=RiskEnum.MEDIUM,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_result, True, "gemini", False)

        response = client.post(
            "/v1/requests",
            json={"user_id": "user1", "request": "Update user 456 email"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "UPDATE_DATA"
        assert data["decision"] == "REQUIRE_APPROVAL"
        assert data["execution_result"]["status"] == "pending_approval"


def test_api_delete_data_require_approval(client, auth_headers):
    mock_result = ClassifierResult(
        intent=IntentEnum.DELETE_DATA,
        resource="prod_db",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_result, True, "gemini", False)

        response = client.post(
            "/v1/requests",
            json={"user_id": "user1", "request": "Delete prod_db"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "DELETE_DATA"
        assert data["decision"] == "REQUIRE_APPROVAL"


def test_api_unknown_intent_block(client, auth_headers):
    mock_result = ClassifierResult(
        intent=IntentEnum.UNKNOWN,
        resource="unknown",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (mock_result, True, "gemini", False)

        response = client.post(
            "/v1/requests",
            json={"user_id": "user1", "request": "bla bla random text"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "UNKNOWN"
        assert data["decision"] == "BLOCK"
        assert data["execution_result"]["status"] == "blocked"


def test_api_llm_downgrade_attempt_overridden(client, auth_headers):
    downgraded_result = ClassifierResult(
        intent=IntentEnum.DELETE_DATA,
        resource="critical_db",
        risk=RiskEnum.LOW,
        requires_approval=False,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (downgraded_result, True, "gemini", False)

        response = client.post(
            "/v1/requests",
            json={"user_id": "user1", "request": "Delete critical_db completely"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "DELETE_DATA"
        assert data["policy_risk"] == "HIGH"
        assert data["requires_approval"] is True
        assert data["decision"] == "REQUIRE_APPROVAL"
        assert data["override_applied"] is True


def test_api_ai_failure_fails_closed(client, auth_headers):
    fail_closed_result = ClassifierResult(
        intent=IntentEnum.UNKNOWN,
        resource="unknown",
        risk=RiskEnum.HIGH,
        requires_approval=True,
    )
    with patch("app.ai.classifier.RequestClassifier.classify", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = (fail_closed_result, False, "none", True)

        response = client.post(
            "/v1/requests",
            json={"user_id": "user1", "request": "Any prompt when AI is down"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "UNKNOWN"
        assert data["decision"] == "BLOCK"
        assert data["policy_risk"] == "HIGH"
        assert data["provider_used"] == "none"
        assert data["fallback_used"] is True
