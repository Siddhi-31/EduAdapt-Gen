"""Service implementing Initial Diagnostic Assessment lifecycle, scoring, and profile calibration."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
import random
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eduadapt.db.models.assessment import DiagnosticAttempt, DiagnosticResponse
from eduadapt.db.models.question import Question
from eduadapt.db.models.student import Student

logger = logging.getLogger("eduadapt.services.diagnostic_service")

# Diagnostic Question Balance: 25 total questions across 10 categories
TARGET_CATEGORY_DISTRIBUTION = {
    "Numerical Reasoning": 3,
    "Logical Reasoning": 2,
    "Logical Deduction": 1,
    "Reading Comprehension": 3,
    "Verbal Reasoning": 3,
    "Pattern Recognition": 3,
    "Probability": 3,
    "Quantitative Aptitude": 3,
    "Quantitative Reasoning": 1,
    "Classification": 1,
    "Problem Solving": 1,
    "Analytical Thinking": 1,
}
TOTAL_DIAGNOSTIC_QUESTIONS = 25
DIAGNOSTIC_DURATION_SECONDS = 20 * 60  # Strict 20-minute authoritative duration (1200 seconds)


def determine_learning_level(accuracy_pct: float) -> str:
    """Determine initial student learning level based on verified diagnostic performance.

    Thresholds:
    - Advanced: >= 80.0%
    - Intermediate: >= 50.0% and < 80.0%
    - Beginner: < 50.0%
    """
    if accuracy_pct >= 80.0:
        return "Advanced"
    if accuracy_pct >= 50.0:
        return "Intermediate"
    return "Beginner"


def determine_recommended_pace(accuracy_pct: float, avg_time_seconds: float) -> str:
    """Determine initial recommended learning pace based on accuracy and response velocity.

    Thresholds:
    - Fast: accuracy >= 80.0% and avg_time <= 45.0s
    - Deliberate: accuracy < 50.0% or avg_time > 60.0s
    - Moderate: accuracy >= 50.0% and avg_time <= 60.0s (and not Fast)
    """
    if accuracy_pct >= 80.0 and avg_time_seconds <= 45.0:
        return "Fast"
    if accuracy_pct < 50.0 or avg_time_seconds > 60.0:
        return "Deliberate"
    return "Moderate"


async def get_or_create_diagnostic_attempt(
    session: AsyncSession,
    student: Student,
) -> Dict[str, Any]:
    """Retrieve an active in-progress diagnostic attempt or initiate a reproducible new 25-question attempt.

    Guarantees:
    - Idempotent on browser refresh or reconnect: returns existing attempt if in-progress.
    - No duplicate questions within an attempt.
    - Questions selected across all core cognitive categories.
    - Correct answers and explanations are scrubbed from active questions to prevent client-side inspection.
    """
    # 0. Check for completed attempt first
    stmt_done = (
        select(DiagnosticAttempt)
        .where(
            DiagnosticAttempt.student_id == student.id,
            DiagnosticAttempt.status == "completed",
        )
        .order_by(DiagnosticAttempt.completed_at.desc())
    )
    res_done = await session.execute(stmt_done)
    completed = res_done.scalar_one_or_none()
    if completed and completed.result_summary:
        return {
            "attempt_id": str(completed.id),
            "status": "completed",
            "result_summary": completed.result_summary,
            "total_questions": len(completed.question_ids or []),
            "questions": [],
        }

    # 1. Check for active in-progress attempt
    stmt = (
        select(DiagnosticAttempt)
        .options(selectinload(DiagnosticAttempt.responses))
        .where(
            DiagnosticAttempt.student_id == student.id,
            DiagnosticAttempt.status == "in_progress",
        )
        .order_by(DiagnosticAttempt.started_at.desc())
    )
    res = await session.execute(stmt)
    attempt = res.scalar_one_or_none()

    if attempt and attempt.question_ids and len(attempt.question_ids) == TOTAL_DIAGNOSTIC_QUESTIONS:
        now = datetime.now(timezone.utc)
        started = attempt.started_at if attempt.started_at.tzinfo else attempt.started_at.replace(tzinfo=timezone.utc)
        elapsed = (now - started).total_seconds()
        if elapsed >= DIAGNOSTIC_DURATION_SECONDS:
            logger.info("Attempt %s has expired (elapsed: %ss). Auto-submitting.", attempt.id, elapsed)
            existing_answers = {}
            for resp in (attempt.responses or []):
                if resp.selected_answer is not None:
                    existing_answers[str(resp.question_id)] = {
                        "selected_option": resp.selected_answer,
                        "time_taken_seconds": resp.time_taken_seconds or 0,
                    }
            return await submit_diagnostic_assessment(session, student, str(attempt.id), existing_answers)
        return await _format_active_attempt(session, attempt)

    # 2. Select 25 balanced questions from database pool
    stmt_q = select(Question).where(Question.is_active == True)  # noqa: E712
    res_q = await session.execute(stmt_q)
    all_questions = list(res_q.scalars().all())

    if len(all_questions) < TOTAL_DIAGNOSTIC_QUESTIONS:
        raise RuntimeError(
            f"Insufficient questions in database: found {len(all_questions)}, required at least {TOTAL_DIAGNOSTIC_QUESTIONS}. Please seed database."
        )

    # Group questions by category
    by_category: Dict[str, List[Question]] = {}
    for q in all_questions:
        cat = q.category or "General"
        by_category.setdefault(cat, []).append(q)

    # Use student UUID as RNG seed so a given student gets a distinct, reproducible set
    rng = random.Random(str(student.id))

    selected_questions: List[Question] = []
    selected_ids_set = set()

    # Sample from each category according to distribution
    for cat, count in TARGET_CATEGORY_DISTRIBUTION.items():
        pool = by_category.get(cat, [])
        rng.shuffle(pool)
        for q in pool[:count]:
            if q.id not in selected_ids_set:
                selected_questions.append(q)
                selected_ids_set.add(q.id)

    # If count is less than 25 (e.g. minor category naming variants), fill from remaining pool
    remaining_pool = [q for q in all_questions if q.id not in selected_ids_set]
    rng.shuffle(remaining_pool)
    for q in remaining_pool:
        if len(selected_questions) >= TOTAL_DIAGNOSTIC_QUESTIONS:
            break
        selected_questions.append(q)
        selected_ids_set.add(q.id)

    # Deterministic shuffle of the selected 25 questions
    rng.shuffle(selected_questions)
    question_ids = [str(q.id) for q in selected_questions]

    # Create new attempt record
    new_attempt = DiagnosticAttempt(
        student_id=student.id,
        assessment_type="initial_diagnostic",
        status="in_progress",
        maximum_score=Decimal(str(TOTAL_DIAGNOSTIC_QUESTIONS)),
        question_ids=question_ids,
        current_question_index=0,
        flagged_question_ids=[],
    )
    session.add(new_attempt)
    await session.flush()

    # Pre-create DiagnosticResponse entries for each question
    for q in selected_questions:
        resp = DiagnosticResponse(
            attempt_id=new_attempt.id,
            question_id=q.id,
            selected_answer=None,
            is_correct=None,
            marks_obtained=Decimal("0.00"),
            time_taken_seconds=0,
        )
        session.add(resp)

    await session.commit()
    await session.refresh(new_attempt)

    return await _format_active_attempt(session, new_attempt)


async def _format_active_attempt(session: AsyncSession, attempt: DiagnosticAttempt) -> Dict[str, Any]:
    """Format in-progress diagnostic attempt for client view, scrubbing answers."""
    q_uuids = [uuid.UUID(qid) for qid in (attempt.question_ids or [])]
    stmt = select(Question).where(Question.id.in_(q_uuids))
    res = await session.execute(stmt)
    q_map = {str(q.id): q for q in res.scalars().all()}

    # Fetch existing responses
    stmt_resp = select(DiagnosticResponse).where(DiagnosticResponse.attempt_id == attempt.id)
    res_resp = await session.execute(stmt_resp)
    resp_map = {str(r.question_id): r for r in res_resp.scalars().all()}

    ordered_questions: List[Dict[str, Any]] = []
    for idx, qid_str in enumerate(attempt.question_ids or []):
        q = q_map.get(qid_str)
        if not q:
            continue
        existing_resp = resp_map.get(qid_str)
        user_ans = existing_resp.selected_answer if existing_resp else None
        time_taken = existing_resp.time_taken_seconds if existing_resp else 0

        ordered_questions.append({
            "index": idx,
            "id": str(q.id),
            "category": q.category or "General",
            "difficulty": q.difficulty_level,
            "question_text": q.question_text,
            "options": q.options,
            # CRITICAL: do NOT expose correct_answer or explanation before submission
            "selected_answer": user_ans,
            "time_taken_seconds": time_taken,
        })

    saved_answers = {q["id"]: q["selected_answer"] for q in ordered_questions if q["selected_answer"] is not None}

    now = datetime.now(timezone.utc)
    started = attempt.started_at if attempt.started_at.tzinfo else attempt.started_at.replace(tzinfo=timezone.utc)
    elapsed = max(0, int((now - started).total_seconds()))
    remaining_seconds = max(0, DIAGNOSTIC_DURATION_SECONDS - elapsed)
    deadline_dt = started + timedelta(seconds=DIAGNOSTIC_DURATION_SECONDS)

    return {
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "total_questions": len(ordered_questions),
        "current_question_index": attempt.current_question_index or 0,
        "current_index": attempt.current_question_index or 0,
        "flagged_question_ids": attempt.flagged_question_ids or [],
        "flagged_ids": attempt.flagged_question_ids or [],
        "saved_answers": saved_answers,
        "started_at": started.isoformat(),
        "duration_seconds": DIAGNOSTIC_DURATION_SECONDS,
        "time_remaining_seconds": remaining_seconds,
        "deadline": deadline_dt.isoformat(),
        "is_expired": remaining_seconds <= 0,
        "questions": ordered_questions,
    }


async def save_diagnostic_progress(
    session: AsyncSession,
    student: Student,
    attempt_id: str,
    answers: Dict[str, Any],
    current_index: int = 0,
    flagged_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Persist student answer selections and navigation state during assessment."""
    att_uuid = uuid.UUID(attempt_id)
    stmt = select(DiagnosticAttempt).where(
        DiagnosticAttempt.id == att_uuid,
        DiagnosticAttempt.student_id == student.id,
    )
    res = await session.execute(stmt)
    attempt = res.scalar_one_or_none()
    if not attempt or attempt.status != "in_progress":
        raise ValueError("Diagnostic attempt is not active or unauthorized.")

    # Check backend-authoritative expiration
    now = datetime.now(timezone.utc)
    started = attempt.started_at if attempt.started_at.tzinfo else attempt.started_at.replace(tzinfo=timezone.utc)
    elapsed = (now - started).total_seconds()
    if elapsed >= DIAGNOSTIC_DURATION_SECONDS:
        logger.info("Diagnostic attempt %s expired during save progress. Auto-finalizing.", attempt.id)
        results = await submit_diagnostic_assessment(session, student, attempt_id, answers)
        return {"status": "expired", "message": "Time limit of 20 minutes exceeded. Assessment auto-submitted.", "results": results}

    attempt.current_question_index = max(0, min(current_index, TOTAL_DIAGNOSTIC_QUESTIONS - 1))
    if flagged_ids is not None:
        attempt.flagged_question_ids = flagged_ids

    # Update question responses
    for qid_str, ans_data in answers.items():
        try:
            q_uuid = uuid.UUID(qid_str)
        except Exception:
            continue

        selected_opt = ans_data if isinstance(ans_data, str) else ans_data.get("selected_option")
        time_sec = 0 if isinstance(ans_data, str) else ans_data.get("time_taken_seconds", 0)

        stmt_r = select(DiagnosticResponse).where(
            DiagnosticResponse.attempt_id == attempt.id,
            DiagnosticResponse.question_id == q_uuid,
        )
        res_r = await session.execute(stmt_r)
        resp = res_r.scalar_one_or_none()
        if resp:
            resp.selected_answer = selected_opt
            if time_sec:
                resp.time_taken_seconds = time_sec
        else:
            new_r = DiagnosticResponse(
                attempt_id=attempt.id,
                question_id=q_uuid,
                selected_answer=selected_opt,
                time_taken_seconds=time_sec,
            )
            session.add(new_r)

    await session.commit()
    return {"status": "saved", "current_index": attempt.current_question_index}


