from app.schemas.decision import (
    ClassifierResult,
    PolicyDecision,
    IntentEnum,
    RiskEnum,
    DecisionEnum,
)

RISK_WEIGHTS = {
    RiskEnum.LOW: 1,
    RiskEnum.MEDIUM: 2,
    RiskEnum.HIGH: 3,
}

CANONICAL_POLICY_MATRIX = {
    IntentEnum.SEARCH_DOCUMENT: {
        "min_risk": RiskEnum.LOW,
        "requires_approval": False,
        "default_decision": DecisionEnum.ALLOW,
    },
    IntentEnum.READ_DATA: {
        "min_risk": RiskEnum.LOW,
        "requires_approval": False,
        "default_decision": DecisionEnum.ALLOW,
    },
    IntentEnum.UPDATE_DATA: {
        "min_risk": RiskEnum.MEDIUM,
        "requires_approval": True,
        "default_decision": DecisionEnum.REQUIRE_APPROVAL,
    },
    IntentEnum.SEND_DOCUMENT: {
        "min_risk": RiskEnum.HIGH,
        "requires_approval": True,
        "default_decision": DecisionEnum.REQUIRE_APPROVAL,
    },
    IntentEnum.DELETE_DATA: {
        "min_risk": RiskEnum.HIGH,
        "requires_approval": True,
        "default_decision": DecisionEnum.REQUIRE_APPROVAL,
    },
    IntentEnum.UNKNOWN: {
        "min_risk": RiskEnum.HIGH,
        "requires_approval": True,
        "default_decision": DecisionEnum.BLOCK,
    },
}


class DeterministicPolicyEngine:
    @staticmethod
    def evaluate(ai_result: ClassifierResult) -> PolicyDecision:
        intent = ai_result.intent
        rule = CANONICAL_POLICY_MATRIX.get(
            intent, CANONICAL_POLICY_MATRIX[IntentEnum.UNKNOWN]
        )

        canonical_min_risk = rule["min_risk"]
        canonical_req_approval = rule["requires_approval"]

        # Anti-Downgrade Rule:
        # Policy risk cannot fall below the canonical minimum risk for the intent.
        ai_risk_weight = RISK_WEIGHTS.get(ai_result.risk, 3)
        canonical_min_risk_weight = RISK_WEIGHTS[canonical_min_risk]

        override_applied = False
        reasons = []

        if ai_risk_weight < canonical_min_risk_weight:
            final_risk = canonical_min_risk
            override_applied = True
            reasons.append(
                f"Risk upgraded from {ai_result.risk.value} to canonical minimum {canonical_min_risk.value} for {intent.value}."
            )
        else:
            final_risk = ai_result.risk

        if canonical_req_approval and not ai_result.requires_approval:
            final_requires_approval = True
            override_applied = True
            reasons.append(
                f"Approval requirement overridden to TRUE (canonical rule for {intent.value})."
            )
        else:
            final_requires_approval = ai_result.requires_approval or canonical_req_approval

        # Determine Final Decision
        if intent == IntentEnum.UNKNOWN:
            final_decision = DecisionEnum.BLOCK
        elif final_risk == RiskEnum.HIGH or final_requires_approval:
            final_decision = DecisionEnum.REQUIRE_APPROVAL
        elif final_risk == RiskEnum.MEDIUM:
            final_decision = DecisionEnum.REQUIRE_APPROVAL
        else:
            final_decision = DecisionEnum.ALLOW

        reason_str = (
            "; ".join(reasons)
            if override_applied
            else f"Deterministic policy evaluated intent {intent.value}."
        )

        return PolicyDecision(
            intent=intent,
            resource=ai_result.resource,
            ai_risk=ai_result.risk,
            policy_risk=final_risk,
            requires_approval=final_requires_approval,
            decision=final_decision,
            override_applied=override_applied,
            reason=reason_str,
        )

    @staticmethod
    def evaluate_agent_tool_call(
        tool_name: str,
        arguments: dict,
        allowed_tools: list,
        agent_id: str,
        tenant_id: str,
        user_id: str = "anonymous",
    ) -> dict:
        from app.adapters.base import NormalizedToolCall
        from app.security.tool_gateway import tool_security_gateway
        from app.security.risk_scorer import risk_scoring_engine

        tc = NormalizedToolCall(tool_name=tool_name, arguments=arguments)
        decision_str, reason, risk_contrib = tool_security_gateway.validate_tool_call(
            tool_call=tc,
            allowed_tools=allowed_tools,
            agent_id=agent_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        score, level = risk_scoring_engine.calculate_risk(
            tool_decision=decision_str,
            tool_risk_contrib=risk_contrib,
            has_dangerous_args=(decision_str == "BLOCK" and "Violation" in reason),
        )

        return {
            "decision": decision_str,
            "reason": reason,
            "risk_score": score,
            "risk_level": level,
            "tool_name": tool_name,
            "agent_id": agent_id,
            "tenant_id": tenant_id,
        }

