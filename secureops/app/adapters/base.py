from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NormalizedToolCall(BaseModel):
    tool_name: str = Field(..., description="Name of the requested tool")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments supplied for tool execution")
    call_id: Optional[str] = Field(None, description="Unique tool call identifier")


class AgentExecutionRequest(BaseModel):
    agent_id: str
    tenant_id: str
    user_id: str
    prompt: str
    session_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class AgentExecutionResponse(BaseModel):
    agent_id: str
    tenant_id: str
    output_text: str
    tool_calls: List[NormalizedToolCall] = Field(default_factory=list)
    raw_response: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgentAdapter(ABC):
    @abstractmethod
    async def execute(self, request: AgentExecutionRequest) -> AgentExecutionResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

    @abstractmethod
    def normalize_response(self, raw_output: Any) -> str:
        pass

    @abstractmethod
    def normalize_tool_calls(self, raw_tool_calls: Any) -> List[NormalizedToolCall]:
        pass
