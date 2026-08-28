from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=128, description="Name of the AI Agent")
    provider: str = Field(..., min_length=2, max_length=64, description="Provider identifier (openai, anthropic, gemini, groq, custom, etc.)")
    framework: Optional[str] = Field(None, max_length=64, description="Framework identifier (langchain, langgraph, crewai, autogen, custom, etc.)")
    description: Optional[str] = Field(None, max_length=1000, description="Detailed agent description")
    endpoint_url: Optional[str] = Field(None, max_length=512, description="Target REST/HTTP endpoint for remote custom agents")
    allowed_tools: List[str] = Field(default_factory=list, description="List of tool names authorized for this agent")
    risk_level: str = Field("LOW", description="Baseline risk level (LOW, MEDIUM, HIGH, CRITICAL)")


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=128)
    provider: Optional[str] = Field(None, min_length=2, max_length=64)
    framework: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = Field(None, max_length=1000)
    endpoint_url: Optional[str] = Field(None, max_length=512)
    allowed_tools: Optional[List[str]] = None
    enabled: Optional[bool] = None
    risk_level: Optional[str] = None


class AgentResponse(BaseModel):
    agent_id: str
    tenant_id: str
    name: str
    provider: str
    framework: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    enabled: bool
    risk_level: str
    allowed_tools: List[str]
    created_at: datetime
    updated_at: datetime


class AgentListResponse(BaseModel):
    agents: List[AgentResponse]
    total: int
