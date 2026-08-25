import pytest
from fastapi import HTTPException
from app.security.network import SSRFProtector
from app.security.secrets import EnvironmentSecretProvider


def test_ssrf_localhost_blocked():
    protector = SSRFProtector(allowed_hosts=["api.internal-doc-service.com"])
    with pytest.raises(HTTPException) as exc:
        protector.validate_outbound_destination("http://localhost:8080/internal")
    assert exc.value.status_code == 403
    assert "forbidden host" in exc.value.detail.lower()


def test_ssrf_cloud_metadata_endpoint_blocked():
    protector = SSRFProtector(allowed_hosts=["api.internal-doc-service.com"])
    with pytest.raises(HTTPException) as exc:
        protector.validate_outbound_destination("http://169.254.169.254/latest/meta-data/")
    assert exc.value.status_code == 403
    assert "forbidden host" in exc.value.detail.lower()


def test_ssrf_private_ip_blocked():
    protector = SSRFProtector(allowed_hosts=["api.internal-doc-service.com"])
    with pytest.raises(HTTPException) as exc:
        protector.validate_outbound_destination("http://10.0.0.1/admin")
    assert exc.value.status_code == 403
    assert "private or local ip address" in exc.value.detail.lower()


def test_ssrf_unallowlisted_domain_blocked():
    protector = SSRFProtector(allowed_hosts=["api.internal-doc-service.com"])
    with pytest.raises(HTTPException) as exc:
        protector.validate_outbound_destination("https://evil-attacker-server.com/exfiltrate")
    assert exc.value.status_code == 403
    assert "not in the ALLOWED_OUTBOUND_HOSTS allowlist" in exc.value.detail


def test_secret_access_outside_allowlist_blocked():
    provider = EnvironmentSecretProvider(allowed_secrets={"DOCUMENT_SERVICE_TOKEN"})
    with pytest.raises(HTTPException) as exc:
        provider.get_secret("AWS_SECRET_ACCESS_KEY")
    assert exc.value.status_code == 403
    assert "not in the authorized secret access allowlist" in exc.value.detail
