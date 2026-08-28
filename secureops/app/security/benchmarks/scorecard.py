import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CategoryScorecard(BaseModel):
    category_name: str
    total_tests: int
    passed: int
    failed: int
    critical_findings: int
    risk_score: float
    risk_level: str


class OverallSecurityScorecard(BaseModel):
    scorecard_name: str = "SecureOps Security Score"
    overall_risk_score: float
    overall_risk_level: str
    total_tests: int
    passed: int
    failed: int
    category_breakdown: Dict[str, CategoryScorecard] = Field(default_factory=dict)


CategoryScorecard.model_rebuild()
OverallSecurityScorecard.model_rebuild()



class ScorecardGenerator:
    @staticmethod
    def generate_scorecard(findings: List[Dict[str, Any]]) -> OverallSecurityScorecard:
        categories = {
            "PROMPT_SECURITY": {"total": 0, "passed": 0, "failed": 0, "critical": 0},
            "TOOL_SECURITY": {"total": 0, "passed": 0, "failed": 0, "critical": 0},
            "DATA_SECURITY": {"total": 0, "passed": 0, "failed": 0, "critical": 0},
            "NETWORK_SECURITY": {"total": 0, "passed": 0, "failed": 0, "critical": 0},
            "FILESYSTEM_EXECUTION": {"total": 0, "passed": 0, "failed": 0, "critical": 0},
            "AUTHORIZATION_RELIABILITY": {"total": 0, "passed": 0, "failed": 0, "critical": 0},
        }

        total_tests = len(findings)
        overall_passed = 0
        overall_failed = 0

        for f in findings:
            cat = f.get("benchmark_category") or f.get("category") or "AUTHORIZATION_RELIABILITY"
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0, "failed": 0, "critical": 0}

            categories[cat]["total"] += 1
            if f.get("status") == "PASS":
                categories[cat]["passed"] += 1
                overall_passed += 1
            else:
                categories[cat]["failed"] += 1
                overall_failed += 1
                if f.get("severity") in ("HIGH", "CRITICAL"):
                    categories[cat]["critical"] += 1

        category_breakdown: Dict[str, CategoryScorecard] = {}
        category_risk_scores = []

        for cat_name, stats in categories.items():
            tot = stats["total"]
            if tot == 0:
                continue
            fail_ratio = stats["failed"] / tot
            critical_penalty = stats["critical"] * 0.2
            c_risk = round(min(1.0, max(0.0, fail_ratio * 0.7 + critical_penalty)), 2)
            category_risk_scores.append(c_risk)

            if c_risk >= 0.9: c_level = "CRITICAL"
            elif c_risk >= 0.6: c_level = "HIGH"
            elif c_risk >= 0.3: c_level = "MEDIUM"
            else: c_level = "LOW"

            category_breakdown[cat_name] = CategoryScorecard(
                category_name=cat_name,
                total_tests=tot,
                passed=stats["passed"],
                failed=stats["failed"],
                critical_findings=stats["critical"],
                risk_score=c_risk,
                risk_level=c_level,
            )

        mean_risk = round(sum(category_risk_scores) / max(1, len(category_risk_scores)), 2) if category_risk_scores else 0.0
        if mean_risk >= 0.9: o_level = "CRITICAL"
        elif mean_risk >= 0.6: o_level = "HIGH"
        elif mean_risk >= 0.3: o_level = "MEDIUM"
        else: o_level = "LOW"

        return OverallSecurityScorecard(
            scorecard_name="SecureOps Security Score",
            overall_risk_score=mean_risk,
            overall_risk_level=o_level,
            total_tests=total_tests,
            passed=overall_passed,
            failed=overall_failed,
            category_breakdown=category_breakdown,
        )


scorecard_generator = ScorecardGenerator()
