import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("secureops.audit")
logger.setLevel(logging.INFO)

# Ensure console handler exists
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)

SENSITIVE_KEYS = {"api_key", "authorization", "bearer", "password", "token", "secret"}


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts sensitive keys from dictionary data."""
    sanitized = {}
    for k, v in data.items():
        if k.lower() in SENSITIVE_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_dict(v)
        else:
            sanitized[k] = v
    return sanitized


redact_sensitive_data = sanitize_dict


class AuditLogger:
    @staticmethod
    def log_event(
        request_id: str,
        user_id: str,
        intent: str,
        resource: str,
        ai_risk: str,
        policy_risk: str,
        final_decision: str,
        provider: str,
        latency_ms: float,
        error_status: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        event = {
            "event_type": "SECURITY_AUDIT_LOG",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id,
            "user_id": user_id,
            "intent": intent,
            "resource": resource,
            "ai_risk": ai_risk,
            "policy_risk": policy_risk,
            "final_decision": final_decision,
            "provider": provider,
            "latency_ms": round(latency_ms, 2),
            "error_status": error_status or "NONE",
        }

        if extra_context:
            event["context"] = sanitize_dict(extra_context)

        logger.info(json.dumps(event))
