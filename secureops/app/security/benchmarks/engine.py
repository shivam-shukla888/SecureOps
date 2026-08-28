import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
from app.db.models import AgentBenchmarkModel, BenchmarkFindingModel
from app.schemas.agent import AgentResponse
from app.security.benchmarks.benchmark_registry import benchmark_registry
from app.security.benchmarks.scorecard import scorecard_generator, OverallSecurityScorecard, CategoryScorecard
from app.security.risk_scorer import risk_scoring_engine
from app.security.secrets import redact_secrets, redact_dict
from app.security.tool_gateway import tool_security_gateway

logger = logging.getLogger(__name__)


class BenchmarkFindingResponse(BaseModel):
    finding_id: str
    test_id: str
    category: str
    benchmark_category: str
    severity: str
    attack_input: str
    expected_behavior: str
    actual_behavior: str
    status: str  # PASS / FAIL
    reason: str
    remediation: str = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AgentBenchmarkResponse(BaseModel):
    benchmark_id: str
    agent_id: str
    tenant_id: str
    benchmark_name: str
    execution_mode: str  # LIVE / MOCKED / SIMULATED
    status: str
    total_tests: int
    passed: int
    failed: int
    risk_score: float
    risk_level: str
    scorecard: OverallSecurityScorecard
    findings: List[BenchmarkFindingResponse] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime


AgentBenchmarkResponse.model_rebuild()


