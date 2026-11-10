"""FastAPI Authentication and Student Profile Router.

Provides:
- POST /api/auth/register
- POST /api/auth/login
- GET  /api/auth/me
- POST /api/auth/logout
- POST /api/auth/send-otp
- POST /api/auth/verify-otp
- GET  /api/profile
- PUT  /api/profile
"""

import logging
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eduadapt.config import get_settings
from eduadapt.db.models.student import Student
from eduadapt.db.models.user import User
from eduadapt.db.security import hash_password, normalize_email
from eduadapt.db.session import get_db_session
from eduadapt.services.auth_service import (
    LoginRequest,
    RegisterRequest,
    SendOtpRequest,
    TokenResponse,
    VerifyOtpRequest,
    _otp_store,
    authenticate_student,
    create_access_token,
    decode_access_token,
    get_current_student,
    get_current_user,
    register_student,
    send_otp_via_email,
)

logger = logging.getLogger("eduadapt.routers.auth")

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
profile_router = APIRouter(prefix="/api", tags=["Student Profile"])


# -----------------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------------

@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create student account",
    description="Registers a new student user and profile in an atomic transaction.",
)
async def register_endpoint(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Register a new student."""
    return await register_student(session=session, data=payload)


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="Student login",
    description="Authenticates student credentials, updates login timestamp, and issues a JWT.",
)
async def login_endpoint(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate student with email and password."""
    return await authenticate_student(
        session=session,
        email=payload.email,
        plain_password=payload.password,
    )


@auth_router.get(
    "/me",
    summary="Get current student profile",
    description="Returns the profile and account status for the currently authenticated student.",
)
async def me_endpoint(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve authenticated user and student profile."""
    student = current_user.student_profile

    recent_attempts = []
    completed_diag_count = 0
    if student:
        from eduadapt.db.models.assessment import DiagnosticAttempt
        stmt_att = (
            select(DiagnosticAttempt)
            .where(
                DiagnosticAttempt.student_id == student.id,
                DiagnosticAttempt.status == "completed",
            )
            .order_by(DiagnosticAttempt.completed_at.desc())
        )
        res_att = await session.execute(stmt_att)
        atts = list(res_att.scalars().all())
        completed_diag_count = len(atts)
        for a in atts:
            score_pct = float(a.total_score / a.maximum_score * 100) if a.maximum_score else 0.0
            if a.result_summary and "score" in a.result_summary:
                score_pct = float(a.result_summary["score"])
            time_str = a.completed_at.strftime("%b %d, %Y") if a.completed_at else "Recently"
            recent_attempts.append({
                "id": str(a.id),
                "title": "Initial Diagnostic Assessment" if a.assessment_type == "initial_diagnostic" else "Assessment",
                "type": "diagnostic",
                "score": round(score_pct, 1),
                "time": time_str,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "level": a.assigned_skill_level or "Calibrated",
            })

    student_data = {
        "id": str(student.id) if student else "",
        "student_id": student.student_code if student else "S001",
        "student_code": student.student_code if student else "S001",
        "full_name": student.full_name if student else "Student",
        "college": student.college if student else None,
        "department": student.department if student else None,
        "academic_year": student.academic_year if student else 1,
        "semester": student.semester if student else 1,
        "section": student.section if student else None,
        "avatar_url": student.avatar_url if student else None,
        "current_skill_level": student.current_skill_level if (student and student.has_completed_diagnostic) else "Not determined",
        "learning_pace": student.learning_pace if (student and student.has_completed_diagnostic) else "Not determined",
        "explanation_style": student.explanation_style or "step_by_step" if student else "step_by_step",
        "preferences": student.preferences or {} if student else {},
        "accessibility": student.accessibility or {} if student else {},
        "has_completed_diagnostic": student.has_completed_diagnostic if student else False,
        "tests_completed": completed_diag_count,
        "diagnostic_completed_count": completed_diag_count,
        "recent_attempts": recent_attempts,
        "recent_activity": recent_attempts[0] if recent_attempts else None,
    }

    user_data = {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }

    return {
        "user": user_data,
        "student": student_data,
        "onboarding_complete": True,
    }


@auth_router.post(
    "/logout",
    summary="Sign out student",
    description="Stateless token logout endpoint. Client clears access token.",
)
async def logout_endpoint() -> Dict[str, str]:
    """Acknowledge student logout and clear session state."""
    return {"message": "You have been logged out successfully."}


@auth_router.post(
    "/send-otp",
    summary="Send one-time verification code",
    description="Issues an OTP code via SMTP email or SMS channel with rate limiting.",
)
async def send_otp_endpoint(payload: SendOtpRequest) -> Dict[str, Any]:
    """Generate and dispatch a 6-digit OTP code."""
    cfg = get_settings()
    target = (payload.email or payload.phone or "").strip()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either an email address or mobile phone number is required.",
        )

    code, cooldown_remaining = _otp_store.generate(
        target=target,
        expire_seconds=cfg.otp_expire_seconds,
        cooldown_seconds=cfg.otp_resend_cooldown_seconds,
    )

    if cooldown_remaining is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {cooldown_remaining} seconds before requesting another code.",
        )

    # If email provided, attempt real SMTP delivery
    sent_via_email = False
    if "@" in target:
        sent_via_email = send_otp_via_email(target, code, settings=cfg)

    # In non-production environments or when SMTP is unconfigured, provide dev_code
    # so development and automated verification are never blocked.
    is_dev = cfg.app_env != "production" or not cfg.smtp_host

    # Obfuscate target for privacy
    if "@" in target:
        parts = target.split("@")
        obfuscated = f"{parts[0][:2]}***@{parts[1]}"
    else:
        obfuscated = f"***{target[-4:]}" if len(target) >= 4 else "***"

    response: Dict[str, Any] = {
        "message": f"Verification code sent to {obfuscated}.",
        "expires_in_seconds": cfg.otp_expire_seconds,
    }

    if is_dev:
        response["dev_code"] = code

    return response


@auth_router.post(
    "/verify-otp",
    summary="Verify one-time code",
    description="Validates a submitted 6-digit OTP code and activates verified status.",
)
async def verify_otp_endpoint(
    payload: VerifyOtpRequest,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Verify submitted OTP code and return authentication session."""
    target = (payload.email or payload.phone or "").strip()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Target email or phone number is required.",
        )

    is_valid = _otp_store.verify(target, payload.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please check the code and try again.",
        )

    # Check if a user with this email or phone exists
    user = None
    if "@" in target:
        try:
            norm_email = normalize_email(target)
            stmt = select(User).options(selectinload(User.student_profile)).where(User.email == norm_email)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
            if user:
                user.is_verified = True
                await session.commit()
                await session.refresh(user)
        except Exception:
            pass

    # If user exists, issue token for that user; otherwise issue temporary student onboarding token
    cfg = get_settings()
    if user:
        token = create_access_token(user_id=str(user.id), email=user.email, role=user.role, settings=cfg)
        student = user.student_profile
        student_id = str(student.id) if student else str(user.id)
    else:
        # Create or link an account for phone/OTP login
        temp_id = str(uuid.uuid4())
        token = create_access_token(user_id=temp_id, email=f"{target}@eduadapt.local", role="student", settings=cfg)
        student_id = temp_id

    return {
        "message": "Verification successful.",
        "token": token,
        "verified": True,
        "onboarding_complete": True,
        "student_id": student_id,
    }


# -----------------------------------------------------------------------------
# Profile & Accessibility Endpoints
# -----------------------------------------------------------------------------

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    college: Optional[str] = None
    department: Optional[str] = None
    learning_pace: Optional[str] = None
    explanation_style: Optional[str] = None
    preferred_explanation_style: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    accessibility: Optional[Dict[str, Any]] = None


@profile_router.get(
    "/profile",
    summary="Get user profile and accessibility settings",
    description="Returns current student profile details and user interface preferences.",
)
async def get_profile_endpoint(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Fetch student profile and accessibility parameters."""
    user = None
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization.split(" ", 1)[1].strip()
            payload = decode_access_token(token)
            user_uuid = uuid.UUID(payload.get("sub"))
            stmt = select(User).options(selectinload(User.student_profile)).where(User.id == user_uuid)
            res = await session.execute(stmt)
            user = res.scalar_one_or_none()
        except Exception:
            user = None

    if user and user.student_profile:
        st = user.student_profile
        name = st.full_name
        code = st.student_code or str(st.id)
        college = st.college
        department = st.department
        skill = st.current_skill_level if st.has_completed_diagnostic else "Not determined"
        pace = st.learning_pace if st.has_completed_diagnostic else "Not determined"
        diag = st.has_completed_diagnostic
        style = st.explanation_style or "step_by_step"
        pref = st.preferences or {}
        acc = st.accessibility or {
            "font": "default",
            "text_size": "md",
            "contrast": "normal",
            "chunk_size": "micro",
            "reduce_motion": False,
        }
    else:
        name = "Student"
        code = "S001"
        college = None
        department = None
        skill = "Not determined"
        pace = "Not determined"
        diag = False
        style = "step_by_step"
        pref = {}
        acc = {
            "font": "default",
            "text_size": "md",
            "contrast": "normal",
            "chunk_size": "micro",
            "reduce_motion": False,
        }

    return {
        "student": {
            "student_id": code,
            "full_name": name,
            "college": college,
            "department": department,
            "current_skill_level": skill,
            "learning_pace": pace,
            "explanation_style": style,
            "has_completed_diagnostic": diag,
            "preferences": pref,
            "accessibility": acc,
        },
        "profile": {
            "name": name,
            "student_code": code,
            "explanation_style": style,
            "learning_pace": pace,
            "accessibility": acc,
            "preferences": pref,
        },
    }


@profile_router.put(
    "/profile",
    summary="Update student profile and accessibility preferences",
    description="Persists changes to student preferences, accessibility settings, and explanation style.",
)
async def update_profile_endpoint(
    payload: UpdateProfileRequest,
    current_student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Persist student profile and accessibility parameters."""
    if payload.full_name is not None and payload.full_name.strip():
        current_student.full_name = payload.full_name.strip()
    if payload.college is not None:
        current_student.college = payload.college.strip()
    if payload.department is not None:
        current_student.department = payload.department.strip()
    if payload.learning_pace is not None:
        current_student.learning_pace = payload.learning_pace.strip()

    chosen_style = payload.preferred_explanation_style or payload.explanation_style
    if chosen_style is not None:
        current_student.explanation_style = chosen_style.strip()

    if payload.accessibility is not None:
        merged_acc = dict(current_student.accessibility or {})
        merged_acc.update(payload.accessibility)
        current_student.accessibility = merged_acc

    if payload.preferences is not None:
        merged_pref = dict(current_student.preferences or {})
        merged_pref.update(payload.preferences)
        current_student.preferences = merged_pref

    await session.commit()
    await session.refresh(current_student)

    return {
        "message": "Profile and preferences updated successfully.",
        "student": {
            "student_id": current_student.student_code or str(current_student.id),
            "full_name": current_student.full_name,
            "college": current_student.college,
            "department": current_student.department,
            "current_skill_level": current_student.current_skill_level if current_student.has_completed_diagnostic else "Not determined",
            "learning_pace": current_student.learning_pace if current_student.has_completed_diagnostic else "Not determined",
            "explanation_style": current_student.explanation_style,
            "accessibility": current_student.accessibility or {},
            "preferences": current_student.preferences or {},
            "has_completed_diagnostic": current_student.has_completed_diagnostic,
        },
    }


@profile_router.post(
    "/profile/preferences",
    summary="Update learning and accessibility preferences",
    description="Dedicated endpoint for saving student accessibility and explanation style preferences.",
)
async def update_preferences_endpoint(
    payload: UpdateProfileRequest,
    current_student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Dedicated endpoint saving preferences and explanation styles."""
    return await update_profile_endpoint(payload=payload, current_student=current_student, session=session)
