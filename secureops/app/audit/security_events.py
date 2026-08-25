import uuid
import logging
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    AUTH_FAILURE = "AUTH_FAILURE"
    AUTHZ_FAILURE = "AUTHZ_FAILURE"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    POLICY_OVERRIDE = "POLICY_OVERRIDE"
    SSRF_BLOCK = "SSRF_BLOCK"
    APPROVAL_REPLAY = "APPROVAL_REPLAY"
    CREDENTIAL_REVOKED = "CREDENTIAL_REVOKED"
    RATE_LIMIT_TRIGGERED = "RATE_LIMIT_TRIGGERED"
    TOOL_PERMISSION_DENIED = "TOOL_PERMISSION_DENIED"


class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class SecurityEvent:
    event_type: SecurityEventType
    severity: SeverityEnum
    tenant_id: str = "tenant_default"
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    event_id: str = field(default_factory=lambda: f"sec_evt_{uuid.uuid4().hex[:12]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "metadata": self.metadata,
        }
