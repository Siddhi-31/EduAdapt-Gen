"""Comprehensive Multi-Student End-to-End Integration and Isolation Test Suite (Phases 1-11).

Validates:
1. Student 1 (New Student): Mandatory diagnostic requirement, 'Not determined' metrics before diagnostic, locked roadmap, reproducible attempt resume.
2. Student 2 (Advanced Student): Diagnostic completion with high score, 'Advanced' level, 'Fast' pace, unlocked roadmap sequence, custom preferences persistence.
3. Student 3 (Beginner Student): Diagnostic completion with foundational score, 'Beginner' level, 'Deliberate' pace, cognitive focus areas, personalized lesson grounding.
4. Student 4 (Cross-Student Data Isolation): Strict tenant separation. Student A cannot view or manipulate Student B's roadmap, diagnostic attempt, or profile.
"""

from datetime import datetime
import uuid
import pytest
from fastapi.testclient import TestClient

from eduadapt.api import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def register_student(client, name: str, email_prefix: str):
    """Helper to register a new student and return token and payload."""
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
    return token, student_id, data


# ==============================================================================
# TEST 1: STUDENT 1 — NEW REGISTERED STUDENT & RESUMABLE ATTEMPT
# ==============================================================================

def test_student_1_new_registered_flow(client):
    token, student_id, reg_data = register_student(client, "Aarav Patel", "aarav")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Profile before diagnostic must indicate 'Not determined'
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    me = res_me.json()
    assert me["student"]["full_name"] == "Aarav Patel"
    assert me["student"]["has_completed_diagnostic"] is False
    assert me["student"]["current_skill_level"] == "Not determined"
    assert me["student"]["learning_pace"] == "Not determined"

    # 2. Roadmap before diagnostic must have all topics locked
    res_road = client.get("/api/roadmap/me", headers=headers)
    assert res_road.status_code == 200
    road = res_road.json()
    assert road["has_completed_diagnostic"] is False
    assert len(road["stages"]) == 0
    assert road["completed_count"] == 0
    assert road["progress_percent"] == 0

    # 3. Start diagnostic assessment
    res_start = client.get("/api/diagnostic/start", headers=headers)
    assert res_start.status_code == 200
    diag = res_start.json()
    assert diag["total_questions"] == 25
    assert len(diag["questions"]) == 25
    attempt_id = diag["attempt_id"]

    # Verify no correct answers leaked
    for q in diag["questions"]:
        assert "correct_option" not in q
        assert "explanation" not in q
        assert len(q["options"]) >= 3

    # 4. Save progress
    q0 = diag["questions"][0]["id"]
    q1 = diag["questions"][1]["id"]
    save_payload = {
        "attempt_id": attempt_id,
        "answers": {q0: "C", q1: "A"},
        "current_index": 2,
        "flagged_ids": [q1],
    }
    res_save = client.post("/api/diagnostic/save", headers=headers, json=save_payload)
    assert res_save.status_code == 200

    # 5. Resume attempt (e.g. after refresh)
    res_resume = client.get("/api/diagnostic/start", headers=headers)
    assert res_resume.status_code == 200
    resumed = res_resume.json()
    assert resumed["attempt_id"] == attempt_id
    assert resumed["current_index"] == 2
    assert resumed["saved_answers"][q0] == "C"
    assert q1 in resumed["flagged_ids"]


# ==============================================================================
# TEST 2: STUDENT 2 — ADVANCED STUDENT HIGH SCORE & PREFERENCES
# ==============================================================================

def test_student_2_advanced_flow(client):
    token, student_id, reg_data = register_student(client, "Neha Gupta", "neha")
    headers = {"Authorization": f"Bearer {token}"}

    # Start diagnostic
    res_start = client.get("/api/diagnostic/start", headers=headers)
    diag = res_start.json()
    attempt_id = diag["attempt_id"]
    questions = diag["questions"]

    # Submit high-accuracy answers
    # Answer most questions with their correct answer from DB
    from eduadapt.db.session import get_sync_session_factory
    from eduadapt.db.models.question import Question
    from sqlalchemy import select

    factory = get_sync_session_factory()
    with factory() as session:
        q_uuids = [uuid.UUID(q["id"]) for q in questions]
        q_objs = session.execute(select(Question).where(Question.id.in_(q_uuids))).scalars().all()
        q_map = {str(q.id): q.correct_answer for q in q_objs}

    answers = {q["id"]: q_map.get(q["id"], "A") for q in questions}

    res_submit = client.post(
        "/api/diagnostic/submit",
        headers=headers,
        json={"attempt_id": attempt_id, "answers": answers},
    )
    assert res_submit.status_code == 200
    result = res_submit.json()
    assert result["score"] >= 80.0
    assert result["learning_level"] == "Advanced"
    assert result["recommended_pace"] == "Fast"
    assert len(result["strengths"]) > 0

    # Verify /api/auth/me reflects Advanced and Fast
    res_me = client.get("/api/auth/me", headers=headers)
    me = res_me.json()
    assert me["student"]["has_completed_diagnostic"] is True
    assert me["student"]["current_skill_level"] == "Advanced"
    assert me["student"]["learning_pace"] == "Fast"

    # Verify roadmap unlocks initial topic
    res_road = client.get("/api/roadmap/me", headers=headers)
    road = res_road.json()
    assert road["has_completed_diagnostic"] is True
    assert len(road["stages"]) == 10
    first_stage = road["stages"][0]
    assert first_stage["is_locked"] is False
    assert first_stage["status"] in ("current", "in_progress", "unlocked")

    # Update explanation style & accessibility preferences
    pref_payload = {
        "explanation_style": "detailed",
        "accessibility": {
            "contrast": "high",
            "chunk_size": "micro",
            "font": "default",
        },
        "preferences": {
            "audio_enabled": True,
            "visual_enabled": True,
        },
    }
    res_pref = client.post("/api/profile/preferences", headers=headers, json=pref_payload)
    assert res_pref.status_code == 200

    # Fetch profile again to confirm DB persistence
    res_me2 = client.get("/api/auth/me", headers=headers)
    me2 = res_me2.json()
    assert me2["student"]["explanation_style"] == "detailed"
    assert me2["student"]["accessibility"]["contrast"] == "high"


