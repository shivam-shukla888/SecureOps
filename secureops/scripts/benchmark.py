#!/usr/bin/env python3
import sys
import os
import time
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.decision import ClassifierResult, IntentEnum, RiskEnum
from app.security.policy import DeterministicPolicyEngine
from app.security.rate_limit import InMemoryRateLimiter
from app.tools.registry import ToolRegistry
from app.tools.schemas import SearchDocumentInput


async def run_benchmark(iterations: int = 10000):
    print("===============================================================================")
    print(f"            SECUREOPS MICRO-BENCHMARK SUITE ({iterations:,} iterations)         ")
    print("===============================================================================\n")

    # 1. Deterministic Policy Engine Benchmark
    ai_res = ClassifierResult(intent=IntentEnum.DELETE_DATA, resource="table1", risk=RiskEnum.LOW, requires_approval=False)
    start_policy = time.perf_counter()
    for _ in range(iterations):
        _ = DeterministicPolicyEngine.evaluate(ai_res)
    policy_time = time.perf_counter() - start_policy
    avg_policy_ms = (policy_time / iterations) * 1000.0

    # 2. Rate Limiter Benchmark
    limiter = InMemoryRateLimiter(requests_per_minute=1000000)
    start_rate = time.perf_counter()
    for i in range(iterations):
        _ = await limiter.is_rate_limited("bench_user")
    rate_time = time.perf_counter() - start_rate
    avg_rate_ms = (rate_time / iterations) * 1000.0

    # 3. Tool Lookup & Schema Validation Benchmark
    inp = SearchDocumentInput(query="benchmark query test")
    tool_def = ToolRegistry.get_tool_for_intent(IntentEnum.SEARCH_DOCUMENT)
    start_tool = time.perf_counter()
    for _ in range(iterations):
        _ = await tool_def.handler(inp)
    tool_time = time.perf_counter() - start_tool
    avg_tool_ms = (tool_time / iterations) * 1000.0

    total_local_latency_ms = avg_policy_ms + avg_rate_ms + avg_tool_ms

    print(f"1. Deterministic Policy Evaluation : {avg_policy_ms:.4f} ms / request")
    print(f"2. Rate Limiter Check               : {avg_rate_ms:.4f} ms / request")
    print(f"3. Tool Handler Execution           : {avg_tool_ms:.4f} ms / request")
    print("-------------------------------------------------------------------------------")
    print(f"TOTAL LOCAL DETERMINISTIC LATENCY  : {total_local_latency_ms:.4f} ms (~{1000.0/total_local_latency_ms:.0f} req/sec/core)\n")

    print("NOTE: External AI classification (Gemini / Groq) introduces an additional ~200-800ms")
    print("network latency depending on provider SLA and prompt complexity.")
    print("===============================================================================")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
