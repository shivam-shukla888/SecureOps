import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from app.adapters.http_adapter import GenericHTTPAgentAdapter
from app.adapters.base import AgentExecutionRequest


def test_company_agent_ssrf_and_redirect_protections():
    """
    [MOCKED TEST] Proves GenericHTTPAgentAdapter blocks cloud metadata, local IP ranges, and unsafe schemes.
    """
    # 1. Attempting 169.254.169.254 cloud metadata must raise HTTP 400
    with pytest.raises(HTTPException) as exc_169:
        GenericHTTPAgentAdapter(endpoint_url="http://169.254.169.254/agent")
    assert exc_169.value.status_code == 400
    assert "Security Violation" in exc_169.value.detail

    # 2. Attempting 127.0.0.1 loopback must raise HTTP 400
    with pytest.raises(HTTPException) as exc_local:
        GenericHTTPAgentAdapter(endpoint_url="http://127.0.0.1:8080/agent")
    assert exc_local.value.status_code == 400
    assert "Security Violation" in exc_local.value.detail


def test_company_agent_execution_sanitization():
    """
    [MOCKED TEST] Validates that company agent error outputs sanitize tokens and secrets.
    """
    adapter = GenericHTTPAgentAdapter(endpoint_url="https://api.internal-doc-service.com/agent")
    req = AgentExecutionRequest(
        agent_id="company_agent_001",
        tenant_id="tenant_default",
        user_id="company_user",
        prompt="Hello internal agent with secret secops_live_super_secret_key_12345",
    )

    mock_http_res = MagicMock()
    mock_http_res.status_code = 500
    mock_http_res.content = b"Internal Error containing secops_live_super_secret_key_12345"
    mock_http_res.text = "Internal Error containing secops_live_super_secret_key_12345"

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_http_res
        res = asyncio.run(adapter.execute(req))

        assert res.agent_id == "company_agent_001"
        # Ensure raw secret key in response body is redacted
        assert "secops_live_super_secret_key_12345" not in res.output_text
        assert "[REDACTED_SECRET]" in res.output_text
