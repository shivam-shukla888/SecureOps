import time
import asyncio
import logging
from typing import Dict, Any, Optional

from app.ai.providers.base import BaseAIProvider

logger = logging.getLogger(__name__)

# In-memory cache for provider health checks (60 seconds TTL)
_HEALTH_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_TTL_SECONDS = 60.0


async def check_provider_health(provider: BaseAIProvider) -> Dict[str, Any]:
    """
    Checks if a provider is configured and operational without exposing secrets.
    Caches results for 60 seconds to avoid spamming provider APIs on frequent /ready calls.
    """
    provider_name = getattr(provider, "name", "unknown")
    model_name = getattr(provider, "model_name", "default")
    is_configured = getattr(provider, "is_configured", False)

    if not is_configured:
        return {
            "configured": False,
            "operational": False,
            "model": model_name,
            "status": "UNCONFIGURED",
        }

    now = time.time()
    cached = _HEALTH_CACHE.get(provider_name)
    if cached and (now - cached.get("_cached_at", 0)) < _CACHE_TTL_SECONDS:
        return {k: v for k, v in cached.items() if not k.startswith("_")}

    # Perform lightweight operational test with "What is 2+2?"
    start_time = time.time()
    try:
        # Run with strict timeout
        result = await asyncio.wait_for(provider.classify_request("What is 2+2?"), timeout=5.0)
        latency_ms = (time.time() - start_time) * 1000.0
        health_info = {
            "configured": True,
            "operational": True,
            "model": model_name,
            "latency_ms": round(latency_ms, 1),
            "status": "OPERATIONAL",
            "_cached_at": now,
        }
        _HEALTH_CACHE[provider_name] = health_info
        return {k: v for k, v in health_info.items() if not k.startswith("_")}
    except Exception as exc:
        latency_ms = (time.time() - start_time) * 1000.0
        failure_category = type(exc).__name__
        logger.warning(
            f"[AI Diagnostics] Health check failed for provider '{provider_name}' ({model_name}): {failure_category}"
        )
        health_info = {
            "configured": True,
            "operational": False,
            "model": model_name,
            "latency_ms": round(latency_ms, 1),
            "status": "FAILED",
            "failure_category": failure_category,
            "_cached_at": now,
        }
        _HEALTH_CACHE[provider_name] = health_info
        return {k: v for k, v in health_info.items() if not k.startswith("_")}


async def get_all_ai_providers_health(
    openai_provider: BaseAIProvider,
    gemini_provider: BaseAIProvider,
    groq_provider: BaseAIProvider,
) -> Dict[str, Any]:
    """
    Returns health and operational status for all providers.
    """
    primary_status = await check_provider_health(openai_provider)
    gemini_status = await check_provider_health(gemini_provider)
    groq_status = await check_provider_health(groq_provider)

    is_any_operational = (
        primary_status.get("operational")
        or gemini_status.get("operational")
        or groq_status.get("operational")
    )

    is_any_configured = (
        primary_status.get("configured")
        or gemini_status.get("configured")
        or groq_status.get("configured")
    )

    return {
        "status": "ready" if is_any_operational else ("degraded" if is_any_configured else "unavailable"),
        "providers": {
            "primary": primary_status,
            "gemini": gemini_status,
            "groq": groq_status,
        },
    }
