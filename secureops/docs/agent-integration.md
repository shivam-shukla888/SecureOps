# SecureOps AI Agent Integration Guide

SecureOps provides a provider-agnostic AI Agent Security Gateway interface capable of connecting and testing arbitrary AI agents without hardcoding vendor logic or exposing API credentials.

---

## Supported Agent Adapters

### 1. Generic REST / HTTP Agent (`GenericHTTPAgentAdapter`)
Connect any company internal or framework-based agent (LangChain, LangGraph, CrewAI, AutoGen, Custom Python, Custom Java) that exposes an HTTP endpoint.

#### Security Controls:
- Automatic SSRF validation: Blocks `127.0.0.1`, private IP subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and cloud metadata (`169.254.169.254`).
- Open redirect protection: `follow_redirects=False`.
- Response size capping: Maximum 2MB payload size limit.
- Protocol enforcement: Requires `https://` in production environments.

#### Registration Example:
```bash
curl -X POST "http://localhost:8000/v1/agents" \
  -H "Authorization: Bearer test-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Company Support Agent",
    "provider": "custom",
    "framework": "langgraph",
    "endpoint_url": "https://api.internal-doc-service.com/agent",
    "allowed_tools": ["knowledge_search", "ticket_lookup"],
    "risk_level": "LOW"
  }'
```

---

### 2. OpenAI-Compatible Agent (`OpenAICompatibleAgentAdapter`)
Connect any OpenAI or OpenAI-compatible endpoint (OpenAI, Groq, LocalAI, vLLM, Ollama).

#### Security Controls:
- **Zero API Key Storage in Database**: API keys are dynamically loaded from environment variables (`OPENAI_API_KEY`) or secret providers (`VaultSecretProvider`, `CloudSecretManagerProvider`).
- Automatic tool call normalization: Converts OpenAI `tool_calls` into internal `NormalizedToolCall` objects.
- Safe MOCKED fallback mode when no external API credential exists in test environments.

#### Registration Example:
```bash
curl -X POST "http://localhost:8000/v1/agents" \
  -H "Authorization: Bearer test-secret-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production GPT-4o Agent",
    "provider": "openai",
    "framework": "openai_sdk",
    "endpoint_url": "https://api.openai.com/v1",
    "allowed_tools": ["read_data", "knowledge_search"],
    "risk_level": "LOW"
  }'
```

---

### 3. Simulated Agent (`SimulatedAgentAdapter`)
Provides non-destructive execution simulation for sandbox testing and red-team evaluation without host side-effects.

---

## Agent Adapter Lifecycle

```
Provider / External Agent
          ↓
  BaseAgentAdapter
          ↓
AgentExecutionRequest
          ↓
AgentExecutionResponse & NormalizedToolCall
          ↓
  ToolSecurityGateway
          ↓
  Deterministic PolicyEngine
          ↓
ALLOW / REQUIRE_APPROVAL / BLOCK
```
