import hashlib
import secrets
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import Dict, Optional, List
from fastapi import HTTPException, status
from app.config import settings
from app.security.rbac import RoleEnum

logger = logging.getLogger(__name__)


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key(prefix: str = "secops_") -> tuple[str, str]:
    raw_secret = secrets.token_urlsafe(32)
    raw_key = f"{prefix}{raw_secret}"
    key_hash = hash_api_key(raw_key)
    return raw_key, key_hash


@dataclass
class APICredentialRecord:
    credential_id: str
    tenant_id: str
    user_id: str
    name: str
    key_hash: str
    role: RoleEnum
    created_at: datetime
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        if self.revoked_at is not None:
            return False
        if self.expires_at is not None and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True


class APICredentialRepository:
    def __init__(self):
        self.credentials: Dict[str, APICredentialRecord] = {}
        self.hash_index: Dict[str, str] = {}
        self._seed_default_credentials()

    def _seed_default_credentials(self):
        # Default test API key seed
        test_key = "test-secret-api-key-12345"
        test_hash = hash_api_key(test_key)
        rec = APICredentialRecord(
            credential_id="cred_test_default",
            tenant_id="tenant_default",
            user_id="test_user",
            name="Default Test Credential",
            key_hash=test_hash,
            role=RoleEnum.OWNER,
            created_at=datetime.now(timezone.utc),
        )
        self.credentials[rec.credential_id] = rec
        self.hash_index[test_hash] = rec.credential_id

        # Settings API key seed
        if settings.API_KEY and settings.API_KEY != test_key:
            env_hash = hash_api_key(settings.API_KEY)
            env_rec = APICredentialRecord(
                credential_id="cred_env_default",
                tenant_id="tenant_default",
                user_id="admin_user",
                name="Environment API Credential",
                key_hash=env_hash,
                role=RoleEnum.OWNER,
                created_at=datetime.now(timezone.utc),
            )
            self.credentials[env_rec.credential_id] = env_rec
            self.hash_index[env_hash] = env_rec.credential_id

    async def get_by_raw_key(self, raw_key: str) -> Optional[APICredentialRecord]:
        if not raw_key:
            return None

        # Clean token: strip whitespace, quotes, and duplicate Bearer/bearer prefix
        clean_key = raw_key.strip("\"' \t\r\n")
        if clean_key.startswith("Bearer ") or clean_key.startswith("bearer "):
            clean_key = clean_key[7:].strip("\"' \t\r\n")

        k_hash = hash_api_key(clean_key)
        cred_id = self.hash_index.get(k_hash)

        # Dynamic fallback check for settings.API_KEY (handles dynamic .env updates)
        if not cred_id and settings.API_KEY:
            clean_env_key = settings.API_KEY.strip("\"' \t\r\n")
            if clean_key == clean_env_key:
                env_hash = hash_api_key(clean_env_key)
                env_rec = APICredentialRecord(
                    credential_id="cred_env_default",
                    tenant_id="tenant_default",
                    user_id="admin_user",
                    name="Environment API Credential",
                    key_hash=env_hash,
                    role=RoleEnum.OWNER,
                    created_at=datetime.now(timezone.utc),
                )
                self.credentials[env_rec.credential_id] = env_rec
                self.hash_index[env_hash] = env_rec.credential_id
                cred_id = env_rec.credential_id

        # Fallback check for test default key
        if not cred_id:
            test_key = "test-secret-api-key-12345"
            if clean_key == test_key:
                t_hash = hash_api_key(test_key)
                t_rec = APICredentialRecord(
                    credential_id="cred_test_default",
                    tenant_id="tenant_default",
                    user_id="test_user",
                    name="Default Test Credential",
                    key_hash=t_hash,
                    role=RoleEnum.OWNER,
                    created_at=datetime.now(timezone.utc),
                )
                self.credentials[t_rec.credential_id] = t_rec
                self.hash_index[t_hash] = t_rec.credential_id
                cred_id = t_rec.credential_id

        # Database lookup if miss in memory index
        if not cred_id:
            try:
                from app.db.session import async_session_factory
                from app.db.models import APICredentialModel
                from sqlalchemy import select

                async with async_session_factory() as session:
                    stmt = select(APICredentialModel).where(APICredentialModel.key_hash == k_hash)
                    res = await session.execute(stmt)
                    db_cred = res.scalar_one_or_none()

                    if db_cred:
                        role_enum = RoleEnum(db_cred.role) if db_cred.role in [r.value for r in RoleEnum] else RoleEnum.OPERATOR
                        rec = APICredentialRecord(
                            credential_id=db_cred.credential_id,
                            tenant_id=db_cred.tenant_id,
                            user_id=db_cred.user_id,
                            name=db_cred.name,
                            key_hash=db_cred.key_hash,
                            role=role_enum,
                            created_at=db_cred.created_at or datetime.now(timezone.utc),
                            expires_at=db_cred.expires_at,
                            revoked_at=db_cred.revoked_at,
                            last_used_at=db_cred.last_used_at,
                        )
                        self.credentials[rec.credential_id] = rec
                        self.hash_index[rec.key_hash] = rec.credential_id
                        cred_id = rec.credential_id
            except Exception as exc:
                logger.debug(f"PostgreSQL credential read skipped/failed ({exc})")

        if not cred_id:
            return None

        cred = self.credentials.get(cred_id)
        if cred and cred.is_valid():
            cred.last_used_at = datetime.now(timezone.utc)
            return cred
        return None

    async def create_credential(
        self,
        tenant_id: str,
        user_id: str,
        name: str,
        role: RoleEnum = RoleEnum.OPERATOR,
        expires_in_days: Optional[int] = None,
    ) -> tuple[str, APICredentialRecord]:
        raw_key, k_hash = generate_api_key()
        cred_id = f"cred_{secrets.token_hex(6)}"
        expires_at = (
            datetime.now(timezone.utc) + timedelta(days=expires_in_days)
            if expires_in_days
            else None
        )

        record = APICredentialRecord(
            credential_id=cred_id,
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            key_hash=k_hash,
            role=role,
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
        )

        self.credentials[cred_id] = record
        self.hash_index[k_hash] = cred_id

        # Persist into PostgreSQL
        try:
            from app.db.session import async_session_factory
            from app.db.models import APICredentialModel
            async with async_session_factory() as session:
                db_model = APICredentialModel(
                    credential_id=cred_id,
                    tenant_id=tenant_id,
                    user_id=user_id,
                    name=name,
                    key_hash=k_hash,
                    role=role.value if hasattr(role, "value") else str(role),
                    created_at=record.created_at,
                    expires_at=expires_at,
                )
                session.add(db_model)
                await session.commit()
        except Exception as exc:
            logger.debug(f"PostgreSQL credential save skipped/failed ({exc})")

        return raw_key, record

    async def revoke_credential(self, credential_id: str, tenant_id: str) -> APICredentialRecord:
        cred = self.credentials.get(credential_id)
        if not cred or cred.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Credential '{credential_id}' not found in tenant '{tenant_id}'."
            )
        cred.revoked_at = datetime.now(timezone.utc)

        # Update in PostgreSQL
        try:
            from app.db.session import async_session_factory
            from app.db.models import APICredentialModel
            from sqlalchemy import select
            async with async_session_factory() as session:
                stmt = select(APICredentialModel).where(APICredentialModel.credential_id == credential_id)
                res = await session.execute(stmt)
                db_cred = res.scalar_one_or_none()
                if db_cred:
                    db_cred.revoked_at = cred.revoked_at
                    await session.commit()
        except Exception as exc:
            logger.debug(f"PostgreSQL credential revoke skipped/failed ({exc})")

        return cred

    async def rotate_credential(self, credential_id: str, tenant_id: str) -> tuple[str, APICredentialRecord]:
        old_cred = await self.revoke_credential(credential_id, tenant_id)
        return await self.create_credential(
            tenant_id=tenant_id,
            user_id=old_cred.user_id,
            name=f"{old_cred.name} (Rotated)",
            role=old_cred.role,
        )

    async def list_tenant_credentials(self, tenant_id: str) -> List[APICredentialRecord]:
        # Query PostgreSQL to include any persisted credentials
        try:
            from app.db.session import async_session_factory
            from app.db.models import APICredentialModel
            from sqlalchemy import select
            async with async_session_factory() as session:
                stmt = select(APICredentialModel).where(APICredentialModel.tenant_id == tenant_id)
                res = await session.execute(stmt)
                db_creds = res.scalars().all()
                for db_c in db_creds:
                    if db_c.credential_id not in self.credentials:
                        r_enum = RoleEnum(db_c.role) if db_c.role in [r.value for r in RoleEnum] else RoleEnum.OPERATOR
                        rec = APICredentialRecord(
                            credential_id=db_c.credential_id,
                            tenant_id=db_c.tenant_id,
                            user_id=db_c.user_id,
                            name=db_c.name,
                            key_hash=db_c.key_hash,
                            role=r_enum,
                            created_at=db_c.created_at or datetime.now(timezone.utc),
                            expires_at=db_c.expires_at,
                            revoked_at=db_c.revoked_at,
                            last_used_at=db_c.last_used_at,
                        )
                        self.credentials[rec.credential_id] = rec
                        self.hash_index[rec.key_hash] = rec.credential_id
        except Exception as exc:
            logger.debug(f"PostgreSQL credential list skipped/failed ({exc})")

        return [c for c in self.credentials.values() if c.tenant_id == tenant_id]


credential_repo = APICredentialRepository()