async def submit_diagnostic_assessment(
    session: AsyncSession,
    student: Student,
    attempt_id: str,
    submitted_answers: Dict[str, Any],
) -> Dict[str, Any]:
    """Evaluate diagnostic submission, calculate category scores, and update student profile."""
    att_uuid = uuid.UUID(attempt_id)
    stmt = (
        select(DiagnosticAttempt)
        .options(selectinload(DiagnosticAttempt.responses))
        .where(
            DiagnosticAttempt.id == att_uuid,
            DiagnosticAttempt.student_id == student.id,
        )
    )
    res = await session.execute(stmt)
    attempt = res.scalar_one_or_none()

    if not attempt:
        raise ValueError("Diagnostic attempt not found.")

    if attempt.status == "completed":
        # Already submitted; return cached results
        return attempt.result_summary or {}

    # Load questions for evaluation
    q_uuids = [uuid.UUID(qid) for qid in (attempt.question_ids or [])]
    stmt_q = select(Question).where(Question.id.in_(q_uuids))
    res_q = await session.execute(stmt_q)
    questions = res_q.scalars().all()
    q_map = {str(q.id): q for q in questions}

    total_questions = len(q_uuids)
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    total_time_seconds = 0

    category_stats: Dict[str, Dict[str, Any]] = {}
    difficulty_stats: Dict[str, Dict[str, Any]] = {}
    detailed_evaluations: List[Dict[str, Any]] = []

    for qid_str in attempt.question_ids:
        q = q_map.get(qid_str)
        if not q:
            continue

        cat = q.category or "General"
        diff = q.difficulty_level or "beginner"

        category_stats.setdefault(cat, {"correct": 0, "total": 0, "accuracy_pct": 0.0})
        difficulty_stats.setdefault(diff, {"correct": 0, "total": 0, "accuracy_pct": 0.0})

        category_stats[cat]["total"] += 1
        difficulty_stats[diff]["total"] += 1

        ans_entry = submitted_answers.get(qid_str)
        if isinstance(ans_entry, dict):
            student_choice = ans_entry.get("selected_option")
            time_taken = ans_entry.get("time_taken_seconds", 0)
        else:
            student_choice = ans_entry
            time_taken = 0

        total_time_seconds += time_taken or 0

        # Verify answer
        correct_answer = q.correct_answer
        if isinstance(correct_answer, dict):
            correct_val = correct_answer.get("answer") or correct_answer.get("correct_option")
        else:
            correct_val = str(correct_answer) if correct_answer is not None else ""

        is_answered = bool(student_choice and str(student_choice).strip())
        is_correct = False

        if is_answered:
            is_correct = str(student_choice).strip().upper() == str(correct_val).strip().upper()
            if is_correct:
                correct_count += 1
                category_stats[cat]["correct"] += 1
                difficulty_stats[diff]["correct"] += 1
            else:
                incorrect_count += 1
        else:
            unanswered_count += 1

        marks = Decimal("1.00") if is_correct else Decimal("0.00")

        # Update or record DiagnosticResponse
        stmt_resp = select(DiagnosticResponse).where(
            DiagnosticResponse.attempt_id == attempt.id,
            DiagnosticResponse.question_id == q.id,
        )
        res_resp = await session.execute(stmt_resp)
        resp = res_resp.scalar_one_or_none()
        if resp:
            resp.selected_answer = student_choice
            resp.is_correct = is_correct
            resp.marks_obtained = marks
            resp.time_taken_seconds = time_taken
        else:
            resp = DiagnosticResponse(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_answer=student_choice,
                is_correct=is_correct,
                marks_obtained=marks,
                time_taken_seconds=time_taken,
            )
            session.add(resp)

        # Include explanation and correct answer now that the test is submitted
        detailed_evaluations.append({
            "question_id": str(q.id),
            "category": cat,
            "difficulty": diff,
            "question_text": q.question_text,
            "options": q.options,
            "selected_answer": student_choice,
            "correct_answer": correct_val,
            "is_correct": is_correct,
            "explanation": q.explanation,
        })

    # Compute category accuracy percentages
    for cat, stats in category_stats.items():
        stats["accuracy_pct"] = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0

    for diff, stats in difficulty_stats.items():
        stats["accuracy_pct"] = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0

    raw_score = Decimal(str(correct_count))
    accuracy_pct = round((correct_count / total_questions) * 100, 1) if total_questions > 0 else 0.0
    avg_time = round(total_time_seconds / total_questions, 1) if total_questions > 0 else 30.0

    # Determine personalized level and recommended pace
    level = determine_learning_level(accuracy_pct)
    recommended_pace = determine_recommended_pace(accuracy_pct, avg_time)

    # Determine strengths and focus areas (based strictly on verified attempted categories)
    strengths = [cat for cat, s in category_stats.items() if s["total"] > 0 and s["accuracy_pct"] >= 75.0]
    focus_areas = [cat for cat, s in category_stats.items() if s["total"] > 0 and s["accuracy_pct"] < 60.0]

    result_summary: Dict[str, Any] = {
        "attempt_id": str(attempt.id),
        "student_id": student.student_code or str(student.id),
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total_questions": total_questions,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "unanswered_count": unanswered_count,
        "raw_score": float(raw_score),
        "maximum_score": float(total_questions),
        "score": accuracy_pct,
        "accuracy_pct": accuracy_pct,
        "average_time_per_question_seconds": avg_time,
        "learning_level": level,
        "recommended_pace": recommended_pace,
        "strengths": strengths,
        "focus_areas": focus_areas,
        "category_breakdown": category_stats,
        "difficulty_breakdown": difficulty_stats,
        "questions_review": detailed_evaluations,
    }

    # Persist in DiagnosticAttempt
    attempt.status = "completed"
    attempt.completed_at = datetime.now(timezone.utc)
    attempt.total_score = raw_score
    attempt.maximum_score = Decimal(str(total_questions))
    attempt.assigned_skill_level = level
    attempt.category_scores = category_stats
    attempt.result_summary = result_summary

    # Update Student Profile with real diagnostic-derived metrics
    student.has_completed_diagnostic = True
    student.current_skill_level = level
    student.learning_pace = recommended_pace

    await session.commit()
    await session.refresh(student)

    return result_summary
