import json
import logging
import os
import httpx
from typing import Any, Dict, List, Optional
from app.adapters.base import (
    BaseAgentAdapter,
    AgentExecutionRequest,
    AgentExecutionResponse,
    NormalizedToolCall,
)
from app.security.secrets import secret_provider, redact_secrets

logger = logging.getLogger(__name__)


class OpenAICompatibleAgentAdapter(BaseAgentAdapter):
    def __init__(
        self,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        api_credential_name: str = "OPENAI_API_KEY",
        timeout_seconds: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_credential_name = api_credential_name
        self.timeout_seconds = timeout_seconds

    def _get_api_key(self) -> Optional[str]:
        try:
            val = secret_provider.get_secret(self.api_credential_name)
            if val:
                return val
        except Exception:
            pass
        return os.environ.get(self.api_credential_name)

    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        logger.info(f"Executing OpenAI-compatible agent adapter for agent '{request.agent_id}' (model: '{self.model}')")
        
        api_key = self._get_api_key()

        # Safe MOCKED fallback for testing when no live external key is configured in environment
        if not api_key and "openai.com" in self.base_url:
            logger.info(f"No OPENAI_API_KEY present; operating in MOCKED evaluation mode for agent '{request.agent_id}'")
            tool_calls = []
            if "simulated_tool" in request.parameters:
                st = request.parameters["simulated_tool"]
                if isinstance(st, dict):
                    tool_calls.append(NormalizedToolCall(
                        tool_name=st.get("name", "knowledge_search"),
                        arguments=st.get("arguments", {}),
                        call_id=st.get("call_id", "sim_call_001")
                    ))
            return AgentExecutionResponse(
                agent_id=request.agent_id,
                tenant_id=request.tenant_id,
                output_text=f"[Mocked OpenAI Agent ({self.model})] Response for prompt: '{request.prompt[:60]}...'",
                tool_calls=tool_calls,
                metadata={"provider": "openai_compatible", "mode": "MOCKED", "model": self.model},
            )

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        endpoint = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": request.prompt}
            ],
            "temperature": 0.0,
        }

        # Check for simulated tool invocation requests in request parameters
        if "simulated_tool" in request.parameters:
            payload["tools"] = [{
                "type": "function",
                "function": {
                    "name": request.parameters["simulated_tool"].get("name", "knowledge_search"),
                    "arguments": json.dumps(request.parameters["simulated_tool"].get("arguments", {}))
                }
            }]

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
                response = await client.post(endpoint, json=payload, headers=headers)
                
                if response.status_code != 200:
                    sanitized_err = redact_secrets(response.text[:200])
                    logger.warning(f"OpenAI endpoint returned status {response.status_code}: {sanitized_err}")
                    return AgentExecutionResponse(
                        agent_id=request.agent_id,
                        tenant_id=request.tenant_id,
                        output_text=f"Provider Error (HTTP {response.status_code}): {sanitized_err}",
                        metadata={"http_status": response.status_code, "provider": "openai_compatible"},
                    )

                data = response.json()
                output_text = self.normalize_response(data)
                
                # Extract choices[0].message.tool_calls
                choices = data.get("choices", [])
                raw_tool_calls = []
                if choices and isinstance(choices, list) and len(choices) > 0:
                    message = choices[0].get("message", {})
                    raw_tool_calls = message.get("tool_calls", [])

                tool_calls = self.normalize_tool_calls(raw_tool_calls)

                return AgentExecutionResponse(
                    agent_id=request.agent_id,
                    tenant_id=request.tenant_id,
                    output_text=output_text,
                    tool_calls=tool_calls,
                    raw_response={"model": self.model, "output_preview": output_text[:100]},
                    metadata={"provider": "openai_compatible", "model": self.model},
                )
        except httpx.TimeoutException:
            logger.error(f"Timeout connecting to OpenAI endpoint '{endpoint}'")
            return AgentExecutionResponse(
                agent_id=request.agent_id,
                tenant_id=request.tenant_id,
                output_text="Error: OpenAI-compatible provider request timed out.",
                metadata={"error": "timeout"},
            )
        except Exception as exc:
            sanitized_msg = redact_secrets(str(exc))
            logger.error(f"Error executing OpenAI-compatible agent adapter: {sanitized_msg}")
            return AgentExecutionResponse(
                agent_id=request.agent_id,
                tenant_id=request.tenant_id,
                output_text=f"Error executing OpenAI-compatible agent: {sanitized_msg}",
                metadata={"error": "provider_error"},
            )

    async def health_check(self) -> bool:
        return True

    def normalize_response(self, raw_output: Any) -> str:
        if isinstance(raw_output, dict):
            choices = raw_output.get("choices", [])
            if choices and isinstance(choices, list) and len(choices) > 0:
                msg = choices[0].get("message", {})
                content = msg.get("content")
                if content:
                    return str(content)
        return str(raw_output)

    def normalize_tool_calls(self, raw_tool_calls: Any) -> List[NormalizedToolCall]:
        normalized = []
        if not isinstance(raw_tool_calls, list):
            return normalized

        for tc in raw_tool_calls:
            if isinstance(tc, dict):
                func = tc.get("function", {})
                tool_name = func.get("name") or tc.get("name") or tc.get("tool_name")
                args_raw = func.get("arguments") or tc.get("arguments") or {}

                if isinstance(args_raw, str):
                    try:
                        args = json.loads(args_raw)
                    except Exception:
                        args = {"raw": args_raw}
                elif isinstance(args_raw, dict):
                    args = args_raw
                else:
                    args = {"arg": str(args_raw)}

                if tool_name:
                    normalized.append(NormalizedToolCall(
                        tool_name=tool_name,
                        arguments=args,
                        call_id=tc.get("id") or tc.get("call_id"),
                    ))
        return normalized
