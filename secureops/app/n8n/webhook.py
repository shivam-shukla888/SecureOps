import time
import logging
import httpx
from typing import Dict, Any, Optional

from app.config import settings
from app.security.hmac import generate_hmac_signature

logger = logging.getLogger(__name__)


class N8nApprovalWebhookClient:
    def __init__(
        self,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.webhook_url = webhook_url or settings.N8N_APPROVAL_WEBHOOK_URL
        self.webhook_secret = webhook_secret or settings.N8N_WEBHOOK_SECRET

    async def dispatch_approval_request(
        self,
        request_id: str,
        approval_id: str,
        user_id: str,
        intent: str,
        resource: str,
        policy_risk: str,
        expires_at: str,
    ) -> bool:
        if not self.webhook_url:
            logger.info(
                f"N8N_APPROVAL_WEBHOOK_URL not configured. Skipping outbound n8n notification for approval {approval_id}."
            )
            return False

        timestamp = str(time.time())
        event_type = "APPROVAL_REQUEST_CREATED"

        signature = generate_hmac_signature(
            timestamp=timestamp,
            request_id=request_id,
            approval_id=approval_id,
            event_type=event_type,
            secret=self.webhook_secret,
        )

        headers = {
            "Content-Type": "application/json",
            "X-SecureOps-Signature": signature,
            "X-SecureOps-Timestamp": timestamp,
        }

        payload = {
            "event_type": event_type,
            "timestamp": timestamp,
            "request_id": request_id,
            "approval_id": approval_id,
            "user_id": user_id,
            "intent": intent,
            "resource": resource,
            "policy_risk": policy_risk,
            "expires_at": expires_at,
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self.webhook_url, json=payload, headers=headers)
                if response.status_code in [200, 201, 202]:
                    logger.info(f"Successfully dispatched n8n approval webhook for ticket {approval_id}.")
                    return True
                else:
                    logger.warning(
                        f"n8n webhook returned status HTTP {response.status_code}: {response.text}"
                    )
                    return False
        except Exception as exc:
            logger.error(f"Failed to dispatch n8n approval webhook: {exc}")
            return False


n8n_webhook_client = N8nApprovalWebhookClient()
