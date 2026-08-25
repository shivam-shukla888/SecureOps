import secrets
import logging
from typing import Optional
from fastapi import Request, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.security.credentials import credential_repo
from app.security.rbac import TenantUserContext, RoleEnum

logger = logging.getLogger(__name__)
security_bearer = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> str:
    if not credentials or not credentials.credentials:
        logger.warning("Authentication failed: Missing Bearer token in request headers.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = credentials.credentials.strip()

    # Look up hashed credential record
    cred_record = credential_repo.get_by_raw_key(raw_token)

    if not cred_record:
        logger.warning("Authentication failed: Invalid or revoked API key.")
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

    return raw_token
