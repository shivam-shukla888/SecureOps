import hmac
import hashlib
import time
from typing import Dict, Any
from fastapi import HTTPException, status
from app.config import settings

MAX_TIMESTAMP_DELTA_SECONDS = 300  # 5 minutes replay protection window


def generate_hmac_signature(
    timestamp: str,
    request_id: str,
    approval_id: str,
    event_type: str,
    secret: str = settings.N8N_WEBHOOK_SECRET,
) -> str:
    """
    Generates HMAC-SHA256 signature over payload parameters.
    """
    message = f"{timestamp}.{request_id}.{approval_id}.{event_type}"
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def verify_hmac_signature(
    signature: str,
    timestamp_str: str,
    request_id: str,
    approval_id: str,
    event_type: str,
    secret: str = settings.N8N_WEBHOOK_SECRET,
    max_age_seconds: int = MAX_TIMESTAMP_DELTA_SECONDS,
) -> bool:
    """
    Verifies HMAC-SHA256 signature and checks timestamp age for replay protection.
    Raises HTTPException if missing, invalid, or expired.
    """
    if not signature or not timestamp_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required HMAC security headers (X-SecureOps-Signature or X-SecureOps-Timestamp)."
        )

    # 1. Timestamp age validation (Replay Protection)
    try:
        ts = float(timestamp_str)
        now = time.time()
        if abs(now - ts) > max_age_seconds:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Webhook event expired or replay attack detected. Timestamp outside allowed tolerance window."
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-SecureOps-Timestamp header value."
        )

    # 2. Re-compute expected signature
    expected_signature = generate_hmac_signature(
        timestamp=timestamp_str,
        request_id=request_id,
        approval_id=approval_id,
        event_type=event_type,
        secret=secret,
    )

    # 3. Constant-time comparison
    if not hmac.compare_digest(signature.lower(), expected_signature.lower()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid HMAC-SHA256 webhook signature."
        )

    return True
