"""Security utilities for user identity and credentials.

Provides Argon2 password hashing, verification, and email normalization.
"""

from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Standard Argon2id configuration
_hasher = PasswordHasher()


def normalize_email(email: str) -> str:
    """Normalize email address to trimmed lowercase.

    Args:
        email: Raw email string.

    Returns:
        Normalized email string.

    Raises:
        ValueError: If email is empty or invalid format.
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string.")
    normalized = email.strip().lower()
    if not normalized or "@" not in normalized or "." not in normalized.split("@")[-1]:
        raise ValueError(f"Invalid email address: '{email}'")
    return normalized


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using Argon2id.

    Args:
        plain_password: The plaintext password to hash.

    Returns:
        The Argon2id hash string.

    Raises:
        ValueError: If the password is empty.
    """
    if not plain_password or not isinstance(plain_password, str):
        raise ValueError("Password must be a non-empty string.")
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash.

    Args:
        plain_password: The candidate plaintext password.
        hashed_password: The stored Argon2 hash.

    Returns:
        True if valid, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed_password: str) -> bool:
    """Check if the hashed password needs rehashing due to parameter updates."""
    if not hashed_password:
        return True
    try:
        return _hasher.check_needs_rehash(hashed_password)
    except Exception:
        return True
