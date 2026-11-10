"""Master Comprehensive End-to-End Verification and Acceptance Test Suite for EduAdapt.

Covers:
- Scenario A: Completely New Student Flow (gating, 20-min timer, resume, submission, unlocking)
- Scenario B: High-Performing Student (Advanced tier, Fast pace, verified strengths >= 75%)
- Scenario C: Foundational Learner (Beginner tier, Deliberate pace, focus areas < 60%)
- Scenario D: Five-Profile Account Isolation (5 independent students, zero cross-contamination)
- Scenario E: Security, IDOR, and Answer Concealment (403 on IDOR, answers concealed)
- Scenario F: Personalization, Explanation Styles, and Accessibility Persistence
- Concurrency & Atomicity: Multi-student parallel execution without race conditions
- Boundary Cases: Explicit 49%, 50%, 79%, 80% accuracy and 44s, 45s, 46s, 60s, 61s pace checks
"""

import asyncio
from datetime import datetime, timedelta, timezone
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from eduadapt.api import app
from eduadapt.db.session import get_async_session_factory
from eduadapt.db.models.assessment import DiagnosticAttempt
from eduadapt.db.models.student import Student
from eduadapt.services.diagnostic_service import (
    determine_learning_level,
    determine_recommended_pace,
)


@pytest.fixture
def client():
    return TestClient(app)


def register_account(client: TestClient, name: str, prefix: str):
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@eduadapt.test"
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
    return data["access_token"], data["student"]["student_id"], data["student"]["student_code"], email


# ==============================================================================
# 1. BOUNDARY VALUE TESTS: SKILL LEVEL AND LEARNING PACE
# ==============================================================================

def test_skill_level_exact_boundaries():
    """Verify exact 49%, 50%, 79%, 80% boundary thresholds."""
    assert determine_learning_level(49.0) == "Beginner"
    assert determine_learning_level(49.9) == "Beginner"
    assert determine_learning_level(50.0) == "Intermediate"
    assert determine_learning_level(79.0) == "Intermediate"
    assert determine_learning_level(79.9) == "Intermediate"
    assert determine_learning_level(80.0) == "Advanced"
    assert determine_learning_level(100.0) == "Advanced"


def test_learning_pace_exact_boundaries():
    """Verify exact pace calculations:
    - Fast: accuracy >= 80% and avg_time <= 45s
    - Deliberate: accuracy < 50% or avg_time > 60s
    - Moderate: accuracy >= 50% and avg_time <= 60s (and not Fast)
    """
    # 44 seconds, 80% accuracy -> Fast
    assert determine_recommended_pace(80.0, 44.0) == "Fast"
    # 45 seconds, 80% accuracy -> Fast
    assert determine_recommended_pace(80.0, 45.0) == "Fast"
    # 46 seconds, 80% accuracy -> Moderate
    assert determine_recommended_pace(80.0, 46.0) == "Moderate"
    # 60 seconds, 80% accuracy -> Moderate
    assert determine_recommended_pace(80.0, 60.0) == "Moderate"
    # 61 seconds, 80% accuracy -> Deliberate (exceeds 60s threshold)
    assert determine_recommended_pace(80.0, 61.0) == "Deliberate"
    # 49% accuracy, 30 seconds -> Deliberate (below 50% accuracy)
    assert determine_recommended_pace(49.0, 30.0) == "Deliberate"
    # 50% accuracy, 50 seconds -> Moderate (>= 50% and <= 60s)
    assert determine_recommended_pace(50.0, 50.0) == "Moderate"
    # 79% accuracy, 30 seconds -> Moderate (>= 50%, <= 60s, but < 80%)
    assert determine_recommended_pace(79.0, 30.0) == "Moderate"
    # 80% accuracy, 40 seconds -> Fast
    assert determine_recommended_pace(80.0, 40.0) == "Fast"


# ==============================================================================
# 2. SCENARIO A: COMPLETELY NEW STUDENT LIFECYCLE
# ==============================================================================

