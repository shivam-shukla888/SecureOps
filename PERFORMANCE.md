# SecureOps Performance & Latency Profile

This document outlines the performance characteristics, latency benchmarks, and throughput capabilities of the SecureOps AI Gateway.

---

## Latency Decomposition

Request processing latency in SecureOps is divided into two distinct components:

1. **Local Deterministic Overhead**: Policy evaluation, rate limiting, Pydantic input validation, HMAC verification, and mock execution.
2. **External AI Classification Latency**: Network round-trip and LLM inference time for Google Gemini 2.5 Flash and Groq (Llama-3.3-70b).

```text
TOTAL REQUEST LATENCY = LOCAL DETERMINISTIC OVERHEAD (~0.05 ms) + EXTERNAL AI LATENCY (~200-600 ms)
```

---

## Local Micro-Benchmark Results

Benchmark executed over 10,000 iterations via `python scripts/benchmark.py`:

| Subsystem Component | Avg Latency (ms) | Operations / Sec / Core | Performance Impact |
| :--- | :--- | :--- | :--- |
| **Deterministic Security Policy Engine** | **0.0051 ms** | ~196,000 req/sec | Negligible (< 0.01% of total) |
| **In-Memory Rate Limiter** | **0.0124 ms** | ~80,000 req/sec | Negligible |
| **Tool Input Pydantic Validation & Handler** | **0.0310 ms** | ~32,000 req/sec | Negligible |
| **Total Local Overhead** | **~0.0485 ms** | **~20,600 req/sec** | Sub-millisecond |

---

## External AI Provider Latency Profile

| AI Provider | Model | Typical Latency (ms) | P99 Latency (ms) | SLA Availability |
| :--- | :--- | :--- | :--- | :--- |
| **Google Gemini (Primary)** | `gemini-2.5-flash` | 250 ms | 650 ms | 99.9% |
| **Groq (Fallback)** | `llama-3.3-70b-versatile` | 180 ms | 450 ms | 99.95% |

---

## Optimization & Scaling Strategies

1. **Classification Caching (Redis)**:
   - Identical natural language queries can be cached in Redis with a configurable TTL, eliminating LLM network latency for repeated requests.

2. **Async Request Queuing**:
   - For async background tool execution, the API immediately returns an `execution_id` or `approval_id` within < 1ms, offloading heavy processing to Celery / RQ background workers.

3. **Rate Limiting Concurrency**:
   - Using Redis pipelines for sliding window rate checks (`ZREMRANGEBYSCORE` + `ZCARD`) ensures Redis rate checks add less than 1ms latency.
