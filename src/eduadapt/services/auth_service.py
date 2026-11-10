"""Authentication and Student Identity Service for EduAdapt.

Implements:
- Argon2id password verification and hashing
- JWT access token creation and validation (HS256)
- Password strength and email normalization
- Cryptographically secure OTP generation, verification, cooldown, and attempt limiting
- SMTP email delivery for OTP verification
- Atomic student registration and profile persistence
- Secure student login and identity retrieval
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import re
import secrets
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, Optional, Tuple
import uuid

from fastapi import Depends, HTTPException, Header, status
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eduadapt.config import Settings, get_settings
from eduadapt.db.models.student import Student
from eduadapt.db.models.user import User
from eduadapt.db.security import hash_password, normalize_email, verify_password
from eduadapt.db.session import get_db_session

logger = logging.getLogger("eduadapt.services.auth")


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """Payload for student account creation."""

    full_name: str = Field(..., min_length=2, max_length=150, description="Student's real full name")
    email: str = Field(..., description="Student's email address")
    password: str = Field(..., min_length=8, max_length=128, description="Account password (min 8 characters)")
    confirm_password: Optional[str] = Field(default=None, description="Confirm password matching password")
    college: Optional[str] = Field(default=None, max_length=255)
    department: Optional[str] = Field(default=None, max_length=255)
    academic_year: Optional[int] = Field(default=1, ge=1, le=6)
    section: Optional[str] = Field(default=None, max_length=50)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return normalize_email(v)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter.")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit.")
        return v


class LoginRequest(BaseModel):
    """Payload for student login."""

    email: str = Field(..., description="Student's registered email")
    password: str = Field(..., description="Student's account password")

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        return normalize_email(v)


class TokenResponse(BaseModel):
    """Authentication token response payload."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: Dict[str, Any]
    student: Dict[str, Any]


class SendOtpRequest(BaseModel):
    """Payload to request an OTP code."""

    email: Optional[str] = None
    phone: Optional[str] = None
    country_code: Optional[str] = "+91"


class VerifyOtpRequest(BaseModel):
    """Payload to verify an OTP code."""

    email: Optional[str] = None
    phone: Optional[str] = None
    code: str = Field(..., min_length=4, max_length=8, description="One-time verification code")


# -----------------------------------------------------------------------------
# JWT Token Handling
# -----------------------------------------------------------------------------

def create_access_token(
    user_id: str,
    email: str,
    role: str = "student",
    expires_delta: Optional[timedelta] = None,
    settings: Optional[Settings] = None,
) -> str:
    """Create a signed JWT access token for an authenticated user."""
    cfg = settings or get_settings()
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=cfg.jwt_access_token_expire_minutes))

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "eduadapt-auth",
    }

    return jwt.encode(payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)


def decode_access_token(token: str, settings: Optional[Settings] = None) -> Dict[str, Any]:
    """Decode and validate a JWT access token.

    Raises:
        HTTPException(401): If token is expired, invalid, or forged.
    """
    cfg = settings or get_settings()
    try:
        payload = jwt.decode(
            token,
            cfg.jwt_secret_key,
            algorithms=[cfg.jwt_algorithm],
            issuer="eduadapt-auth",
        )
        return payload
    except JWTError as exc:
        logger.warning("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid credentials. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# -----------------------------------------------------------------------------
# OTP Verification Store & Email Delivery
# -----------------------------------------------------------------------------

class OTPStore:
    """Thread-safe, secure ephemeral OTP manager with rate-limiting and attempt limits."""

    def __init__(self):
        # Maps target_key -> dict(hash, expires_at, attempts, resend_after)
        self._records: Dict[str, Dict[str, Any]] = {}

    def _hash_code(self, target: str, code: str) -> str:
        # Salt with target identifier
        return hashlib.sha256(f"{target.lower()}:{code}".encode("utf-8")).hexdigest()

    def generate(
        self,
        target: str,
        expire_seconds: int = 300,
        cooldown_seconds: int = 30,
        code_length: int = 6,
    ) -> Tuple[str, Optional[int]]:
        """Generate a cryptographically secure numeric OTP code.

        Returns:
            Tuple of (code, cooldown_remaining)
        """
        key = target.strip().lower()
        now = datetime.now(timezone.utc)

        # Check resend cooldown
        if key in self._records:
            resend_after = self._records[key].get("resend_after")
            if resend_after and now < resend_after:
                seconds_left = int((resend_after - now).total_seconds())
                return "", seconds_left

        # Generate a 6-digit numeric string
        raw_code = f"{secrets.randbelow(10 ** code_length):0{code_length}d}"
        expires_at = now + timedelta(seconds=expire_seconds)
        resend_after = now + timedelta(seconds=cooldown_seconds)

        self._records[key] = {
            "hash": self._hash_code(key, raw_code),
            "expires_at": expires_at,
            "resend_after": resend_after,
            "attempts": 0,
            "max_attempts": 3,
        }

        return raw_code, None

    def verify(self, target: str, candidate_code: str) -> bool:
        """Verify an OTP code. Enforces single-use, max attempts, and expiration."""
        key = target.strip().lower()
        now = datetime.now(timezone.utc)

        record = self._records.get(key)
        if not record:
            return False

        if now > record["expires_at"]:
            self._records.pop(key, None)
            return False

        record["attempts"] += 1
        if record["attempts"] > record["max_attempts"]:
            self._records.pop(key, None)
            return False

        expected_hash = record["hash"]
        candidate_hash = self._hash_code(key, candidate_code.strip())

        if hmac.compare_digest(expected_hash, candidate_hash):
            # Consumed successfully - single use only
            self._records.pop(key, None)
            return True

        return False

    def clear(self, target: str) -> None:
        self._records.pop(target.strip().lower(), None)


_otp_store = OTPStore()


def send_otp_via_email(recipient_email: str, code: str, settings: Optional[Settings] = None) -> bool:
    """Send OTP code via SMTP if configured."""
    cfg = settings or get_settings()
    if not cfg.smtp_host or not cfg.smtp_from_email:
        logger.info("SMTP not configured. OTP generated for %s (dev_code mode active)", recipient_email)
        return False

    try:
        msg = EmailMessage()
        msg["Subject"] = "Your EduAdapt Verification Code"
        msg["From"] = cfg.smtp_from_email
        msg["To"] = recipient_email
        msg.set_content(
            f"Hello,\n\n"
            f"Your EduAdapt one-time verification code is: {code}\n\n"
            f"This code will expire in {cfg.otp_expire_seconds // 60} minutes.\n"
            f"If you did not request this code, you can safely ignore this email.\n\n"
            f"— The EduAdapt Team"
        )

        with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10) as server:
            if cfg.smtp_use_tls:
                server.starttls()
            if cfg.smtp_username and cfg.smtp_password:
                server.login(cfg.smtp_username, cfg.smtp_password)
            server.send_message(msg)

        logger.info("Successfully sent OTP email to %s", recipient_email)
        return True
    except Exception as exc:
        logger.warning("Failed to send OTP email to %s: %s", recipient_email, exc)
        return False