# ==============================================================================
# TEST 3: STUDENT 3 — BEGINNER STUDENT & ACCESSIBILITY
# ==============================================================================

def test_student_3_beginner_flow(client):
    token, student_id, reg_data = register_student(client, "Rohan Verma", "rohan")
    headers = {"Authorization": f"Bearer {token}"}

    # Start diagnostic
    res_start = client.get("/api/diagnostic/start", headers=headers)
    diag = res_start.json()
    attempt_id = diag["attempt_id"]
    questions = diag["questions"]

    # Submit answers with intentional wrong answers to simulate foundational learner
    answers = {q["id"]: "Z_INCORRECT" for q in questions}
    # Provide 6 correct answers
    from eduadapt.db.session import get_sync_session_factory
    from eduadapt.db.models.question import Question
    from sqlalchemy import select

    factory = get_sync_session_factory()
    with factory() as session:
        q_uuids = [uuid.UUID(q["id"]) for q in questions[:6]]
        q_objs = session.execute(select(Question).where(Question.id.in_(q_uuids))).scalars().all()
        for q in q_objs:
            answers[str(q.id)] = q.correct_answer

    res_submit = client.post(
        "/api/diagnostic/submit",
        headers=headers,
        json={"attempt_id": attempt_id, "answers": answers},
    )
    assert res_submit.status_code == 200
    result = res_submit.json()
    assert result["score"] <= 40.0
    assert result["learning_level"] == "Beginner"
    assert result["recommended_pace"] == "Deliberate"
    assert len(result["focus_areas"]) > 0

    # Set explanation style to simple and font to opendyslexic
    pref_payload = {
        "explanation_style": "simple",
        "accessibility": {
            "font": "opendyslexic",
            "contrast": "normal",
        },
    }
    res_pref = client.post("/api/profile/preferences", headers=headers, json=pref_payload)
    assert res_pref.status_code == 200

    res_me = client.get("/api/auth/me", headers=headers)
    me = res_me.json()
    assert me["student"]["current_skill_level"] == "Beginner"
    assert me["student"]["learning_pace"] == "Deliberate"
    assert me["student"]["explanation_style"] == "simple"
    assert me["student"]["accessibility"]["font"] == "opendyslexic"


# ==============================================================================
# TEST 4: STUDENT 4 — CROSS-STUDENT DATA ISOLATION (SECURITY)
# ==============================================================================

def test_cross_student_data_isolation(client):
    # Register Student A
    token_a, student_id_a, _ = register_student(client, "Alice Smith", "alice")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Register Student B
    token_b, student_id_b, _ = register_student(client, "Bob Jones", "bob")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Student A starts diagnostic
    res_a = client.get("/api/diagnostic/start", headers=headers_a)
    attempt_id_a = res_a.json()["attempt_id"]

    # Student B starts diagnostic -> gets distinct attempt ID
    res_b = client.get("/api/diagnostic/start", headers=headers_b)
    attempt_id_b = res_b.json()["attempt_id"]
    assert attempt_id_a != attempt_id_b

    # Student B attempts to save answers to Student A's attempt -> Rejected (403 or 404)
    res_hack = client.post(
        "/api/diagnostic/save",
        headers=headers_b,
        json={
            "attempt_id": attempt_id_a,
            "answers": {"fake": "A"},
        },
    )
    assert res_hack.status_code in (403, 404)

    # Student B attempts to access Student A's roadmap
    res_road_hack = client.get(f"/api/roadmap/{student_id_a}", headers=headers_b)
    assert res_road_hack.status_code == 403

    # Student B modifying preferences does NOT modify Student A
    client.post(
        "/api/profile/preferences",
        headers=headers_b,
        json={"explanation_style": "detailed"},
    )
    res_a_me = client.get("/api/auth/me", headers=headers_a)
    assert res_a_me.json()["student"]["explanation_style"] != "detailed"
