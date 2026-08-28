import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import AgentExecutionRequest
from app.adapters.factory import get_agent_adapter
from app.ai.classifier import intent_classifier
from app.approval.manager import approval_manager
from app.audit.logger import AuditLogger
from app.audit.repository import in_memory_audit_repo
from app.audit.siem import siem_manager


from app.db.models import AgentEvaluationModel, EvaluationFindingModel
from app.schemas.agent import AgentResponse
from app.security.evaluations.scenarios.scenarios_registry import scenario_registry
from app.security.policy import DeterministicPolicyEngine
from app.security.risk_scorer import risk_scoring_engine
from app.security.secrets import redact_dict, redact_secrets
from app.security.tool_gateway import tool_security_gateway

logger = logging.getLogger(__name__)


class EvaluationFindingResponse(BaseModel):
    finding_id: str
    test_id: str
    category: str
    severity: str
    attack_input: str
    expected_behavior: str
    actual_behavior: str
    status: str  # PASS / FAIL
    reason: str
    created_at: datetime


class AgentEvaluationResponse(BaseModel):
    evaluation_id: str
    agent_id: str
    tenant_id: str
    test_suite: str
    status: str
    total_tests: int
    passed: int
    failed: int
    risk_score: float
    risk_level: str
    findings: List[EvaluationFindingResponse] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime


class AgentEvaluationEngine:
    def __init__(self):
        self._in_memory_evaluations: Dict[str, AgentEvaluationResponse] = {}

    async def run_evaluation(
        self,
        agent: AgentResponse,
        test_suite: str = "security-baseline",
        tenant_id: str = "tenant_default",
        db: Optional[AsyncSession] = None,
    ) -> AgentEvaluationResponse:
        evaluation_id = f"eval_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        scenarios = scenario_registry.get_test_suite(test_suite)
        adapter = get_agent_adapter(agent)

        logger.info(f"Starting security evaluation '{evaluation_id}' for agent '{agent.agent_id}' ({len(scenarios)} tests)")

        findings: List[EvaluationFindingResponse] = []
        total_tests = len(scenarios)
        passed = 0
        failed = 0
        cumulative_risk = 0.0

        for scenario in scenarios:
            f_now = datetime.now(timezone.utc)
            finding_id = f"find_{uuid.uuid4().hex[:12]}"

            # 1. Execute test case against Agent Adapter
            exec_req = AgentExecutionRequest(
                agent_id=agent.agent_id,
                tenant_id=tenant_id,
                user_id="red_team_evaluator",
                prompt=scenario.attack_input,
                parameters={"simulated_tool": scenario.simulated_tool} if scenario.simulated_tool else {},
            )
            
            exec_res = await adapter.execute(exec_req)

            # 2. Security Analysis: AI Classifier + Tool Gateway
            cls_res = await intent_classifier.classify_intent(
                user_request=scenario.attack_input,
                user_id="red_team_evaluator"
            )
            is_prompt_injection = cls_res.is_prompt_injection

            actual_behavior = "ALLOW"
            eval_reason = "Gateway allowed execution cleanly."
            tool_risk_contrib = 0.0

            # Evaluate prompt injection decision
            if is_prompt_injection:
                actual_behavior = "BLOCK"
                eval_reason = "Prompt injection attempt detected by Security Classifier."

            # Evaluate tool calls via ToolSecurityGateway
            if exec_res.tool_calls:
                for tc in exec_res.tool_calls:
                    t_dec, t_reason, t_contrib = tool_security_gateway.validate_tool_call(
                        tool_call=tc,
                        allowed_tools=agent.allowed_tools,
                        agent_id=agent.agent_id,
                        tenant_id=tenant_id,
                        user_id="red_team_evaluator",
                    )
                    tool_risk_contrib = max(tool_risk_contrib, t_contrib)
                    if t_dec == "BLOCK":
                        actual_behavior = "BLOCK"
                        eval_reason = f"Tool Gateway blocked execution: {t_reason}"
                        break
                    elif t_dec == "REQUIRE_APPROVAL" and actual_behavior != "BLOCK":
                        actual_behavior = "REQUIRE_APPROVAL"
                        eval_reason = f"Tool Gateway flagged execution: {t_reason}"
                        # Trigger HITL approval workflow integration
                        try:
                            await approval_manager.create_approval(
                                request_id=f"req_{finding_id}",
                                tenant_id=tenant_id,
                                requester_id="red_team_evaluator",
                                intent="UPDATE_DATA",
                                resource=tc.tool_name,
                                policy_risk="HIGH",
                                db=db,
                            )
                        except Exception as e:
                            logger.warning(f"Error creating approval ticket: {e}")

            # 3. Calculate Risk Score
            r_score, r_level = risk_scoring_engine.calculate_risk(
                ai_classifier_score=cls_res.confidence if is_prompt_injection else 0.1,
                is_prompt_injection=is_prompt_injection,
                tool_decision=actual_behavior,
                tool_risk_contrib=tool_risk_contrib,
                is_cross_tenant_attempt=(scenario.category == "cross_tenant_access"),
                is_cross_user_attempt=(scenario.category == "cross_user_access"),
                has_dangerous_args=(scenario.category in ("command_injection", "path_traversal", "ssrf_attempt")),
            )
            cumulative_risk += r_score

            # 4. Compare Actual vs Expected Policy Behavior
            # Pass condition: gateway/agent behavior matched expected security policy
            status_result = "PASS" if actual_behavior == scenario.expected_behavior or (scenario.expected_behavior == "BLOCK" and actual_behavior in ("BLOCK", "REQUIRE_APPROVAL")) else "FAIL"
            if status_result == "PASS":
                passed += 1
            else:
                failed += 1

            sanitized_input = redact_secrets(scenario.attack_input)

            finding = EvaluationFindingResponse(
                finding_id=finding_id,
                test_id=scenario.test_id,
                category=scenario.category,
                severity=scenario.severity,
                attack_input=sanitized_input,
                expected_behavior=scenario.expected_behavior,
                actual_behavior=actual_behavior,
                status=status_result,
                reason=eval_reason,
                created_at=f_now,
            )
            findings.append(finding)

            # Audit event recording
            try:
                AuditLogger.log_event(
                    request_id=f"req_{finding_id}",
                    user_id="red_team_evaluator",
                    intent=scenario.category.upper(),
                    resource=agent.agent_id,
                    ai_risk=r_level,
                    policy_risk=r_level,
                    final_decision=actual_behavior,
                    provider=agent.provider,
                    latency_ms=12.5,
                )
                await in_memory_audit_repo.save_audit_log(
                    request_id=f"req_{finding_id}",
                    user_id="red_team_evaluator",
                    intent=scenario.category.upper(),
                    resource=agent.agent_id,
                    ai_risk=r_level,
                    policy_risk=r_level,
                    final_decision=actual_behavior,
                    provider=agent.provider,
                    fallback_used=False,
                    latency_ms=12.5,
                    tenant_id=tenant_id,
                )
            except Exception as e:
                logger.warning(f"Audit log recording error: {e}")


        completed_at = datetime.now(timezone.utc)
        final_risk_score = round(cumulative_risk / max(1, total_tests), 2)
        _, final_risk_level = risk_scoring_engine.calculate_risk(ai_classifier_score=final_risk_score)

        response = AgentEvaluationResponse(
            evaluation_id=evaluation_id,
            agent_id=agent.agent_id,
            tenant_id=tenant_id,
            test_suite=test_suite,
            status="COMPLETED",
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            risk_score=final_risk_score,
            risk_level=final_risk_level,
            findings=findings,
            created_at=now,
            completed_at=completed_at,
        )

        self._in_memory_evaluations[f"{tenant_id}:{evaluation_id}"] = response

        # Persist Evaluation & Findings to Database if session provided
        if db is not None:
            try:
                db_eval = AgentEvaluationModel(
                    evaluation_id=evaluation_id,
                    agent_id=agent.agent_id,
                    tenant_id=tenant_id,
                    test_suite=test_suite,
                    status="COMPLETED",
                    total_tests=total_tests,
                    passed=passed,
                    failed=failed,
                    risk_score=final_risk_score,
                    risk_level=final_risk_level,
                    created_at=now,
                    completed_at=completed_at,
                )
                db.add(db_eval)

                for f in findings:
                    db_find = EvaluationFindingModel(
                        finding_id=f.finding_id,
                        evaluation_id=evaluation_id,
                        tenant_id=tenant_id,
                        test_id=f.test_id,
                        category=f.category,
                        severity=f.severity,
                        attack_input=f.attack_input,
                        expected_behavior=f.expected_behavior,
                        actual_behavior=f.actual_behavior,
                        status=f.status,
                        reason=f.reason,
                        created_at=f.created_at,
                    )
                    db.add(db_find)

                await db.commit()
            except Exception as exc:
                logger.warning(f"Database error saving evaluation: {exc}")
                await db.rollback()

        return response

    async def list_evaluations(
        self,
        tenant_id: str,
        agent_id: str,
        db: Optional[AsyncSession] = None,
    ) -> List[AgentEvaluationResponse]:
        if db is not None:
            try:
                stmt = select(AgentEvaluationModel).where(
                    AgentEvaluationModel.tenant_id == tenant_id,
                    AgentEvaluationModel.agent_id == agent_id,
                ).order_by(AgentEvaluationModel.created_at.desc())

                result = await db.execute(stmt)
                db_evals = result.scalars().all()
                if db_evals:
                    evals = []
                    for e in db_evals:
                        evals.append(await self.get_evaluation(tenant_id, e.evaluation_id, db))
                    return [e for e in evals if e is not None]
            except Exception as exc:
                logger.warning(f"Database error listing evaluations: {exc}")

        prefix = f"{tenant_id}:"
        results = [ev for k, ev in self._in_memory_evaluations.items() if k.startswith(prefix) and ev.agent_id == agent_id]
        return sorted(results, key=lambda e: e.created_at, reverse=True)

    async def get_evaluation(
        self,
        tenant_id: str,
        evaluation_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[AgentEvaluationResponse]:
        if db is not None:
            try:
                stmt = select(AgentEvaluationModel).where(
                    AgentEvaluationModel.tenant_id == tenant_id,
                    AgentEvaluationModel.evaluation_id == evaluation_id,
                )
                result = await db.execute(stmt)
                db_eval = result.scalar_one_or_none()
                if db_eval:
                    f_stmt = select(EvaluationFindingModel).where(
                        EvaluationFindingModel.tenant_id == tenant_id,
                        EvaluationFindingModel.evaluation_id == evaluation_id,
                    )
                    f_res = await db.execute(f_stmt)
                    db_findings = f_res.scalars().all()

                    findings = [
                        EvaluationFindingResponse(
                            finding_id=f.finding_id,
                            test_id=f.test_id,
                            category=f.category,
                            severity=f.severity,
                            attack_input=f.attack_input,
                            expected_behavior=f.expected_behavior,
                            actual_behavior=f.actual_behavior,
                            status=f.status,
                            reason=f.reason,
                            created_at=f.created_at,
                        )
                        for f in db_findings
                    ]

                    return AgentEvaluationResponse(
                        evaluation_id=db_eval.evaluation_id,
                        agent_id=db_eval.agent_id,
                        tenant_id=db_eval.tenant_id,
                        test_suite=db_eval.test_suite,
                        status=db_eval.status,
                        total_tests=db_eval.total_tests,
                        passed=db_eval.passed,
                        failed=db_eval.failed,
                        risk_score=db_eval.risk_score,
                        risk_level=db_eval.risk_level,
                        findings=findings,
                        created_at=db_eval.created_at,
                        completed_at=db_eval.completed_at,
                    )
            except Exception as exc:
                logger.warning(f"Database error fetching evaluation: {exc}")

        return self._in_memory_evaluations.get(f"{tenant_id}:{evaluation_id}")


agent_evaluation_engine = AgentEvaluationEngine()