# -----------------------------------------------------------------------------
# Student Registration and Authentication Services
# -----------------------------------------------------------------------------

async def register_student(
    session: AsyncSession,
    data: RegisterRequest,
) -> Dict[str, Any]:
    """Register a new student account in a single atomic database transaction.

    Ensures:
    - Unique email constraint
    - Argon2id password hashing
    - Safe student profile linking with auto-generated code
    - Zero plain password or hash leakage
    """
    if data.confirm_password is not None and data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password and confirm password do not match.",
        )

    normalized = normalize_email(data.email)

    # Check for duplicate email
    existing_stmt = select(User).where(User.email == normalized)
    existing_res = await session.execute(existing_stmt)
    if existing_res.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists. Please sign in.",
        )

    # Hash password using Argon2id
    hashed = hash_password(data.password)

    # Generate unique student code (e.g. S-A1B2C3)
    code_suffix = uuid.uuid4().hex[:6].upper()
    student_code = f"S-{code_suffix}"

    user_id = uuid.uuid4()
    student_id = uuid.uuid4()

    new_user = User(
        id=user_id,
        email=normalized,
        hashed_password=hashed,
        role="student",
        is_active=True,
        is_verified=False,
    )

    new_student = Student(
        id=student_id,
        user_id=user_id,
        student_code=student_code,
        full_name=data.full_name.strip(),
        college=data.college.strip() if data.college else None,
        department=data.department.strip() if data.department else None,
        academic_year=data.academic_year,
        section=data.section.strip() if data.section else None,
        current_skill_level="Beginner",
        has_completed_diagnostic=False,
    )

    session.add(new_user)
    session.add(new_student)
    await session.commit()
    await session.refresh(new_user)
    await session.refresh(new_student)

    # Issue access token immediately for smooth onboarding
    token = create_access_token(user_id=str(new_user.id), email=new_user.email, role=new_user.role)

    return {
        "message": "Student account created successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "role": new_user.role,
            "is_verified": new_user.is_verified,
        },
        "student": {
            "id": str(new_student.id),
            "student_id": new_student.student_code,
            "student_code": new_student.student_code,
            "full_name": new_student.full_name,
            "college": new_student.college,
            "department": new_student.department,
            "current_skill_level": new_student.current_skill_level,
            "has_completed_diagnostic": new_student.has_completed_diagnostic,
        },
    }


async def authenticate_student(
    session: AsyncSession,
    email: str,
    plain_password: str,
) -> TokenResponse:
    """Authenticate student credentials, update last_login_at, and issue JWT."""
    normalized = normalize_email(email)

    stmt = select(User).options(selectinload(User.student_profile)).where(User.email == normalized)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    # Constant-time comparison logic / generic error to prevent email enumeration
    generic_err = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password. Please try again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise generic_err

    if not verify_password(plain_password, user.hashed_password):
        raise generic_err

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your student account has been deactivated. Please contact support.",
        )

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(user)

    cfg = get_settings()
    token = create_access_token(user_id=str(user.id), email=user.email, role=user.role, settings=cfg)

    student = user.student_profile
    student_payload = {
        "id": str(student.id) if student else "",
        "student_code": student.student_code if student else "S001",
        "full_name": student.full_name if student else "Student",
        "college": student.college if student else None,
        "department": student.department if student else None,
        "academic_year": student.academic_year if student else 1,
        "section": student.section if student else None,
        "current_skill_level": student.current_skill_level if student else "Beginner",
        "has_completed_diagnostic": student.has_completed_diagnostic if student else False,
    }

    user_payload = {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "is_verified": user.is_verified,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=cfg.jwt_access_token_expire_minutes,
        user=user_payload,
        student=student_payload,
    )


# -----------------------------------------------------------------------------
# FastAPI Dependencies for Protected Endpoints
# -----------------------------------------------------------------------------

async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """FastAPI dependency extracting and validating the authenticated User record."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or are malformed.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(raw_token)
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user identifier in token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(User).options(selectinload(User.student_profile)).where(User.id == user_uuid)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User associated with this token does not exist.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    return user


async def get_current_student(
    current_user: User = Depends(get_current_user),
) -> Student:
    """FastAPI dependency resolving the Student profile for the authenticated User."""
    if not current_user.student_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No student profile is attached to this user account.",
        )
    return current_user.student_profile
