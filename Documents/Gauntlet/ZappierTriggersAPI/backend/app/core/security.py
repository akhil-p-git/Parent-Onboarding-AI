"""
Security Utilities.

Provides security-related functions for authentication and authorization.
"""

import hashlib
import hmac
import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


def generate_api_key(environment: str = "test") -> str:
    """
    Generate a secure API key.

    Format: sk_{environment}_{32 random chars}
    Example: sk_test_XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

    Args:
        environment: Either 'live' or 'test'

    Returns:
        str: A new API key
    """
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(32))
    return f"sk_{environment}_{random_part}"


def hash_api_key(key: str) -> str:
    """
    Hash an API key for secure storage.

    Uses SHA-256 with a secret salt for additional security.

    Args:
        key: The API key to hash

    Returns:
        str: SHA-256 hash of the key
    """
    salted = f"{key}{settings.API_KEY_SECRET}"
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    Verify an API key against its hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        key: The API key to verify
        key_hash: The stored hash to compare against

    Returns:
        bool: True if the key matches the hash
    """
    computed_hash = hash_api_key(key)
    return secrets.compare_digest(computed_hash, key_hash)


def extract_key_prefix(key: str) -> str:
    """
    Extract the prefix from an API key for identification.

    Args:
        key: The full API key

    Returns:
        str: Key prefix (e.g., 'sk_live_abc1')
    """
    parts = key.split("_")
    if len(parts) >= 3:
        # sk_live_abc123... -> sk_live_abc1
        prefix = f"{parts[0]}_{parts[1]}"
        secret_part = parts[2]
        return f"{prefix}_{secret_part[:4]}"
    return key[:12] if len(key) >= 12 else key


def mask_api_key(key: str) -> str:
    """
    Mask an API key for safe display.

    Args:
        key: The full API key

    Returns:
        str: Masked key like 'sk_live_abc1...xyz9'
    """
    if len(key) < 16:
        return key[:4] + "..." if len(key) > 4 else "***"

    parts = key.split("_")
    if len(parts) >= 3:
        prefix = f"{parts[0]}_{parts[1]}"
        secret = parts[2]
        return f"{prefix}_{secret[:4]}...{secret[-4:]}"

    return f"{key[:8]}...{key[-4:]}"


def generate_signing_secret() -> str:
    """
    Generate a webhook signing secret.

    Returns:
        str: A 32-byte hex string (64 characters)
    """
    return secrets.token_hex(32)


def sign_webhook_payload(payload: str, secret: str, timestamp: int | None = None) -> dict[str, str]:
    """
    Sign a webhook payload for verification.

    Uses HMAC-SHA256 with timestamp to prevent replay attacks.

    Args:
        payload: The JSON payload to sign
        secret: The signing secret
        timestamp: Unix timestamp (defaults to now)

    Returns:
        dict: Contains 'signature' and 'timestamp'
    """
    if timestamp is None:
        timestamp = int(datetime.now(timezone.utc).timestamp())

    # Create signature message: timestamp.payload
    message = f"{timestamp}.{payload}"
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    return {
        "signature": f"v1={signature}",
        "timestamp": str(timestamp),
    }


def verify_webhook_signature(
    payload: str,
    signature: str,
    timestamp: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    """
    Verify a webhook signature.

    Args:
        payload: The received payload
        signature: The received signature header
        timestamp: The received timestamp header
        secret: The signing secret
        tolerance_seconds: Max age of signature (default 5 minutes)

    Returns:
        bool: True if signature is valid and not expired
    """
    try:
        ts = int(timestamp)
    except ValueError:
        return False

    # Check timestamp is within tolerance
    now = int(datetime.now(timezone.utc).timestamp())
    if abs(now - ts) > tolerance_seconds:
        return False

    # Extract signature value (remove 'v1=' prefix if present)
    if signature.startswith("v1="):
        signature = signature[3:]

    # Compute expected signature
    message = f"{ts}.{payload}"
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    return secrets.compare_digest(signature, expected)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Number of bytes (result will be 2x in hex)

    Returns:
        str: Hex-encoded random token
    """
    return secrets.token_hex(length)


def is_key_expired(expires_at: datetime | None) -> bool:
    """
    Check if an API key has expired.

    Args:
        expires_at: Expiration datetime or None for no expiration

    Returns:
        bool: True if expired
    """
    if expires_at is None:
        return False
    return datetime.now(timezone.utc) > expires_at


def parse_bearer_token(authorization: str | None) -> str | None:
    """
    Extract token from Authorization header.

    Args:
        authorization: The Authorization header value

    Returns:
        str | None: The token or None if invalid format
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]
