"""Comprehensive End-to-End Corrective Test Suite for EduAdapt (Phases 1-5).

Validates:
1. PHASE 1: Diagnostic-First Access Control
   - Unassessed student cannot access learning endpoints (/api/session/generate, /api/tutor/chat,
     /api/practice/submit, /api/assessment/submit, /api/subtopics/reading/complete,
     /api/subtopics/mastery-check/submit) -> 403 Forbidden with exact diagnostic requirement message.
   - Cross-student IDOR is strictly blocked with 403 Forbidden.

2. PHASE 2: Exact 20-Minute Assessment Timer (1200 seconds)
   - Initial attempt starts with duration_seconds == 1200.
   - Backend computes authoritative deadline (started_at + 1200s).
   - Resuming attempt maintains authoritative deadline and tracks elapsed time.
   - Expired attempt (> 1200s) automatically finalizes and marks attempt completed.
   - Double-submission is idempotent and safe.

3. PHASE 3: Mastery Integrity
   - Unassessed student has 0 completed tests, 0% mastery, and no false "Mastered" badges.
   - Diagnostic completion determines skill level and pace without fabricating topic mastery.

4. PHASE 4: Assessment Count Synchronization
   - Completed diagnostic increments tests_completed to 1.
   - Appears in /api/auth/me recent_attempts and recent_activity.
   - Appears in /api/student/{student_id} tests_completed and recent_attempts.
   - Persists across repeated requests.

5. PHASE 5: Five-Profile Browser Slot Isolation
   - 5 independent students registered and authenticated.
   - Each slot has independent JWT token, identity, diagnostic state, and history.
   - Zero state leakage or cross-contamination across all 5 profiles.
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from eduadapt.api import app
from eduadapt.db.session import get_async_session_factory
from eduadapt.db.models.assessment import DiagnosticAttempt


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def register_student(client: TestClient, name: str, email_prefix: str):
    """Register a new student and return token, student_id, student_code, and payload."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@eduadapt.test"
    payload = {
        "full_name": name,
        "email": email,
        "password": "Password123!",
        "confirm_password": "Password123!",
        "college": "BVRIT",
        "department": "CSE",
        "academic_year": 1,
        "section": "A",
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()
    token = data["access_token"]
    student_id = data["student"]["student_id"]
    student_code = data["student"]["student_code"]
    return token, student_id, student_code, data


# ==============================================================================
# PHASE 1: DIAGNOSTIC-FIRST ACCESS CONTROL
# ==============================================================================

def test_phase1_unassessed_student_gating(client: TestClient):
    """Unassessed student must be blocked from all protected learning endpoints with 403."""
    token, student_id, student_code, _ = register_student(client, "Gated Student", "gated")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify unassessed state
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["student"]["has_completed_diagnostic"] is False

    expected_msg = "Initial Diagnostic Assessment required before accessing learning modules. Please complete the diagnostic assessment first."

    # 1. Lesson generation endpoint
    res = client.post(
        "/api/session/generate",
        headers=headers,
        json={"student_id": student_id, "topic": "Variables and Data Types"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == expected_msg

    # 2. AI Tutor chat endpoint
    res = client.post(
        "/api/tutor/chat",
        headers=headers,
        json={"student_id": student_id, "topic": "Variables and Data Types", "message": "Help me"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == expected_msg

    # 3. Practice checkpoint submission endpoint
    res = client.post(
        "/api/practice/submit",
        headers=headers,
        json={"student_id": student_id, "topic": "Variables and Data Types", "selected_index": 0, "time_taken_ms": 1000},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == expected_msg

    # 4. Assessment submission endpoint
    res = client.post(
        "/api/assessment/submit",
        headers=headers,
        json={"student_id": student_id, "topic": "Variables and Data Types", "selected_index": 0, "time_taken_ms": 1000},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == expected_msg

    # 5. Subtopic reading complete endpoint
    res = client.post(
        "/api/subtopics/reading/complete",
        headers=headers,
        json={"student_id": student_id, "topic": "Variables and Data Types", "subtopic_id": "var_basics"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == expected_msg

    # 6. Subtopic mastery check endpoint
    res = client.post(
        "/api/subtopics/mastery-check/submit",
        headers=headers,
        json={
            "student_id": student_id,
            "topic": "Variables and Data Types",
            "subtopic_id": "var_basics",
            "selected_option": "A",
        },
    )
    assert res.status_code == 403
    assert res.json()["detail"] == expected_msg


def test_phase1_idor_protection(client: TestClient):
    """Student A cannot view or manipulate Student B's learning data."""
    token_a, id_a, _, _ = register_student(client, "Student Alpha", "alpha")
    token_b, id_b, _, _ = register_student(client, "Student Beta", "beta")

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Student A attempts to access Student B's session generate
    res = client.post(
        "/api/session/generate",
        headers=headers_a,
        json={"student_id": id_b, "topic": "Variables and Data Types"},
    )
    assert res.status_code == 403
    assert "Cannot access or alter another student's learning profile" in res.json()["detail"]


# ==============================================================================
# PHASE 2: EXACT 20-MINUTE ASSESSMENT TIMER (1200 SECONDS)
# ==============================================================================

def test_phase2_timer_duration_and_persistence(client: TestClient):
    """Diagnostic assessment must have exact 20-minute (1200 seconds) duration with deadline."""
    token, student_id, _, _ = register_student(client, "Timer Tester", "timer")
    headers = {"Authorization": f"Bearer {token}"}

    # Start diagnostic
    res = client.get("/api/diagnostic/start", headers=headers)
    assert res.status_code == 200
    diag = res.json()

    assert diag["duration_seconds"] == 1200
    assert 1195 <= diag["time_remaining_seconds"] <= 1200
    assert diag["is_expired"] is False
    assert "deadline" in diag
    assert "started_at" in diag

    started_dt = datetime.fromisoformat(diag["started_at"])
    deadline_dt = datetime.fromisoformat(diag["deadline"])
    diff_seconds = (deadline_dt - started_dt).total_seconds()
    assert int(diff_seconds) == 1200

    attempt_id = diag["attempt_id"]

    # Resume attempt via GET /api/diagnostic/start (simulating page reload)
    res_resume = client.get("/api/diagnostic/start", headers=headers)
    assert res_resume.status_code == 200
    resumed = res_resume.json()
    assert resumed["attempt_id"] == attempt_id
    assert resumed["deadline"] == diag["deadline"]
    assert resumed["duration_seconds"] == 1200
    assert resumed["time_remaining_seconds"] <= diag["time_remaining_seconds"]


@pytest.mark.asyncio
async def test_phase2_auto_submission_on_expiration(client: TestClient):
    """If 20 minutes elapse, backend automatically finalizes attempt and marks completed."""
    token, student_id, _, _ = register_student(client, "Expired Student", "expired")
    headers = {"Authorization": f"Bearer {token}"}

    # Start diagnostic
    start_res = client.get("/api/diagnostic/start", headers=headers)
    assert start_res.status_code == 200
    diag = start_res.json()
    attempt_id = diag["attempt_id"]

    # Answer 2 questions
    q0 = diag["questions"][0]["id"]
    q1 = diag["questions"][1]["id"]
    save_res = client.post(
        "/api/diagnostic/save",
        headers=headers,
        json={
            "attempt_id": attempt_id,
            "answers": {q0: "A", q1: "B"},
            "current_index": 2,
        },
    )
    assert save_res.status_code == 200

    # Backdate started_at by 25 minutes (1500 seconds ago) in database
    factory = get_async_session_factory()
    async with factory() as session:
        stmt = select(DiagnosticAttempt).where(DiagnosticAttempt.id == uuid.UUID(attempt_id))
        res = await session.execute(stmt)
        attempt_obj = res.scalar_one()
        attempt_obj.started_at = datetime.now(timezone.utc) - timedelta(minutes=25)
        await session.commit()

    # Calling start now should detect expiration and auto-submit
    expired_res = client.get("/api/diagnostic/start", headers=headers)
    assert expired_res.status_code == 200
    data = expired_res.json()
    assert data["status"] == "completed"
    assert data.get("total_questions") == 25 or "result_summary" in data

    # Verify student is now marked as having completed diagnostic
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["student"]["has_completed_diagnostic"] is True


def test_phase2_idempotent_submission(client: TestClient):
    """Submitting an assessment multiple times must be idempotent and return identical summary."""
    token, student_id, _, _ = register_student(client, "Idempotent Student", "idempotent")
    headers = {"Authorization": f"Bearer {token}"}

    start_res = client.get("/api/diagnostic/start", headers=headers)
    diag = start_res.json()
    attempt_id = diag["attempt_id"]

    answers = {q["id"]: "A" for q in diag["questions"][:5]}
    sub_payload = {
        "attempt_id": attempt_id,
        "answers": answers,
        "time_taken_seconds": 300,
    }

    # First submit
    res1 = client.post("/api/diagnostic/submit", headers=headers, json=sub_payload)
    assert res1.status_code == 200
    raw1 = res1.json()
    summary1 = raw1.get("result_summary", raw1)

    # Second submit (double-click / duplicate request)
    res2 = client.post("/api/diagnostic/submit", headers=headers, json=sub_payload)
    assert res2.status_code == 200
    raw2 = res2.json()
    summary2 = raw2.get("result_summary", raw2)

    assert summary1["total_questions"] == summary2["total_questions"]
    assert summary1["score"] == summary2["score"]
    assert summary1["learning_level"] == summary2["learning_level"]


# ==============================================================================
# PHASE 3: MASTERY INTEGRITY
# ==============================================================================

def test_phase3_mastery_integrity_before_and_after_diagnostic(client: TestClient):
    """Unassessed student has 0 tests and no false 'Mastered' topics."""
    token, student_id, student_code, _ = register_student(client, "Integrity Student", "integrity")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Check profile before diagnostic
    prof_res = client.get(f"/api/student/{student_id}", headers=headers)
    assert prof_res.status_code == 200
    prof = prof_res.json()
    assert prof["has_completed_diagnostic"] is False
    assert prof["current_skill_level"] == "Not determined"
    assert prof["learning_pace"] == "Not determined"
    assert prof["tests_completed"] == 0
    assert prof["recent_attempts"] == []
    assert prof["recent_activity"] is None

    # 2. Complete diagnostic
    start_res = client.get("/api/diagnostic/start", headers=headers)
    diag = start_res.json()
    attempt_id = diag["attempt_id"]
    answers = {q["id"]: "A" for q in diag["questions"]}

    client.post(
        "/api/diagnostic/submit",
        headers=headers,
        json={"attempt_id": attempt_id, "answers": answers, "time_taken_seconds": 450},
    )

    # 3. Check profile after diagnostic
    post_res = client.get(f"/api/student/{student_id}", headers=headers)
    assert post_res.status_code == 200
    post_prof = post_res.json()
    assert post_prof["has_completed_diagnostic"] is True
    assert post_prof["current_skill_level"] in ("Beginner", "Intermediate", "Advanced")
    assert post_prof["learning_pace"] in ("Deliberate", "Moderate", "Fast")
    assert post_prof["tests_completed"] == 1

    # Check roadmap: stages exist now, but topics are unlocked in progression, not all 'Mastered'
    road_res = client.get("/api/roadmap/me", headers=headers)
    assert road_res.status_code == 200
    road = road_res.json()
    assert road["has_completed_diagnostic"] is True
    assert len(road["stages"]) > 0
    statuses = [s["status"] for s in road["stages"]]
    assert "current" in statuses
    assert "mastered" not in statuses  # Diagnostic does NOT automatically grant 'mastered' status


# ==============================================================================
# PHASE 4: ASSESSMENT COUNT SYNCHRONIZATION
# ==============================================================================

def test_phase4_assessment_count_synchronization(client: TestClient):
    """Submitting diagnostic synchronizes tests_completed and populates recent activity."""
    token, student_id, student_code, _ = register_student(client, "Sync Student", "sync")
    headers = {"Authorization": f"Bearer {token}"}

    # Verify initial tests_completed == 0
    me_before = client.get("/api/auth/me", headers=headers).json()
    assert me_before["student"]["tests_completed"] == 0
    assert me_before["student"]["recent_attempts"] == []

    # Complete diagnostic
    diag = client.get("/api/diagnostic/start", headers=headers).json()
    answers = {q["id"]: "B" for q in diag["questions"]}
    client.post(
        "/api/diagnostic/submit",
        headers=headers,
        json={"attempt_id": diag["attempt_id"], "answers": answers, "time_taken_seconds": 600},
    )

    # Check /api/auth/me
    me_after = client.get("/api/auth/me", headers=headers).json()
    assert me_after["student"]["tests_completed"] == 1
    assert me_after["student"]["diagnostic_completed_count"] == 1
    assert len(me_after["student"]["recent_attempts"]) == 1
    assert me_after["student"]["recent_attempts"][0]["title"] == "Initial Diagnostic Assessment"
    assert me_after["student"]["recent_activity"] is not None

    # Check /api/student/{student_id} (used by dashboard / learning twin)
    twin_res = client.get(f"/api/student/{student_id}", headers=headers).json()
    assert twin_res["tests_completed"] == 1
    assert twin_res["diagnostic_completed_count"] == 1
    assert len(twin_res["recent_attempts"]) == 1
    assert twin_res["recent_attempts"][0]["title"] == "Initial Diagnostic Assessment"

    # Check /api/student/{student_code} lookup by student_code
    code_res = client.get(f"/api/student/{student_code}", headers=headers).json()
    assert code_res["tests_completed"] == 1


# ==============================================================================
# PHASE 5: FIVE-PROFILE BROWSER SLOT ISOLATION
# ==============================================================================

def test_phase5_five_profile_slots_isolation(client: TestClient):
    """5 profile slots maintain independent authentication, metrics, and records."""
    profiles = [
        {"name": "Slot 1 Student", "prefix": "slot1", "choice": "A", "time": 300},
        {"name": "Slot 2 Student", "prefix": "slot2", "choice": "B", "time": 500},
        {"name": "Slot 3 Student", "prefix": "slot3", "choice": "C", "time": 700},
        {"name": "Slot 4 Student", "prefix": "slot4", "choice": "D", "time": 400},
        {"name": "Slot 5 Student", "prefix": "slot5", "choice": "A", "time": 900},
    ]

    tokens = []
    student_ids = []

    # 1. Register all 5 students
    for p in profiles:
        token, s_id, s_code, data = register_student(client, p["name"], p["prefix"])
        tokens.append(token)
        student_ids.append(s_id)

    assert len(set(tokens)) == 5
    assert len(set(student_ids)) == 5

    # 2. Complete diagnostic for each with distinct answers and times
    for i, p in enumerate(profiles):
        headers = {"Authorization": f"Bearer {tokens[i]}"}
        diag = client.get("/api/diagnostic/start", headers=headers).json()
        assert diag["status"] == "in_progress"
        answers = {q["id"]: p["choice"] for q in diag["questions"]}
        sub_res = client.post(
            "/api/diagnostic/submit",
            headers=headers,
            json={"attempt_id": diag["attempt_id"], "answers": answers, "time_taken_seconds": p["time"]},
        )
        assert sub_res.status_code == 200

    # 3. Verify total isolation across all 5 profiles
    for i, p in enumerate(profiles):
        headers = {"Authorization": f"Bearer {tokens[i]}"}
        me = client.get("/api/auth/me", headers=headers).json()
        assert me["student"]["full_name"] == p["name"]
        assert me["student"]["student_id"] == student_ids[i]
        assert me["student"]["has_completed_diagnostic"] is True
        assert me["student"]["tests_completed"] == 1
        assert len(me["student"]["recent_attempts"]) == 1

        # Verify Student i cannot access Student j's data
        other_idx = (i + 1) % 5
        other_id = student_ids[other_idx]
        idor_res = client.post(
            "/api/session/generate",
            headers=headers,
            json={"student_id": other_id, "topic": "Variables and Data Types"},
        )
        assert idor_res.status_code == 403
        assert "Cannot access or alter another student's learning profile" in idor_res.json()["detail"]