class AgentBenchmarkEngine:
    def __init__(self):
        self._in_memory_benchmarks: Dict[str, AgentBenchmarkResponse] = {}

    async def run_benchmark(
        self,
        agent: AgentResponse,
        benchmark_name: str = "security-baseline-v1",
        adaptive: bool = False,
        tenant_id: str = "tenant_default",
        db: Optional[AsyncSession] = None,
    ) -> AgentBenchmarkResponse:
        benchmark_id = f"bm_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        scenarios = list(benchmark_registry.get_benchmark_scenarios(benchmark_name))
        adapter = get_agent_adapter(agent)

        # Determine exact execution mode
        if agent.provider.lower() in ("openai", "openai_compatible") and not adapter._get_api_key():
            execution_mode = "MOCKED"
        elif agent.endpoint_url and "example" in agent.endpoint_url:
            execution_mode = "MOCKED"
        elif agent.endpoint_url:
            execution_mode = "LIVE"
        else:
            execution_mode = "SIMULATED"

        logger.info(f"Starting benchmark '{benchmark_name}' (ID: '{benchmark_id}', Mode: {execution_mode}, Adaptive: {adaptive}) for agent '{agent.agent_id}'")

        findings: List[BenchmarkFindingResponse] = []
        raw_finding_dicts: List[Dict[str, Any]] = []

        # Safe testing bounds
        MAX_ADAPTIVE_REQUESTS = 10
        adaptive_requests_run = 0

        async def _evaluate_scenario(scenario) -> BenchmarkFindingResponse:
            f_now = datetime.now(timezone.utc)
            finding_id = f"bmf_{uuid.uuid4().hex[:12]}"
            b_category = benchmark_registry.get_category_for_test(scenario.test_id)

            # 1. Execute test scenario against Adapter
            exec_req = AgentExecutionRequest(
                agent_id=agent.agent_id,
                tenant_id=tenant_id,
                user_id="benchmark_evaluator",
                prompt=scenario.attack_input,
                parameters={"simulated_tool": scenario.simulated_tool} if scenario.simulated_tool else {},
            )

            exec_res = await adapter.execute(exec_req)

            # 2. Security Analysis: AI Classifier + Tool Security Gateway
            cls_res = await intent_classifier.classify_intent(
                user_request=scenario.attack_input,
                user_id="benchmark_evaluator"
            )
            is_prompt_injection = cls_res.is_prompt_injection

            actual_behavior = "ALLOW"
            eval_reason = "Gateway allowed request cleanly."
            tool_risk_contrib = 0.0

            if is_prompt_injection:
                actual_behavior = "BLOCK"
                eval_reason = "Security Classifier detected adversarial prompt injection pattern."

            # Evaluate tool calls via ToolSecurityGateway -> PolicyEngine
            if exec_res.tool_calls:
                for tc in exec_res.tool_calls:
                    t_dec, t_reason, t_contrib = tool_security_gateway.validate_tool_call(
                        tool_call=tc,
                        allowed_tools=agent.allowed_tools,
                        agent_id=agent.agent_id,
                        tenant_id=tenant_id,
                        user_id="benchmark_evaluator",
                    )
                    tool_risk_contrib = max(tool_risk_contrib, t_contrib)
                    if t_dec == "BLOCK":
                        actual_behavior = "BLOCK"
                        eval_reason = f"Tool Security Gateway blocked tool call: {t_reason}"
                        break
                    elif t_dec == "REQUIRE_APPROVAL" and actual_behavior != "BLOCK":
                        actual_behavior = "REQUIRE_APPROVAL"
                        eval_reason = f"Tool Security Gateway flagged tool call: {t_reason}"

            # 3. Calculate Risk Score
            r_score, r_level = risk_scoring_engine.calculate_risk(
                ai_classifier_score=cls_res.confidence if is_prompt_injection else 0.1,
                is_prompt_injection=is_prompt_injection,
                tool_decision=actual_behavior,
                tool_risk_contrib=tool_risk_contrib,
                is_cross_tenant_attempt=(scenario.category == "cross_tenant_access"),
                is_cross_user_attempt=(scenario.category == "cross_user_access"),
                has_dangerous_args=(scenario.category in ("command_injection", "path_traversal", "ssrf_attempt", "malicious_tool_arguments")),
            )

            # 4. Compare Actual vs Expected Policy Behavior
            status_result = "PASS" if actual_behavior == scenario.expected_behavior or (scenario.expected_behavior == "BLOCK" and actual_behavior in ("BLOCK", "REQUIRE_APPROVAL")) else "FAIL"

            sanitized_input = redact_secrets(scenario.attack_input)
            remediation = benchmark_registry.get_remediation_for_category(b_category)

            evidence_dict = {
                "benchmark_id": benchmark_id,
                "attack_id": scenario.test_id,
                "category": scenario.category,
                "severity": scenario.severity,
                "risk_score": r_score,
                "request_input": sanitized_input,
                "agent_response": redact_secrets(exec_res.output_text[:200]),
                "normalized_tool_calls": [tc.model_dump() for tc in exec_res.tool_calls],
                "policy_decision": actual_behavior,
                "execution_mode": execution_mode,
                "remediation": remediation,
                "timestamp": f_now.isoformat(),
            }

            f_obj = BenchmarkFindingResponse(
                finding_id=finding_id,
                test_id=scenario.test_id,
                category=scenario.category,
                benchmark_category=b_category,
                severity=scenario.severity,
                attack_input=sanitized_input,
                expected_behavior=scenario.expected_behavior,
                actual_behavior=actual_behavior,
                status=status_result,
                reason=eval_reason,
                remediation=remediation,
                evidence=evidence_dict,
                created_at=f_now,
            )

            # Record Audit Log
            try:
                AuditLogger.log_event(
                    request_id=f"bm_req_{finding_id}",
                    user_id="benchmark_evaluator",
                    intent=scenario.category.upper(),
                    resource=agent.agent_id,
                    ai_risk=r_level,
                    policy_risk=r_level,
                    final_decision=actual_behavior,
                    provider=agent.provider,
                    latency_ms=10.0,
                )
                await in_memory_audit_repo.save_audit_log(
                    request_id=f"bm_req_{finding_id}",
                    user_id="benchmark_evaluator",
                    intent=scenario.category.upper(),
                    resource=agent.agent_id,
                    ai_risk=r_level,
                    policy_risk=r_level,
                    final_decision=actual_behavior,
                    provider=agent.provider,
                    fallback_used=False,
                    latency_ms=10.0,
                    tenant_id=tenant_id,
                )
            except Exception as e:
                logger.warning(f"Audit log recording error in benchmark: {e}")

            return f_obj

        # Execute primary scenarios
        for sc in scenarios:
            f = await _evaluate_scenario(sc)
            findings.append(f)
            raw_finding_dicts.append({
                "test_id": f.test_id,
                "category": f.category,
                "benchmark_category": f.benchmark_category,
                "severity": f.severity,
                "status": f.status,
                "risk_score": f.evidence.get("risk_score", 0.1),
            })

        # Adaptive Loop: Trigger targeted variants with hard safety bounds
        if adaptive:
            triggered_ids = [f.test_id for f in findings if f.test_id in ("SE-001", "UT-001", "SSRF-001", "PE-001")]
            adaptive_scenarios = benchmark_registry.get_adaptive_scenarios(triggered_ids, max_adaptive=4)
            for a_sc in adaptive_scenarios:
                if adaptive_requests_run >= MAX_ADAPTIVE_REQUESTS:
                    break
                adaptive_requests_run += 1
                f = await _evaluate_scenario(a_sc)
                findings.append(f)
                raw_finding_dicts.append({
                    "test_id": f.test_id,
                    "category": f.category,
                    "benchmark_category": f.benchmark_category,
                    "severity": f.severity,
                    "status": f.status,
                    "risk_score": f.evidence.get("risk_score", 0.1),
                })

        completed_at = datetime.now(timezone.utc)
        scorecard = scorecard_generator.generate_scorecard(raw_finding_dicts)

        response = AgentBenchmarkResponse(
            benchmark_id=benchmark_id,
            agent_id=agent.agent_id,
            tenant_id=tenant_id,
            benchmark_name=f"{benchmark_name}-adaptive" if adaptive else benchmark_name,
            execution_mode=execution_mode,
            status="COMPLETED",
            total_tests=scorecard.total_tests,
            passed=scorecard.passed,
            failed=scorecard.failed,
            risk_score=scorecard.overall_risk_score,
            risk_level=scorecard.overall_risk_level,
            scorecard=scorecard,
            findings=findings,
            created_at=now,
            completed_at=completed_at,
        )

        self._in_memory_benchmarks[f"{tenant_id}:{benchmark_id}"] = response

        # Persist Benchmark & Findings to DB if session provided
        if db is not None:
            try:
                cat_scores_json = json.dumps({k: v.model_dump() for k, v in scorecard.category_breakdown.items()})
                db_bm = AgentBenchmarkModel(
                    benchmark_id=benchmark_id,
                    agent_id=agent.agent_id,
                    tenant_id=tenant_id,
                    benchmark_name=response.benchmark_name,
                    status="COMPLETED",
                    total_tests=scorecard.total_tests,
                    passed=scorecard.passed,
                    failed=scorecard.failed,
                    risk_score=scorecard.overall_risk_score,
                    risk_level=scorecard.overall_risk_level,
                    category_scores=cat_scores_json,
                    created_at=now,
                    completed_at=completed_at,
                )
                db.add(db_bm)

                for f in findings:
                    db_find = BenchmarkFindingModel(
                        finding_id=f.finding_id,
                        benchmark_id=benchmark_id,
                        tenant_id=tenant_id,
                        test_id=f.test_id,
                        category=f.category,
                        severity=f.severity,
                        attack_input=f.attack_input,
                        expected_behavior=f.expected_behavior,
                        actual_behavior=f.actual_behavior,
                        status=f.status,
                        reason=f.reason,
                        evidence=json.dumps(f.evidence),
                        created_at=f.created_at,
                    )
                    db.add(db_find)

                await db.commit()
            except Exception as exc:
                logger.warning(f"Database error persisting benchmark: {exc}")
                await db.rollback()

        return response

    async def list_benchmarks(
        self,
        tenant_id: str,
        agent_id: str,
        db: Optional[AsyncSession] = None,
    ) -> List[AgentBenchmarkResponse]:
        if db is not None:
            try:
                stmt = select(AgentBenchmarkModel).where(
                    AgentBenchmarkModel.tenant_id == tenant_id,
                    AgentBenchmarkModel.agent_id == agent_id,
                ).order_by(AgentBenchmarkModel.created_at.desc())

                result = await db.execute(stmt)
                db_bms = result.scalars().all()
                if db_bms:
                    bms = []
                    for b in db_bms:
                        res = await self.get_benchmark(tenant_id, b.benchmark_id, db)
                        if res:
                            bms.append(res)
                    return bms
            except Exception as exc:
                logger.warning(f"Database error listing benchmarks: {exc}")

        prefix = f"{tenant_id}:"
        results = [bm for k, bm in self._in_memory_benchmarks.items() if k.startswith(prefix) and bm.agent_id == agent_id]
        return sorted(results, key=lambda b: b.created_at, reverse=True)

    async def get_benchmark(
        self,
        tenant_id: str,
        benchmark_id: str,
        db: Optional[AsyncSession] = None,
    ) -> Optional[AgentBenchmarkResponse]:
        if db is not None:
            try:
                stmt = select(AgentBenchmarkModel).where(
                    AgentBenchmarkModel.tenant_id == tenant_id,
                    AgentBenchmarkModel.benchmark_id == benchmark_id,
                )
                result = await db.execute(stmt)
                db_bm = result.scalar_one_or_none()
                if db_bm:
                    f_stmt = select(BenchmarkFindingModel).where(
                        BenchmarkFindingModel.tenant_id == tenant_id,
                        BenchmarkFindingModel.benchmark_id == benchmark_id,
                    )
                    f_res = await db.execute(f_stmt)
                    db_findings = f_res.scalars().all()

                    findings = []
                    finding_dicts = []
                    for f in db_findings:
                        ev_dict = json.loads(f.evidence) if f.evidence else {}
                        b_cat = benchmark_registry.get_category_for_test(f.test_id)
                        remediation = ev_dict.get("remediation") or benchmark_registry.get_remediation_for_category(b_cat)
                        finding_res = BenchmarkFindingResponse(
                            finding_id=f.finding_id,
                            test_id=f.test_id,
                            category=f.category,
                            benchmark_category=b_cat,
                            severity=f.severity,
                            attack_input=f.attack_input,
                            expected_behavior=f.expected_behavior,
                            actual_behavior=f.actual_behavior,
                            status=f.status,
                            reason=f.reason,
                            remediation=remediation,
                            evidence=ev_dict,
                            created_at=f.created_at,
                        )
                        findings.append(finding_res)
                        finding_dicts.append({
                            "test_id": f.test_id,
                            "category": f.category,
                            "benchmark_category": b_cat,
                            "severity": f.severity,
                            "status": f.status,
                            "risk_score": ev_dict.get("risk_score", 0.5),
                        })

                    scorecard = scorecard_generator.generate_scorecard(finding_dicts)

                    return AgentBenchmarkResponse(
                        benchmark_id=db_bm.benchmark_id,
                        agent_id=db_bm.agent_id,
                        tenant_id=db_bm.tenant_id,
                        benchmark_name=db_bm.benchmark_name,
                        execution_mode="MOCKED" if "example" in (db_bm.benchmark_name or "") else "SIMULATED",
                        status=db_bm.status,
                        total_tests=db_bm.total_tests,
                        passed=db_bm.passed,
                        failed=db_bm.failed,
                        risk_score=db_bm.risk_score,
                        risk_level=db_bm.risk_level,
                        scorecard=scorecard,
                        findings=findings,
                        created_at=db_bm.created_at,
                        completed_at=db_bm.completed_at,
                    )
            except Exception as exc:
                logger.warning(f"Database error fetching benchmark: {exc}")

        return self._in_memory_benchmarks.get(f"{tenant_id}:{benchmark_id}")


agent_benchmark_engine = AgentBenchmarkEngine()
