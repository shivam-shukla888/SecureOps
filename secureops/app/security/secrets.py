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