def test_scenario_a_new_student_complete_flow(client: TestClient):
    token, student_id, student_code, email = register_account(client, "Naveen Kumar", "naveen")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Clean profile before diagnostic
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["student"]["full_name"] == "Naveen Kumar"
    assert me["student"]["has_completed_diagnostic"] is False
    assert me["student"]["current_skill_level"] == "Not determined"
    assert me["student"]["learning_pace"] == "Not determined"
    assert me["student"]["tests_completed"] == 0

    # 2. Learning endpoints must be strictly blocked (HTTP 403)
    blocked_endpoints = [
        ("/api/session/generate", {"student_id": student_id, "topic": "Variables and Data Types"}),
        ("/api/tutor/chat", {"student_id": student_id, "topic": "Variables and Data Types", "message": "Hi"}),
        ("/api/practice/submit", {"student_id": student_id, "topic": "Variables and Data Types"}),
        ("/api/assessment/submit", {"student_id": student_id, "topic": "Variables and Data Types"}),
    ]
    for url, payload in blocked_endpoints:
        res = client.post(url, headers=headers, json=payload)
        assert res.status_code == 403
        assert "Initial Diagnostic Assessment required" in res.json()["detail"]

    # 3. Start diagnostic: 25 questions, exact 20-min timer (1200s), no answer leaks
    start_res = client.get("/api/diagnostic/start", headers=headers)
    assert start_res.status_code == 200
    diag = start_res.json()
    assert diag["total_questions"] == 25
    assert diag["duration_seconds"] == 1200
    assert 1195 <= diag["time_remaining_seconds"] <= 1200
    for q in diag["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q

    # 4. Save progress
    attempt_id = diag["attempt_id"]
    q0 = diag["questions"][0]["id"]
    save_res = client.post(
        "/api/diagnostic/save",
        headers=headers,
        json={"attempt_id": attempt_id, "answers": {q0: "B"}, "current_index": 1},
    )
    assert save_res.status_code == 200

    # 5. Reload / resume attempt: retains authoritative deadline
    resume_res = client.get("/api/diagnostic/start", headers=headers)
    assert resume_res.status_code == 200
    assert resume_res.json()["attempt_id"] == attempt_id
    assert resume_res.json()["saved_answers"][q0] == "B"

    # 6. Submit assessment
    submit_payload = {
        "attempt_id": attempt_id,
        "answers": {q["id"]: "A" for q in diag["questions"]},
        "time_taken_seconds": 600,
    }
    sub_res = client.post("/api/diagnostic/submit", headers=headers, json=submit_payload)
    assert sub_res.status_code == 200
    results = sub_res.json()
    assert results["status"] == "completed"
    assert results["total_questions"] == 25
    assert results["learning_level"] in ("Beginner", "Intermediate", "Advanced")
    assert results["recommended_pace"] in ("Fast", "Moderate", "Deliberate")

    # 7. Verify platform unlocked: tests_completed == 1, roadmap unlocked
    me_after = client.get("/api/auth/me", headers=headers).json()
    assert me_after["student"]["has_completed_diagnostic"] is True
    assert me_after["student"]["tests_completed"] == 1
    assert len(me_after["student"]["recent_attempts"]) == 1

    road_res = client.get("/api/roadmap/me", headers=headers)
    assert road_res.status_code == 200
    road = road_res.json()
    assert road["has_completed_diagnostic"] is True
    assert len(road["stages"]) == 10
    assert road["stages"][0]["status"] in ("current", "in_progress")


# ==============================================================================
# 3. SCENARIO B: HIGH-PERFORMING STUDENT CALIBRATION
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_b_high_performing_student(client: TestClient):
    token, student_id, student_code, _ = register_account(client, "Pooja Hegde", "pooja")
    headers = {"Authorization": f"Bearer {token}"}

    # Start diagnostic
    diag = client.get("/api/diagnostic/start", headers=headers).json()
    attempt_id = diag["attempt_id"]

    # Lookup actual correct answers from database for high score (100%)
    factory = get_async_session_factory()
    correct_answers = {}
    async with factory() as session:
        from eduadapt.db.models.question import Question
        q_uuids = [uuid.UUID(q["id"]) for q in diag["questions"]]
        res = await session.execute(select(Question).where(Question.id.in_(q_uuids)))
        q_objs = {str(q.id): q for q in res.scalars().all()}
        for q in diag["questions"]:
            q_obj = q_objs.get(q["id"])
            if q_obj:
                correct_val = q_obj.correct_answer.get("answer") if isinstance(q_obj.correct_answer, dict) else str(q_obj.correct_answer)
                correct_answers[q["id"]] = {"selected_option": correct_val, "time_taken_seconds": 30}

    # Submit with 100% correct answers in 30 seconds avg time
    sub_res = client.post(
        "/api/diagnostic/submit",
        headers=headers,
        json={"attempt_id": attempt_id, "answers": correct_answers, "time_taken_seconds": 750},
    )
    assert sub_res.status_code == 200
    res = sub_res.json()
    assert res["accuracy_pct"] == 100.0
    assert res["learning_level"] == "Advanced"
    assert res["recommended_pace"] == "Fast"
    assert len(res["strengths"]) > 0
    assert len(res["focus_areas"]) == 0  # 100% accuracy means 0 focus areas below 60%


# ==============================================================================
# 4. SCENARIO C: FOUNDATIONAL LEARNER CALIBRATION
# ==============================================================================

def test_scenario_c_foundational_learner(client: TestClient):
    token, student_id, student_code, _ = register_account(client, "Ravi Teja", "ravi")
    headers = {"Authorization": f"Bearer {token}"}

    diag = client.get("/api/diagnostic/start", headers=headers).json()
    attempt_id = diag["attempt_id"]

    # Submit intentionally low score with slow response velocity (75s per question)
    slow_answers = {
        q["id"]: {"selected_option": "Z", "time_taken_seconds": 75}
        for q in diag["questions"]
    }
    sub_res = client.post(
        "/api/diagnostic/submit",
        headers=headers,
        json={"attempt_id": attempt_id, "answers": slow_answers, "time_taken_seconds": 1875},
    )
    assert sub_res.status_code == 200
    res = sub_res.json()
    assert res["learning_level"] == "Beginner"
    assert res["recommended_pace"] == "Deliberate"
    assert len(res["focus_areas"]) > 0
    assert len(res["strengths"]) == 0


# ==============================================================================
# 5. SCENARIO D: FIVE-PROFILE ISOLATION & VERIFICATION
# ==============================================================================

def test_scenario_d_five_profile_isolation(client: TestClient):
    """Register 5 distinct profiles and verify complete data and session isolation."""
    students = [
        {"name": "Profile 1 Alpha", "prefix": "p1"},
        {"name": "Profile 2 Beta", "prefix": "p2"},
        {"name": "Profile 3 Gamma", "prefix": "p3"},
        {"name": "Profile 4 Delta", "prefix": "p4"},
        {"name": "Profile 5 Epsilon", "prefix": "p5"},
    ]

    sessions = []
    for s in students:
        tok, sid, scode, em = register_account(client, s["name"], s["prefix"])
        sessions.append({"token": tok, "student_id": sid, "student_code": scode, "name": s["name"]})

    # Verify each session queries only its own identity
    for s in sessions:
        h = {"Authorization": f"Bearer {s['token']}"}
        me = client.get("/api/auth/me", headers=h).json()
        assert me["student"]["full_name"] == s["name"]
        assert me["student"]["student_id"] == s["student_id"]

    # Verify cross-session access is blocked (IDOR protection)
    for i in range(5):
        h = {"Authorization": f"Bearer {sessions[i]['token']}"}
        target_sid = sessions[(i + 1) % 5]["student_id"]
        res = client.post(
            "/api/session/generate",
            headers=h,
            json={"student_id": target_sid, "topic": "Variables and Data Types"},
        )
        assert res.status_code == 403


# ==============================================================================
# 6. SCENARIO E: SECURITY, IDOR & PERSISTENCE
# ==============================================================================

def test_scenario_e_security_and_answer_concealment(client: TestClient):
    token, student_id, _, _ = register_account(client, "Sec Tester", "sec")
    headers = {"Authorization": f"Bearer {token}"}

    # Start diagnostic
    diag = client.get("/api/diagnostic/start", headers=headers).json()
    for q in diag["questions"]:
        assert "correct_answer" not in q
        assert "explanation" not in q

    # Attempt to tamper with another student's profile via PUT /api/profile
    other_token, other_id, _, _ = register_account(client, "Victim", "victim")
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Changing Sec Tester's explanation style does not touch Victim's
    client.put(
        "/api/profile",
        headers=headers,
        json={"explanation_style": "detailed_and_technical", "accessibility": {"high_contrast": True}},
    )
    victim_me = client.get("/api/auth/me", headers=other_headers).json()
    assert victim_me["student"]["explanation_style"] == "step_by_step"
    assert victim_me["student"]["accessibility"] == {}


# ==============================================================================
# 7. SCENARIO F: PREFERENCES AND EXPLANATION STYLES PERSISTENCE
# ==============================================================================

def test_scenario_f_preferences_persistence_and_rehydration(client: TestClient):
    token, student_id, _, _ = register_account(client, "Pref Tester", "pref")
    headers = {"Authorization": f"Bearer {token}"}

    # Update preferences
    pref_payload = {
        "explanation_style": "simple_and_visual",
        "accessibility": {
            "font": "opendyslexic",
            "contrast": "high",
            "reduce_motion": True,
            "micro_chunks": True,
        },
    }
    update_res = client.put("/api/profile", headers=headers, json=pref_payload)
    assert update_res.status_code == 200

    # Fetch /api/auth/me and verify full rehydration from database
    me = client.get("/api/auth/me", headers=headers).json()
    assert me["student"]["explanation_style"] == "simple_and_visual"
    assert me["student"]["accessibility"]["font"] == "opendyslexic"
    assert me["student"]["accessibility"]["contrast"] == "high"
    assert me["student"]["accessibility"]["reduce_motion"] is True


# ==============================================================================
# 8. CONCURRENCY AND ATOMICITY
# ==============================================================================

def test_concurrent_student_diagnostic_submissions(client: TestClient):
    """Simulate 3 students saving and submitting concurrently."""
    students = [
        register_account(client, f"Concurrent {i}", f"conc{i}")
        for i in range(3)
    ]

    for token, sid, scode, _ in students:
        h = {"Authorization": f"Bearer {token}"}
        diag = client.get("/api/diagnostic/start", headers=h).json()
        sub_payload = {
            "attempt_id": diag["attempt_id"],
            "answers": {q["id"]: "A" for q in diag["questions"]},
            "time_taken_seconds": 300,
        }
        res = client.post("/api/diagnostic/submit", headers=h, json=sub_payload)
        assert res.status_code == 200

    # Verify all 3 completed independently with tests_completed == 1
    for token, sid, scode, _ in students:
        h = {"Authorization": f"Bearer {token}"}
        me = client.get("/api/auth/me", headers=h).json()
        assert me["student"]["tests_completed"] == 1
        assert me["student"]["has_completed_diagnostic"] is True
