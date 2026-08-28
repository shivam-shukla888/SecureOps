import logging
import httpx
from typing import Any, Dict, List
from fastapi import HTTPException, status

from app.adapters.base import (
    BaseAgentAdapter,
    AgentExecutionRequest,
    AgentExecutionResponse,
    NormalizedToolCall,
)
from app.security.network import validate_destination_url

logger = logging.getLogger(__name__)


from app.config import settings
from app.security.secrets import redact_secrets

MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB


class GenericHTTPAgentAdapter(BaseAgentAdapter):
    def __init__(self, endpoint_url: str, timeout_seconds: float = 10.0):
        self.endpoint_url = endpoint_url
        self.timeout_seconds = timeout_seconds

        # Enforce HTTPS in production environment
        if getattr(settings, "ENVIRONMENT", "development") == "production":
            if not endpoint_url.lower().startswith("https://"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security Policy Violation: Agent endpoints must use HTTPS in production."
                )

        # SSRF validation on target endpoint
        is_safe, error_msg = validate_destination_url(endpoint_url)
        if not is_safe:
            logger.error(f"Unsafe destination URL for HTTP Agent Adapter: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Security Violation: Agent endpoint URL rejected ({error_msg})"
            )

    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        logger.info(f"Executing remote HTTP agent at '{self.endpoint_url}' for agent '{request.agent_id}'")
        payload = request.model_dump()
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
                response = await client.post(self.endpoint_url, json=payload)
                
                # Check response payload size limit
                if len(response.content) > MAX_RESPONSE_BYTES:
                    logger.warning(f"Remote agent response exceeded maximum allowed payload size ({len(response.content)} bytes)")
                    return AgentExecutionResponse(
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                        output_text="Error: Remote agent response exceeded size limit.",
                        metadata={"error": "payload_too_large"},
                    )

                if response.status_code != 200:
                    sanitized_body = redact_secrets(response.text[:200])
                    logger.warning(f"Remote agent HTTP status {response.status_code}: {sanitized_body}")
                    return AgentExecutionResponse(
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                        output_text=f"Remote agent error (HTTP {response.status_code}): {sanitized_body}",
                        metadata={"http_status": response.status_code},
                    )
                
                data = response.json()
                output_text = self.normalize_response(data)
                tool_calls = self.normalize_tool_calls(data.get("tool_calls", []))
                
                return AgentExecutionResponse(
                    agent_id=request.agent_id,
                    tenant_id=request.tenant_id,
                    output_text=output_text,
                    tool_calls=tool_calls,
                    raw_response=data if isinstance(data, dict) else {"output": data},
                    metadata={"provider": "custom_http"},
                )
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to remote HTTP agent at '{self.endpoint_url}'")
            return AgentExecutionResponse(
                agent_id=request.agent_id,
                tenant_id=request.tenant_id,
                output_text="Error: Remote agent execution timed out.",
                metadata={"error": "timeout"},
            )
        except Exception as exc:
            sanitized_msg = redact_secrets(str(exc))
            logger.error(f"Error executing remote HTTP agent: {sanitized_msg}")
            return AgentExecutionResponse(
                agent_id=request.agent_id,
                tenant_id=request.tenant_id,
                output_text=f"Error executing agent endpoint: {sanitized_msg}",
                metadata={"error": "connection_error"},
            )


    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(self.endpoint_url)
                return response.status_code in (200, 404, 405)
        except Exception:
            return False

    def normalize_response(self, raw_output: Any) -> str:
        if isinstance(raw_output, str):
            return raw_output
        if isinstance(raw_output, dict):
            return raw_output.get("output_text") or raw_output.get("message") or raw_output.get("output") or str(raw_output)
        return str(raw_output)

    def normalize_tool_calls(self, raw_tool_calls: Any) -> List[NormalizedToolCall]:
        normalized = []
        if not isinstance(raw_tool_calls, list):
            return normalized

        for tc in raw_tool_calls:
            if isinstance(tc, dict):
                tool_name = tc.get("tool_name") or tc.get("name") or tc.get("function", {}).get("name")
                args = tc.get("arguments") or tc.get("args") or tc.get("function", {}).get("arguments") or {}
                if isinstance(args, str):
                    import json
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {"raw": args}
                if tool_name:
                    normalized.append(NormalizedToolCall(
                        tool_name=tool_name,
                        arguments=args if isinstance(args, dict) else {"arg": args},
                        call_id=tc.get("call_id") or tc.get("id"),
                    ))
        return normalized
