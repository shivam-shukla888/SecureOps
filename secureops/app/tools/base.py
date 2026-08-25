from dataclasses import dataclass
from typing import Type, Callable, Any
from pydantic import BaseModel
from app.schemas.decision import IntentEnum, RiskEnum


@dataclass
class ToolDefinition:
    name: str
    description: str
    required_intent: IntentEnum
    minimum_risk: RiskEnum
    requires_approval: bool
    input_schema: Type[BaseModel]
    handler: Callable[..., Any]
