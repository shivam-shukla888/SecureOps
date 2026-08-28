import logging
from typing import Any, Dict, List
from app.adapters.base import (
    BaseAgentAdapter,
    AgentExecutionRequest,
    AgentExecutionResponse,
    NormalizedToolCall,
)

logger = logging.getLogger(__name__)


class SimulatedAgentAdapter(BaseAgentAdapter):
    def __init__(self, agent_name: str = "SimulatedAgent"):
        self.agent_name = agent_name

    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        logger.info(f"Simulating agent execution for agent '{request.agent_id}' (prompt: '{request.prompt[:50]}...')")
        
        prompt_lower = request.prompt.lower()
        tool_calls: List[NormalizedToolCall] = []
        output_text = f"[{self.agent_name}] Processed request: '{request.prompt}'"

        # Check for simulated tool invocation requests embedded in test prompt parameters
        if "simulated_tool" in request.parameters:
            tool_info = request.parameters["simulated_tool"]
            if isinstance(tool_info, dict):
                tool_calls.append(NormalizedToolCall(
                    tool_name=tool_info.get("name", "knowledge_search"),
                    arguments=tool_info.get("arguments", {}),
                    call_id=tool_info.get("call_id", "sim_call_001")
                ))

        # Check if prompt triggers simulated adversarial responses or tool requests
        if "delete_data" in prompt_lower or "drop table" in prompt_lower:
            tool_calls.append(NormalizedToolCall(
                tool_name="delete_data",
                arguments={"table": "customers", "confirm": True},
                call_id="call_del_001"
            ))
            output_text = "Attempting to delete data as requested."
        elif "read_data" in prompt_lower or "export_all_users" in prompt_lower:
            tool_calls.append(NormalizedToolCall(
                tool_name="read_data",
                arguments={"resource": "user_records"},
                call_id="call_read_001"
            ))
        elif "curl" in prompt_lower or "http://" in prompt_lower:
            tool_calls.append(NormalizedToolCall(
                tool_name="http_request",
                arguments={"url": "http://169.254.169.254/latest/meta-data/"},
                call_id="call_ssrf_001"
            ))

        return AgentExecutionResponse(
            agent_id=request.agent_id,
            tenant_id=request.tenant_id,
            output_text=output_text,
            tool_calls=tool_calls,
            raw_response={"simulated": True, "prompt": request.prompt},
            metadata={"adapter": "simulated", "agent_name": self.agent_name},
        )

    async def health_check(self) -> bool:
        return True

    def normalize_response(self, raw_output: Any) -> str:
        return str(raw_output)

    def normalize_tool_calls(self, raw_tool_calls: Any) -> List[NormalizedToolCall]:
        if isinstance(raw_tool_calls, list):
            return [tc for tc in raw_tool_calls if isinstance(tc, NormalizedToolCall)]
        return []
