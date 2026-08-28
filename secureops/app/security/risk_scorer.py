import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class RiskScoringEngine:
    def calculate_risk(
        self,
        ai_classifier_score: float = 0.0,
        is_prompt_injection: bool = False,
        tool_decision: str = "ALLOW",
        tool_risk_contrib: float = 0.0,
        is_cross_tenant_attempt: bool = False,
        is_cross_user_attempt: bool = False,
        has_dangerous_args: bool = False,
    ) -> Tuple[float, str]:
        """
        Computes deterministic risk score [0.0 - 1.0] and risk level.
        """
        score = max(0.0, ai_classifier_score)

        if is_prompt_injection:
            score += 0.5
        if is_cross_tenant_attempt:
            score += 0.6
        if is_cross_user_attempt:
            score += 0.4
        if has_dangerous_args:
            score += 0.5
        if tool_decision == "REQUIRE_APPROVAL":
            score += 0.3
        elif tool_decision == "BLOCK":
            score += 0.6

        score += tool_risk_contrib
        score = min(1.0, max(0.0, score))

        if score >= 0.9:
            level = "CRITICAL"
        elif score >= 0.6:
            level = "HIGH"
        elif score >= 0.3:
            level = "MEDIUM"
        else:
            level = "LOW"

        return round(score, 2), level


risk_scoring_engine = RiskScoringEngine()
