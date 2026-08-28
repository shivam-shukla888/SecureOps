from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SecurityTestCase(BaseModel):
    test_id: str = Field(..., description="Unique test case identifier (e.g. PI-001)")
    category: str = Field(..., description="Attack category")
    name: str = Field(..., description="Short descriptive test name")
    description: str = Field(..., description="Detailed test scenario explanation")
    severity: str = Field("HIGH", description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    attack_input: str = Field(..., description="Adversarial input prompt or payload")
    expected_behavior: str = Field("BLOCK", description="Expected security policy outcome (BLOCK, REQUIRE_APPROVAL, ALLOW)")
    required_policy: Optional[str] = Field(None, description="Policy rule required to trigger expected behavior")
    simulated_tool: Optional[Dict[str, Any]] = Field(None, description="Optional simulated tool request parameters")
    enabled: bool = Field(True, description="Whether test case is active")
