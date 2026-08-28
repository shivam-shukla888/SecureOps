import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Set
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

PERMITTED_SECRETS: Set[str] = {
    "DOCUMENT_SERVICE_TOKEN",
    "DATABASE_READ_ONLY_SECRET",
}


class SecretProvider(ABC):
    @abstractmethod
    def get_secret(self, secret_name: str) -> Optional[str]:
        pass


class EnvironmentSecretProvider(SecretProvider):
    def __init__(self, allowed_secrets: Set[str] = PERMITTED_SECRETS):
        self.allowed_secrets = allowed_secrets

    def get_secret(self, secret_name: str) -> Optional[str]:
        if secret_name not in self.allowed_secrets:
            logger.warning(
                f"Unauthorized attempt to access secret '{secret_name}' outside permitted allowlist."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Secret '{secret_name}' is not in the authorized secret access allowlist."
            )
        
        secret_value = os.environ.get(secret_name)
        if not secret_value:
            return f"mock_secret_value_for_{secret_name.lower()}"
        return secret_value


class VaultSecretProvider(SecretProvider):
    """
    HashiCorp Vault Secret Manager Adapter interface.
    """
    def __init__(self, vault_url: str = "http://vault:8200", allowed_secrets: Set[str] = PERMITTED_SECRETS):
        self.vault_url = vault_url
        self.allowed_secrets = allowed_secrets
        self.env_fallback = EnvironmentSecretProvider(allowed_secrets=allowed_secrets)

    def get_secret(self, secret_name: str) -> Optional[str]:
        if secret_name not in self.allowed_secrets:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Secret '{secret_name}' is not in the authorized secret access allowlist."
            )
        # In development/local fallback mode, read from environment provider
        return self.env_fallback.get_secret(secret_name)


class CloudSecretManagerProvider(SecretProvider):
    """
    AWS Secrets Manager / GCP Secret Manager Adapter interface.
    """
    def __init__(self, allowed_secrets: Set[str] = PERMITTED_SECRETS):
        self.allowed_secrets = allowed_secrets
        self.env_fallback = EnvironmentSecretProvider(allowed_secrets=allowed_secrets)

    def get_secret(self, secret_name: str) -> Optional[str]:
        if secret_name not in self.allowed_secrets:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Secret '{secret_name}' is not in the authorized secret access allowlist."
            )
        return self.env_fallback.get_secret(secret_name)


secret_provider = EnvironmentSecretProvider()

import re

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"secops_[a-zA-Z0-9_]{16,}", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{36}", re.IGNORECASE),
    re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),
]


def redact_secrets(text: str) -> str:
    if not isinstance(text, str):
        return str(text)
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_SECRET]", redacted)
    return redacted


def redact_dict(data: dict) -> dict:
    from app.audit.logger import sanitize_dict
    return sanitize_dict(data)

