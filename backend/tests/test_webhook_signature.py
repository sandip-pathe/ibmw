"""
Tests for webhook signature verification.
"""
import hashlib
import hmac

import pytest
from fastapi import HTTPException

from app.core.webhook_verifier import WebhookVerifier


def test_verify_valid_signature():
    """Test webhook signature verification with valid signature."""
    secret = "test-secret"
    verifier = WebhookVerifier(secret)

    payload = b'{"test": "data"}'
    signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    assert verifier.verify_signature(payload, signature) is True


def test_verify_invalid_signature():
    """Test webhook signature verification with invalid signature."""
    verifier = WebhookVerifier("test-secret")

    payload = b'{"test": "data"}'
    invalid_signature = "sha256=invalid_signature"

    assert verifier.verify_signature(payload, invalid_signature) is False


def test_verify_missing_signature():
    """Test webhook signature verification with missing signature."""
    verifier = WebhookVerifier("test-secret")

    payload = b'{"test": "data"}'

    assert verifier.verify_signature(payload, None) is False


def test_verify_wrong_format():
    """Test webhook signature verification with wrong format."""
    verifier = WebhookVerifier("test-secret")

    payload = b'{"test": "data"}'
    wrong_format = "md5=somehash"  # Wrong algorithm

    assert verifier.verify_signature(payload, wrong_format) is False
