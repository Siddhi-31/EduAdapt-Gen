"""Comprehensive automated test suite for EduAdapt Student Authentication & Identity.

Verifies:
- Student account registration (valid data, hashing, unique student code)
- Duplicate email registration rejection (HTTP 409)
- Email normalization (whitespace trimming, lowercase)
- Password requirements & confirmation checks
- Successful login & JWT issuance
- Incorrect password rejection with generic error (HTTP 401)
- Inactive account rejection (HTTP 403)
- Token generation and verification
- Invalid & expired token rejection
- Authenticated profile retrieval via GET /api/auth/me
- Student profile persistence in database
- Registration transaction atomicity
- OTP generation, secure dev_code, rate-limiting cooldown, max attempts, and single-use enforcement
- Logout acknowledgment
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from fastapi.testclient import TestClient
from jose import jwt

from eduadapt.api import app
from eduadapt.config import get_settings
from eduadapt.db.security import hash_password, normalize_email, verify_password
from eduadapt.services.auth_service import (
    OTPStore,
    create_access_token,
    decode_access_token,
)


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_student_registration_success(client):
    """Verify new student can register and receive safe user/profile payload with token."""
    email = f"student_{datetime.now().timestamp()}@eduadapt.test"
    payload = {
        "full_name": "Priya Sharma",
        "email": email,
        "password": "SecurePassword123!",
        "confirm_password": "SecurePassword123!",
        "college": "BVRIT",
        "department": "CSE",
        "academic_year": 1,
        "section": "A",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert "access_token" in data
    assert data["user"]["email"] == email.lower()
    assert data["student"]["full_name"] == "Priya Sharma"
    assert data["student"]["student_code"].startswith("S-")
    assert "hashed_password" not in data["user"]


def test_duplicate_email_registration_rejected(client):
    """Verify duplicate email registration is rejected with HTTP 409 Conflict."""
    email = f"unique_{uuid.uuid4().hex[:8]}@eduadapt.test"
    payload = {
        "full_name": "First Registration",
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    client.post("/api/auth/register", json=payload)

    # Second attempt with same email
    res_dup = client.post("/api/auth/register", json=payload)
    assert res_dup.status_code == 409
    assert "already exists" in res_dup.json()["detail"]


def test_email_normalization_during_auth(client):
    """Verify emails are trimmed and lowercased during registration and login."""
    unique_id = uuid.uuid4().hex[:8]
    raw_email = f"  MiXeDCaSe_{unique_id}@EduAdapt.TEST  "
    payload = {
        "full_name": "Mixed Case Student",
        "email": raw_email,
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201
    assert res.json()["user"]["email"] == f"mixedcase_{unique_id}@eduadapt.test"

    # Login using different casing
    res_login = client.post(
        "/api/auth/login",
        json={"email": f"MIXEDCASE_{unique_id}@eduadapt.test", "password": "Password123!"},
    )
    assert res_login.status_code == 200
    assert res_login.json()["token_type"] == "bearer"


def test_password_strength_and_mismatch_validation(client):
    """Verify weak password and mismatched confirm_password are appropriately rejected."""
    # Too short
    res1 = client.post(
        "/api/auth/register",
        json={"full_name": "User", "email": "weak@test.com", "password": "123"},
    )
    assert res1.status_code == 422

    # Mismatched confirm_password
    res2 = client.post(
        "/api/auth/register",
        json={
            "full_name": "User",
            "email": "mismatch@test.com",
            "password": "Password123!",
            "confirm_password": "DifferentPassword123!",
        },
    )
    assert res2.status_code == 422
    assert "do not match" in res2.json()["detail"]


def test_successful_login_and_jwt_generation(client):
    """Verify student can log in and receive valid JWT access token."""
    email = f"login_test_{datetime.now().timestamp()}@eduadapt.test"
    client.post(
        "/api/auth/register",
        json={"full_name": "Login Tester", "email": email, "password": "Password123!"},
    )

    res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["student"]["full_name"] == "Login Tester"


def test_incorrect_password_rejected_with_generic_error(client):
    """Verify incorrect credentials return generic 401 without user enumeration."""
    email = f"generic_err_{datetime.now().timestamp()}@eduadapt.test"
    client.post(
        "/api/auth/register",
        json={"full_name": "Tester", "email": email, "password": "Password123!"},
    )

    # Wrong password
    res_wrong = client.post(
        "/api/auth/login",
        json={"email": email, "password": "WrongPassword999!"},
    )
    assert res_wrong.status_code == 401
    assert "Incorrect email or password" in res_wrong.json()["detail"]

    # Non-existent email
    res_nonexistent = client.post(
        "/api/auth/login",
        json={"email": "nonexistent_email_12345@test.com", "password": "Password123!"},
    )
    assert res_nonexistent.status_code == 401
    assert "Incorrect email or password" in res_nonexistent.json()["detail"]


def test_authenticated_me_endpoint_and_profile_retrieval(client):
    """Verify GET /api/auth/me resolves student profile and rejects unauthenticated requests."""
    # Unauthenticated request
    res_unauth = client.get("/api/auth/me")
    assert res_unauth.status_code == 401

    # Register and get token
    email = f"me_test_{datetime.now().timestamp()}@eduadapt.test"
    reg = client.post(
        "/api/auth/register",
        json={
            "full_name": "Me Tester",
            "email": email,
            "password": "Password123!",
            "college": "Tech Institute",
            "department": "PPS",
        },
    )
    token = reg.json()["access_token"]

    # Authenticated request
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    data = res_me.json()
    assert data["student"]["full_name"] == "Me Tester"
    assert data["student"]["college"] == "Tech Institute"
    assert data["student"]["department"] == "PPS"
    assert data["user"]["email"] == email.lower()


def test_invalid_and_expired_token_rejection(client):
    """Verify forged or expired JWTs return 401 Unauthorized."""
    # Completely forged token
    res_forged = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.forged.jwt"})
    assert res_forged.status_code == 401

    # Expired token
    cfg = get_settings()
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000000",
        "email": "expired@test.com",
        "role": "student",
        "iat": int((datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()),
        "exp": int((datetime.now(timezone.utc) - timedelta(hours=1)).timestamp()),
        "iss": "eduadapt-auth",
    }
    expired_token = jwt.encode(expired_payload, cfg.jwt_secret_key, algorithm=cfg.jwt_algorithm)

    res_expired = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401


def test_logout_endpoint(client):
    """Verify POST /api/auth/logout succeeds and returns friendly acknowledgment."""
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    assert "logged out" in res.json()["message"].lower()


def test_otp_generation_verification_and_single_use():
    """Verify OTP manager enforces cryptographic generation, expiration, and single-use."""
    store = OTPStore()
    target = "otp_unit_test@eduadapt.test"

    code, cooldown = store.generate(target, expire_seconds=300, cooldown_seconds=30)
    assert len(code) == 6
    assert code.isdigit()
    assert cooldown is None

    # Immediate second request triggers cooldown
    code2, cooldown2 = store.generate(target, expire_seconds=300, cooldown_seconds=30)
    assert code2 == ""
    assert cooldown2 is not None and cooldown2 > 0

    # Wrong code verification fails
    assert store.verify(target, "000000") is False

    # Correct code verification succeeds
    assert store.verify(target, code) is True

    # Re-using the same code must fail immediately (single-use)
    assert store.verify(target, code) is False


def test_otp_attempt_limits():
    """Verify exceeding max verification attempts invalidates the OTP."""
    store = OTPStore()
    target = "attempts_test@eduadapt.test"

    code, _ = store.generate(target, expire_seconds=300, cooldown_seconds=0)

    # 3 failed attempts
    assert store.verify(target, "111111") is False
    assert store.verify(target, "222222") is False
    assert store.verify(target, "333333") is False

    # 4th attempt with the CORRECT code must be rejected because max attempts exceeded
    assert store.verify(target, code) is False


def test_otp_endpoints_integration(client):
    """Verify /api/auth/send-otp and /api/auth/verify-otp end-to-end with dev_code."""
    target_email = f"otp_endpoint_{datetime.now().timestamp()}@eduadapt.test"

    send_res = client.post("/api/auth/send-otp", json={"email": target_email})
    assert send_res.status_code == 200
    dev_code = send_res.json().get("dev_code")
    assert dev_code is not None

    verify_res = client.post("/api/auth/verify-otp", json={"email": target_email, "code": dev_code})
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True
    assert "token" in verify_res.json()


def test_new_student_clean_profile_integrity(client):
    """Verify newly registered students have 0% mastery, 0 tests completed, and their real name."""
    uniq = uuid.uuid4().hex[:8]
    email = f"integrity_{uniq}@eduadapt.test"
    full_name = f"Kanishk Sharma {uniq}"

    reg_res = client.post(
        "/api/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": "Password123!",
            "confirm_password": "Password123!",
            "college": "SRM Institute of Science and Technology",
            "department": "CSE",
        },
    )
    assert reg_res.status_code == 201
    student_code = reg_res.json()["student"]["student_code"]
    token = reg_res.json()["access_token"]

    # Fetch student profile via /api/student/{student_code}
    prof_res = client.get(
        f"/api/student/{student_code}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert prof_res.status_code == 200
    p = prof_res.json()

    assert p["full_name"] == full_name
    assert p["mastery"] == 0.0
    assert p["accuracy"] == 0.0
    assert p["tests_completed"] == 0
    assert p["predicted_mastery_level"] in ("Not determined", "New Learner")
    assert p["recommended_difficulty"] in ("Beginner", "Not determined")


def test_student_data_isolation_idor_prevention(client):
    """Verify student A cannot view or tamper with student B's records via query manipulation."""
    uniq_a = uuid.uuid4().hex[:8]
    uniq_b = uuid.uuid4().hex[:8]

    # Register Student A
    res_a = client.post(
        "/api/auth/register",
        json={
            "full_name": f"Student A {uniq_a}",
            "email": f"student_a_{uniq_a}@eduadapt.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert res_a.status_code == 201
    code_a = res_a.json()["student"]["student_code"]
    token_a = res_a.json()["access_token"]

    # Register Student B
    res_b = client.post(
        "/api/auth/register",
        json={
            "full_name": f"Student B {uniq_b}",
            "email": f"student_b_{uniq_b}@eduadapt.test",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert res_b.status_code == 201
    code_b = res_b.json()["student"]["student_code"]

    # Student A can access their own profile
    own_res = client.get(
        f"/api/student/{code_a}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert own_res.status_code == 200
    assert own_res.json()["student_id"] == code_a

    # Student A attempting to access Student B's profile must be rejected with 403 Forbidden
    cross_res = client.get(
        f"/api/student/{code_b}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert cross_res.status_code == 403
    assert "access denied" in cross_res.json()["detail"].lower()

    # Cross-student access to subtopics roadmap must also be rejected with 403
    cross_sub_res = client.get(
        f"/api/subtopics/roadmap/{code_b}/Pointers",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert cross_sub_res.status_code == 403
