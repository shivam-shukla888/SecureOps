import ipaddress
import logging
from urllib.parse import urlparse
from typing import List, Optional
from fastapi import HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

BLOCKED_EXPLICIT_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.169.254",  # Cloud metadata endpoint (AWS/GCP/Azure)
    "metadata.google.internal",
}


def extract_hostname(target: str) -> str:
    if "://" in target:
        parsed = urlparse(target)
        hostname = parsed.hostname or ""
    else:
        # If target is host:port or simple hostname
        hostname = target.split(":")[0].split("/")[0]
    return hostname.strip().lower()


class SSRFProtector:
    def __init__(self, allowed_hosts: Optional[List[str]] = None):
        self.allowed_hosts = [
            h.lower() for h in (allowed_hosts or settings.ALLOWED_OUTBOUND_HOSTS)
        ]

    def validate_outbound_destination(self, target: str) -> str:
        if not target or not target.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Outbound network destination cannot be empty."
            )

        hostname = extract_hostname(target)

        # 1. Check explicit blocked hosts / metadata service
        if hostname in BLOCKED_EXPLICIT_HOSTS:
            logger.warning(f"SSRF Protection blocked request to forbidden host: {hostname}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"SSRF Protection: Access to forbidden host '{hostname}' is blocked."
            )

        # 2. Check IP address ranges (Private IPs & Loopbacks)
        try:
            ip_obj = ipaddress.ip_address(hostname)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                logger.warning(f"SSRF Protection blocked private/local IP: {hostname}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"SSRF Protection: Access to private or local IP address '{hostname}' is blocked."
                )
        except ValueError:
            # Target is a domain name, not a raw IP address
            pass

        # 3. Check against explicit domain allowlist
        if hostname not in self.allowed_hosts:
            logger.warning(f"Outbound host '{hostname}' not in allowed hosts: {self.allowed_hosts}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Outbound network policy violation: Host '{hostname}' is not in the ALLOWED_OUTBOUND_HOSTS allowlist."
            )

        return hostname


ssrf_protector = SSRFProtector()
