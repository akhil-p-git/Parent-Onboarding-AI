"""
Core Utilities.

Common utility functions used throughout the application.
"""

import secrets
import string
from datetime import datetime, timezone

import ulid


def generate_ulid() -> str:
    """
    Generate a ULID (Universally Unique Lexicographically Sortable Identifier).

    ULIDs are:
    - Time-ordered (sortable by creation time)
    - URL-safe (no special characters)
    - 26 characters long

    Returns:
        str: A new ULID string
    """
    return str(ulid.new())


def generate_prefixed_id(prefix: str) -> str:
    """
    Generate an ID with a prefix.

    Args:
        prefix: The prefix to use (e.g., 'evt', 'key', 'sub')

    Returns:
        str: Prefixed ID like 'evt_01ARZ3NDEKTSV4RRFFQ69G5FAV'
    """
    return f"{prefix}_{generate_ulid()}"


def generate_api_key(prefix: str = "sk") -> str:
    """
    Generate a secure API key.

    Format: {prefix}_{environment}_{32 random chars}
    Example: sk_live_abc123def456...

    Args:
        prefix: Key prefix (default: 'sk')

    Returns:
        str: A new API key
    """
    alphabet = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(alphabet) for _ in range(32))
    return f"{prefix}_{random_part}"


def generate_signing_secret() -> str:
    """
    Generate a webhook signing secret.

    Returns:
        str: A 32-byte hex string
    """
    return secrets.token_hex(32)


def utc_now() -> datetime:
    """
    Get current UTC datetime.

    Returns:
        datetime: Current time in UTC with timezone info
    """
    return datetime.now(timezone.utc)


def hash_api_key(key: str, secret: str) -> str:
    """
    Hash an API key for storage.

    Args:
        key: The API key to hash
        secret: The secret to use for hashing

    Returns:
        str: SHA-256 hash of the key
    """
    import hashlib

    return hashlib.sha256(f"{key}{secret}".encode()).hexdigest()


def mask_api_key(key: str) -> str:
    """
    Mask an API key for display.

    Args:
        key: The full API key

    Returns:
        str: Masked key like 'sk_live_abc1...xyz9'
    """
    if len(key) < 12:
        return key[:4] + "..." if len(key) > 4 else "***"

    parts = key.split("_")
    if len(parts) >= 2:
        prefix = "_".join(parts[:-1])
        secret = parts[-1]
        return f"{prefix}_{secret[:4]}...{secret[-4:]}"

    return f"{key[:8]}...{key[-4:]}"
