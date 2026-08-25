import time
from typing import Dict, Any
from collections import defaultdict


class ApplicationMetricsTracker:
    def __init__(self):
        self.request_count = 0
        self.ai_fallback_count = 0
        self.approval_count = 0
        self.execution_count = 0
        self.execution_failure_count = 0
        self.rate_limit_count = 0
        self.authentication_failure_count = 0

        self.decision_count: Dict[str, int] = defaultdict(int)
        self.request_latencies: list[float] = []
        self.ai_latencies: list[float] = []

    def record_request(self, decision: str, latency_ms: float, fallback_used: bool):
        self.request_count += 1
        self.decision_count[decision] += 1
        self.request_latencies.append(latency_ms)
        if len(self.request_latencies) > 1000:
            self.request_latencies.pop(0)

        if fallback_used:
            self.ai_fallback_count += 1

        if decision == "REQUIRE_APPROVAL":
            self.approval_count += 1

    def record_ai_latency(self, latency_ms: float):
        self.ai_latencies.append(latency_ms)
        if len(self.ai_latencies) > 1000:
            self.ai_latencies.pop(0)

    def record_execution(self, success: bool):
        self.execution_count += 1
        if not success:
            self.execution_failure_count += 1

    def record_rate_limit(self):
        self.rate_limit_count += 1

    def record_auth_failure(self):
        self.authentication_failure_count += 1

    def get_summary(self) -> Dict[str, Any]:
        avg_req_latency = (
            sum(self.request_latencies) / len(self.request_latencies)
            if self.request_latencies
            else 0.0
        )
        avg_ai_latency = (
            sum(self.ai_latencies) / len(self.ai_latencies)
            if self.ai_latencies
            else 0.0
        )

        return {
            "request_count": self.request_count,
            "avg_request_latency_ms": round(avg_req_latency, 2),
            "avg_ai_provider_latency_ms": round(avg_ai_latency, 2),
            "ai_fallback_count": self.ai_fallback_count,
            "decision_count": dict(self.decision_count),
            "approval_count": self.approval_count,
            "execution_count": self.execution_count,
            "execution_failure_count": self.execution_failure_count,
            "rate_limit_count": self.rate_limit_count,
            "authentication_failure_count": self.authentication_failure_count,
        }


metrics_tracker = ApplicationMetricsTracker()
