import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.adapters.base import AgentExecutionRequest
from app.adapters.openai_adapter import OpenAICompatibleAgentAdapter


def test_openai_compatible_adapter_mocked_execution():
    """
    [MOCKED TEST] Validates OpenAICompatibleAgentAdapter normalization against a mocked OpenAI endpoint.
    No live external request is made.
    """
    adapter = OpenAICompatibleAgentAdapter(
        base_url="https://mock.openai.internal/v1",
        model="gpt-4o-mini",
        api_credential_name="OPENAI_API_KEY",
    )

    mock_response_data = {
        "id": "chatcmpl-mock123",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Mocked response from OpenAI-compatible provider.",
                    "tool_calls": [
                        {
                            "id": "call_999",
                            "type": "function",
                            "function": {
                                "name": "read_data",
                                "arguments": "{\"resource\": \"user_table\"}"
                            }
                        }
                    ]
                },
                "finish_reason": "tool_calls"
            }
        ]
    }

    req = AgentExecutionRequest(
        agent_id="agent_openai_mock",
        tenant_id="tenant_default",
        user_id="test_user",
        prompt="Please read user table data",
    )

    mock_http_res = MagicMock()
    mock_http_res.status_code = 200
    mock_http_res.json.return_value = mock_response_data
    mock_http_res.text = str(mock_response_data)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_http_res

        res = asyncio.run(adapter.execute(req))

        assert res.agent_id == "agent_openai_mock"
        assert "Mocked response" in res.output_text
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0].tool_name == "read_data"
        assert res.tool_calls[0].arguments == {"resource": "user_table"}
        assert res.metadata["provider"] == "openai_compatible"
