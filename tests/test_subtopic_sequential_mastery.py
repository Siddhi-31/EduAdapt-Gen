"""Comprehensive Test Suite for Subtopic Sequential Learning, Mastery Tracking, and Lock/Unlock Logic.

Verifies all 10 mandatory requirements:
1. New student initialization (0% mastery, subtopic 1 unlocked, 2..N locked, 0 completed).
2. Content generation only (does not unlock next subtopic).
3. Reading complete without question answer (AWAITING_ASSESSMENT, next subtopic locked).
4. Incorrect mastery answer (REMEDIATION_REQUIRED, feedback given, next subtopic locked).
5. Correct mastery answer (COMPLETED/MASTERED, next subtopic UNLOCKED, real evidence mastery).
6. Refresh & navigation persistence.
7. Topic isolation (Pointers vs Arrays).
8. Student isolation (S001 vs S005).
9. Backend security enforcement (rejecting out-of-order unlock, reading bypass).
10. Authentic subtopic question bank & remediation.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from eduadapt.api import app
from eduadapt.curriculum.mastery_policy import (
    STATE_AWAITING_ASSESSMENT,
    STATE_COMPLETED,
    STATE_IN_PROGRESS,
    STATE_LOCKED,
    STATE_MASTERED,
    STATE_REMEDIATION_REQUIRED,
    STATE_UNLOCKED,
)
from eduadapt.curriculum.subtopic_mastery_bank import get_subtopic_question
from eduadapt.services.subtopic_progress_service import SubtopicProgressService


@pytest.fixture
def temp_subtopic_service(tmp_path):
    progress_file = tmp_path / "test_student_subtopic_progress.json"
    return SubtopicProgressService(data_file=progress_file)


# ==============================================================================
# TEST 1: NEW STUDENT INITIALIZATION
# ==============================================================================
def test_new_student_initialization_sequential_locks(temp_subtopic_service):
    """A genuinely new student starting a topic must have 0% mastery, only subtopic 1
    unlocked, all remaining subtopics locked, and 0 completed subtopics.
    """
    student_id = "S_NEW_001"
    topic = "Pointers"

    progress = temp_subtopic_service.initialize_topic_for_student(student_id, topic)
    roadmap = temp_subtopic_service.get_student_subtopic_roadmap(student_id, topic)

    assert roadmap["completed_count"] == 0
    assert roadmap["mastered_count"] == 0
    assert roadmap["progress_percent"] == 0
    assert len(roadmap["subtopics"]) == 9

    # Subtopic 1 must be unlocked / ready to start
    sub1 = roadmap["subtopics"][0]
    assert sub1["order"] == 1
    assert sub1["is_locked"] is False
    assert sub1["status"] in ("In Progress", STATE_UNLOCKED, STATE_IN_PROGRESS)
    assert sub1["mastery"] == 0.0

    # Subtopics 2 through 9 must be STRICTLY LOCKED
    for sub in roadmap["subtopics"][1:]:
        assert sub["is_locked"] is True
        assert sub["status"] == STATE_LOCKED
        assert sub["mastery"] == 0.0
        assert sub["is_completed"] is False
        assert "pass its mastery check" in sub["lock_explanation"]


# ==============================================================================
# TEST 2: CONTENT GENERATION ONLY DOES NOT ADVANCE PROGRESS
# ==============================================================================
def test_content_generation_only_does_not_unlock_next_subtopic(temp_subtopic_service):
    """Generating or opening content for Subtopic 1 must not unlock Subtopic 2."""
    student_id = "S_GEN_ONLY"
    topic = "Pointers"

    # Start subtopic 1
    sub1_state = temp_subtopic_service.set_subtopic_in_progress(student_id, topic, "ptr_intro_addresses")
    assert sub1_state["status"] in ("In Progress", STATE_IN_PROGRESS)

    roadmap = temp_subtopic_service.get_student_subtopic_roadmap(student_id, topic)
    assert roadmap["completed_count"] == 0
    assert roadmap["progress_percent"] == 0

    # Subtopic 2 must still be LOCKED
    sub2 = roadmap["subtopics"][1]
    assert sub2["id"] == "ptr_decl_init"
    assert sub2["is_locked"] is True
    assert sub2["status"] == STATE_LOCKED


# ==============================================================================
# TEST 3: READING COMPLETE, QUESTION UNANSWERED
# ==============================================================================
def test_reading_complete_without_mastery_check(temp_subtopic_service):
    """Marking reading complete transitions state to AWAITING_ASSESSMENT, but Subtopic 2
    remains strictly locked until the mastery check is passed.
    """
    student_id = "S_READ_ONLY"
    topic = "Pointers"

    # Mark reading complete for Subtopic 1
    res = temp_subtopic_service.mark_reading_complete(student_id, topic, "ptr_intro_addresses")
    assert res["reading_completed"] is True
    assert res["status"] == STATE_AWAITING_ASSESSMENT

    roadmap = temp_subtopic_service.get_student_subtopic_roadmap(student_id, topic)
    sub1 = roadmap["subtopics"][0]
    assert sub1["reading_completed"] is True
    assert sub1["status"] == STATE_AWAITING_ASSESSMENT
    assert sub1["is_completed"] is False

    # Next subtopic is still locked!
    sub2 = roadmap["subtopics"][1]
    assert sub2["is_locked"] is True
    assert sub2["status"] == STATE_LOCKED
    assert roadmap["completed_count"] == 0


# ==============================================================================
# TEST 4: INCORRECT MASTERY ANSWER TRIGGERS REMEDIATION AND KEEPS LOCK
# ==============================================================================
def test_incorrect_mastery_answer_remediation(temp_subtopic_service):
    """Submitting an incorrect answer must:
    - Keep Subtopic 2 locked
    - Set state to REMEDIATION_REQUIRED
    - Deliver misconception explanation
    - Offer a remedial question
    - Not fabricate completion or mastery
    """
    student_id = "S_INCORRECT"
    topic = "Pointers"

    temp_subtopic_service.mark_reading_complete(student_id, topic, "ptr_intro_addresses")

    # Correct option for ptr_intro_addresses is 'B'
    eval_res = temp_subtopic_service.evaluate_mastery_check(
        student_id=student_id,
        topic=topic,
        subtopic_id="ptr_intro_addresses",
        selected_option="A",  # Wrong option
        time_taken_seconds=30,
    )

    assert eval_res["is_correct"] is False
    assert eval_res["status"] == STATE_REMEDIATION_REQUIRED
    assert eval_res["next_subtopic_unlocked"] is False
    assert eval_res["unlocked_subtopic_id"] is None
    assert eval_res["correct_option"] == "B"
    assert "confused" in eval_res["misconception"].lower() or "address" in eval_res["misconception"].lower()
    assert eval_res["remedial_question"] is not None

    # Check roadmap
    roadmap = temp_subtopic_service.get_student_subtopic_roadmap(student_id, topic)
    assert roadmap["completed_count"] == 0
    assert roadmap["subtopics"][1]["is_locked"] is True
    assert roadmap["subtopics"][1]["status"] == STATE_LOCKED


# ==============================================================================
# TEST 5: CORRECT MASTERY ANSWER COMPLETES AND UNLOCKS NEXT SUBTOPIC
# ==============================================================================
def test_correct_mastery_answer_unlocks_next_subtopic(temp_subtopic_service):
    """Submitting the correct answer must:
    - Mark Subtopic 1 as COMPLETED / MASTERED
    - Update genuine mastery evidence (0.90 for first-attempt clean pass)
    - UNLOCK Subtopic 2
    - Update progress to 1 of 9 completed (11%)
    """
    student_id = "S_CORRECT"
    topic = "Pointers"

    temp_subtopic_service.mark_reading_complete(student_id, topic, "ptr_intro_addresses")

    eval_res = temp_subtopic_service.evaluate_mastery_check(
        student_id=student_id,
        topic=topic,
        subtopic_id="ptr_intro_addresses",
        selected_option="B",  # Correct option
        time_taken_seconds=20,
    )

    assert eval_res["is_correct"] is True
    assert eval_res["status"] in (STATE_COMPLETED, STATE_MASTERED)
    assert eval_res["mastery"] >= 0.85
    assert eval_res["next_subtopic_unlocked"] is True
    assert eval_res["unlocked_subtopic_id"] == "ptr_decl_init"
    assert eval_res["completed_count"] == 1
    assert eval_res["progress_percent"] == 11

    # Check roadmap status
    roadmap = temp_subtopic_service.get_student_subtopic_roadmap(student_id, topic)
    sub1 = roadmap["subtopics"][0]
    assert sub1["is_completed"] is True
    assert sub1["status"] in (STATE_COMPLETED, STATE_MASTERED)

    # Subtopic 2 is now UNLOCKED and accessible!
    sub2 = roadmap["subtopics"][1]
    assert sub2["is_locked"] is False
    assert sub2["status"] in (STATE_UNLOCKED, "In Progress")

    # Subtopic 3 remains LOCKED!
    sub3 = roadmap["subtopics"][2]
    assert sub3["is_locked"] is True
    assert sub3["status"] == STATE_LOCKED


# ==============================================================================
# TEST 6: REFRESH AND NAVIGATION PERSISTENCE
# ==============================================================================
def test_refresh_and_navigation_persistence(tmp_path):
    """Progress must persist across page refreshes and new service instantiations."""
    progress_file = tmp_path / "persistence_test.json"
    service1 = SubtopicProgressService(data_file=progress_file)

    student_id = "S_PERSIST"
    topic = "Pointers"

    service1.mark_reading_complete(student_id, topic, "ptr_intro_addresses")
    service1.evaluate_mastery_check(student_id, topic, "ptr_intro_addresses", selected_option="B")

    # Simulate browser refresh / new request in fresh service instance
    service2 = SubtopicProgressService(data_file=progress_file)
    roadmap = service2.get_student_subtopic_roadmap(student_id, topic)

    assert roadmap["completed_count"] == 1
    assert roadmap["progress_percent"] == 11
    assert roadmap["subtopics"][0]["is_completed"] is True
    assert roadmap["subtopics"][1]["is_locked"] is False
    assert roadmap["subtopics"][2]["is_locked"] is True


# ==============================================================================
# TEST 7: TOPIC ISOLATION
# ==============================================================================
def test_topic_isolation(temp_subtopic_service):
    """Completing a Pointers subtopic must not affect Arrays or carry over mastery."""
    student_id = "S_ISOLATION"

    # Complete Subtopic 1 on Pointers
    temp_subtopic_service.mark_reading_complete(student_id, "Pointers", "ptr_intro_addresses")
    temp_subtopic_service.evaluate_mastery_check(student_id, "Pointers", "ptr_intro_addresses", selected_option="B")

    # Switch to Arrays
    arrays_roadmap = temp_subtopic_service.get_student_subtopic_roadmap(student_id, "Arrays")
    assert arrays_roadmap["completed_count"] == 0
    assert arrays_roadmap["progress_percent"] == 0
    assert arrays_roadmap["subtopics"][0]["mastery"] == 0.0
    assert arrays_roadmap["subtopics"][1]["is_locked"] is True

    # Switch back to Pointers; progress is preserved
    pointers_roadmap = temp_subtopic_service.get_student_subtopic_roadmap(student_id, "Pointers")
    assert pointers_roadmap["completed_count"] == 1
    assert pointers_roadmap["progress_percent"] == 11


# ==============================================================================
# TEST 8: STUDENT ISOLATION
# ==============================================================================
def test_student_isolation(temp_subtopic_service):
    """Students S001 and S005 must maintain strictly isolated progress."""
    # S001 passes Subtopic 1
    temp_subtopic_service.mark_reading_complete("S001_ISO", "Pointers", "ptr_intro_addresses")
    temp_subtopic_service.evaluate_mastery_check("S001_ISO", "Pointers", "ptr_intro_addresses", selected_option="B")

    # S005 has not started
    s005_roadmap = temp_subtopic_service.get_student_subtopic_roadmap("S005_ISO", "Pointers")
    assert s005_roadmap["completed_count"] == 0
    assert s005_roadmap["progress_percent"] == 0
    assert s005_roadmap["subtopics"][0]["is_completed"] is False
    assert s005_roadmap["subtopics"][1]["is_locked"] is True


# ==============================================================================
# TEST 9: BACKEND ENFORCEMENT & SECURITY
# ==============================================================================
def test_backend_security_rejects_reading_bypass(temp_subtopic_service):
    """Backend must reject mastery check submission if reading was not completed."""
    student_id = "S_HACKER_1"
    topic = "Pointers"

    with pytest.raises(ValueError, match="Reading completion required"):
        temp_subtopic_service.evaluate_mastery_check(
            student_id=student_id,
            topic=topic,
            subtopic_id="ptr_intro_addresses",
            selected_option="B",
        )


def test_backend_security_rejects_locked_subtopic_access(temp_subtopic_service):
    """Backend must reject attempting to start or test a locked subtopic."""
    student_id = "S_HACKER_2"
    topic = "Pointers"

    # Subtopic 2 is locked
    with pytest.raises(ValueError, match="locked"):
        temp_subtopic_service.mark_reading_complete(student_id, topic, "ptr_decl_init")

    with pytest.raises(ValueError, match="locked"):
        temp_subtopic_service.evaluate_mastery_check(
            student_id=student_id,
            topic=topic,
            subtopic_id="ptr_decl_init",
            selected_option="B",
        )


# ==============================================================================
# TEST 10: FASTAPI ENDPOINTS INTEGRATION
# ==============================================================================
def test_api_subtopic_sequential_workflow():
    """Verify complete sequential workflow through FastAPI endpoints."""
    client = TestClient(app)
    student_id = "S_API_TEST"
    topic = "Pointers"

    # Reset student topic to baseline
    reset_res = client.post("/api/subtopics/reset", json={"student_id": student_id, "topic": topic})
    assert reset_res.status_code == 200

    # 1. Fetch roadmap: subtopic 1 unlocked, subtopics 2-9 locked
    road_res = client.get(f"/api/subtopics/roadmap/{student_id}/{topic}")
    assert road_res.status_code == 200
    rdata = road_res.json()
    assert rdata["completed_count"] == 0
    assert rdata["subtopics"][0]["is_locked"] is False
    assert rdata["subtopics"][1]["is_locked"] is True

    # 2. Attempt mastery check before reading -> 400 Bad Request
    fail_check = client.post("/api/subtopics/mastery-check/submit", json={
        "student_id": student_id,
        "topic": topic,
        "subtopic_id": "ptr_intro_addresses",
        "selected_option": "B",
    })
    assert fail_check.status_code == 400
    assert "Reading completion required" in fail_check.json()["detail"]

    # 3. Mark reading complete
    read_res = client.post("/api/subtopics/reading/complete", json={
        "student_id": student_id,
        "topic": topic,
        "subtopic_id": "ptr_intro_addresses",
    })
    assert read_res.status_code == 200
    assert read_res.json()["subtopic"]["reading_completed"] is True

    # 4. Submit incorrect answer -> feedback & remediation
    inc_res = client.post("/api/subtopics/mastery-check/submit", json={
        "student_id": student_id,
        "topic": topic,
        "subtopic_id": "ptr_intro_addresses",
        "selected_option": "A",
    })
    assert inc_res.status_code == 200
    inc_data = inc_res.json()
    assert inc_data["is_correct"] is False
    assert inc_data["status"] == STATE_REMEDIATION_REQUIRED
    assert inc_data["next_subtopic_unlocked"] is False

    # 5. Submit correct answer -> unlock next subtopic
    corr_res = client.post("/api/subtopics/mastery-check/submit", json={
        "student_id": student_id,
        "topic": topic,
        "subtopic_id": "ptr_intro_addresses",
        "selected_option": "B",
    })
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["is_correct"] is True
    assert corr_data["next_subtopic_unlocked"] is True
    assert corr_data["unlocked_subtopic_id"] == "ptr_decl_init"
    assert corr_data["completed_count"] == 1

    # 6. Verify subtopic 2 is now unlocked
    road_res2 = client.get(f"/api/subtopics/roadmap/{student_id}/{topic}")
    rdata2 = road_res2.json()
    assert rdata2["completed_count"] == 1
    assert rdata2["subtopics"][0]["is_completed"] is True
    assert rdata2["subtopics"][1]["is_locked"] is False
    assert rdata2["subtopics"][2]["is_locked"] is True
