from enum import Enum
from dataclasses import dataclass
from typing import List, Optional
from fastapi import Request, HTTPException, status


class RoleEnum(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    APPROVER = "APPROVER"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


# Role Hierarchy Order (Higher index = higher privilege)
ROLE_HIERARCHY = {
    RoleEnum.VIEWER: 1,
    RoleEnum.OPERATOR: 2,
    RoleEnum.APPROVER: 3,
    RoleEnum.ADMIN: 4,
    RoleEnum.OWNER: 5,
}


@dataclass
class TenantUserContext:
    tenant_id: str
    user_id: str
    role: RoleEnum
    credential_id: Optional[str] = None


def require_role(allowed_roles: List[RoleEnum]):
    async def role_checker(request: Request) -> TenantUserContext:
        ctx: Optional[TenantUserContext] = getattr(request.state, "user_context", None)
        if not ctx:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required: No tenant user context found."
            )

        if ctx.role not in allowed_roles:
            # Also allow if user has higher role in hierarchy
            max_allowed_level = max(ROLE_HIERARCHY.get(r, 0) for r in allowed_roles)
            user_level = ROLE_HIERARCHY.get(ctx.role, 0)

            if user_level < max_allowed_level and ctx.role != RoleEnum.OWNER:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"RBAC Permission Denied: Role '{ctx.role.value}' is not authorized for this operation. Required: {[r.value for r in allowed_roles]}"
                )

        return ctx

    return role_checker
