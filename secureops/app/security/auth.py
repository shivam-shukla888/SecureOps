import secrets
import logging
from typing import Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.security.credentials import credential_repo, clean_api_key
from app.security.rbac import TenantUserContext, RoleEnum

logger = logging.getLogger(__name__)
security_bearer = HTTPBearer(
    auto_error=False,
    scheme_name="HTTPBearer",
    description="Enter your API Key value (e.g. secops_live_...). Do NOT include the 'Bearer ' prefix.",
)


async def verify_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> str:
    raw_header = request.headers.get("Authorization") or request.headers.get("authorization")

    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif raw_header:
        token = raw_header

    if not token or not token.strip():
        logger.warning("Authentication failed: Missing Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clean_token = clean_api_key(token)
    if not clean_token:
        logger.warning("Authentication failed: Empty or malformed Bearer token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Look up hashed credential record via token
    cred_record = await credential_repo.get_by_raw_key(clean_token)

    if not cred_record:
        logger.warning(
            f"Authentication failed: Invalid or unauthorized API key (Token Length={len(clean_token)}, Scheme={'Bearer' if credentials else 'RawHeader'})."
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Attach tenant user context to request state
    request.state.user_context = TenantUserContext(
        tenant_id=cred_record.tenant_id,
        user_id=cred_record.user_id,
        role=cred_record.role,
        credential_id=cred_record.credential_id,
    )

    return clean_token
