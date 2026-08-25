import time
import pytest
from fastapi import HTTPException
from app.security.hmac import generate_hmac_signature, verify_hmac_signature


def test_hmac_signature_generation_and_verification_valid():
    timestamp = str(time.time())
    request_id = "req_test123"
    approval_id = "appr_test456"
    event_type = "APPROVAL_REQUEST_CREATED"
    secret = "my-test-hmac-secret-key"

    signature = generate_hmac_signature(
        timestamp=timestamp,
        request_id=request_id,
        approval_id=approval_id,
        event_type=event_type,
        secret=secret,
    )

    is_valid = verify_hmac_signature(
        signature=signature,
        timestamp_str=timestamp,
        request_id=request_id,
        approval_id=approval_id,
        event_type=event_type,
        secret=secret,
    )
    assert is_valid is True


def test_hmac_invalid_signature_raises_401():
    timestamp = str(time.time())
    bad_signature = "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f"

    with pytest.raises(HTTPException) as exc_info:
        verify_hmac_signature(
            signature=bad_signature,
            timestamp_str=timestamp,
            request_id="req_123",
            approval_id="appr_123",
            event_type="APPROVAL_REQUEST_CREATED",
            secret="my-test-secret",
        )
    assert exc_info.value.status_code == 401
    assert "Invalid HMAC-SHA256" in exc_info.value.detail


def test_hmac_expired_timestamp_replay_attack_raises_401():
    # Timestamp 600 seconds (10 mins) in the past -> Replay attack
    old_timestamp = str(time.time() - 600)
    secret = "my-test-secret"
    signature = generate_hmac_signature(
        timestamp=old_timestamp,
        request_id="req_replay",
        approval_id="appr_replay",
        event_type="APPROVAL_REQUEST_CREATED",
        secret=secret,
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_hmac_signature(
            signature=signature,
            timestamp_str=old_timestamp,
            request_id="req_replay",
            approval_id="appr_replay",
            event_type="APPROVAL_REQUEST_CREATED",
            secret=secret,
            max_age_seconds=300,
        )
    assert exc_info.value.status_code == 401
    assert "replay attack detected" in exc_info.value.detail.lower()


def test_hmac_missing_headers_raises_401():
    with pytest.raises(HTTPException) as exc_info:
        verify_hmac_signature(
            signature="",
            timestamp_str="",
            request_id="req_123",
            approval_id="appr_123",
            event_type="APPROVAL_REQUEST_CREATED",
            secret="my-secret",
        )
    assert exc_info.value.status_code == 401
