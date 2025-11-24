"""
GitHub webhook signature verification.
"""
import hashlib
import hmac
from typing import Optional

from fastapi import HTTPException, Request, status
from loguru import logger

from app.config import get_settings

settings = get_settings()


class WebhookVerifier:
    """GitHub webhook signature verifier."""

    def __init__(self, secret: str):
        self.secret = secret.encode("utf-8")

    def verify_signature(self, payload: bytes, signature_header: Optional[str]) -> bool:
        """
        Verify GitHub webhook signature using HMAC SHA256.
        
        Args:
            payload: Raw webhook payload bytes
            signature_header: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not signature_header:
            logger.warning("Missing X-Hub-Signature-256 header")
            return False

        # Extract signature from header (format: "sha256=<signature>")
        if not signature_header.startswith("sha256="):
            logger.warning(f"Invalid signature format: {signature_header}")
            return False

        expected_signature = signature_header[7:]  # Remove "sha256=" prefix

        # Compute HMAC
        mac = hmac.new(self.secret, msg=payload, digestmod=hashlib.sha256)
        computed_signature = mac.hexdigest()

        # Compare signatures (constant-time comparison)
        is_valid = hmac.compare_digest(computed_signature, expected_signature)

        if not is_valid:
            logger.warning("Webhook signature verification failed")

        return is_valid

    async def verify_request(self, request: Request) -> bytes:
        """
        Verify webhook request and return payload.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Raw payload bytes
            
        Raises:
            HTTPException: If signature is invalid
        """
        # Get raw body
        payload = await request.body()

        # Get signature header
        signature = request.headers.get("X-Hub-Signature-256")

        # Verify
        if not self.verify_signature(payload, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

        return payload


# Global verifier instance
webhook_verifier = WebhookVerifier(settings.github_webhook_secret)
