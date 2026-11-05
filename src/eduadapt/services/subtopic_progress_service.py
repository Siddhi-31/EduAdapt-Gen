"""Persistent Subtopic Progress and Adaptive Cycle Service for EduAdapt.

Enforces strict sequential, mastery-based progression through the PPS curriculum:
- Subtopic 1: UNLOCKED initially.
- Subtopics 2..N: STRICTLY LOCKED until prerequisite subtopic passes mastery check.
- Real reading completion tracking (persisted and verified by backend).
- Mandatory mastery question evaluation (differentiating COMPLETED vs MASTERED).
- Pedagogical remediation for incorrect answers with targeted alternative questions.
- Idempotent backend security preventing skipped cards or fabricated progress metrics.
- Multi-student and multi-topic isolation.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from eduadapt.curriculum.mastery_policy import (
    MASTERY_THRESHOLD_COMPLETED,
    MASTERY_THRESHOLD_MASTERED,
    STATE_AWAITING_ASSESSMENT,
    STATE_COMPLETED,
    STATE_IN_PROGRESS,
    STATE_LOCKED,
    STATE_MASTERED,
    STATE_REMEDIATION_REQUIRED,
    STATE_UNLOCKED,
    can_access_subtopic,
    evaluate_detailed_diagnostic_level,
    evaluate_mastery_tier,
    get_max_cycles_for_tier,
    is_subtopic_completed,
    is_subtopic_mastered,
)
from eduadapt.curriculum.pps_curriculum import (
    PPS_CURRICULUM_TREE,
    SubtopicNode,
    get_subtopics_for_topic,
    get_subtopic_by_id,
    normalize_topic_key,
)
from eduadapt.curriculum.subtopic_mastery_bank import (
    get_subtopic_question,
    SUBTOPIC_MASTERY_BANK,
)

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "student_subtopic_progress.json"


class SubtopicProgressService:
    """Manages granular subtopic progress, sequential lock/unlock states, reading completion, and persistence."""

    def __init__(self, data_file: Optional[Path] = None) -> None:
        self.data_file = data_file or DATA_FILE
        self._ensure_file()

    def _ensure_file(self) -> None:
        try:
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.data_file.exists():
                self.data_file.write_text("{}", encoding="utf-8")
        except Exception as e:
            logger.warning("Could not initialize subtopic progress file: %s", e)

    def _load_data(self) -> Dict[str, Any]:
        try:
            if self.data_file.exists():
                content = self.data_file.read_text(encoding="utf-8")
                return json.loads(content) if content.strip() else {}
        except Exception as e:
            logger.warning("Error reading subtopic progress: %s", e)
        return {}

    def _save_data(self, data: Dict[str, Any]) -> None:
        try:
            self.data_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("Error saving subtopic progress: %s", e)

    def _sanitize_subtopic_state(self, state: Dict[str, Any], idx: int) -> Dict[str, Any]:
        """Ensure an existing subtopic state adheres to strict sequential rules without fabricated progress."""
        history = state.get("history", [])
        attempts = state.get("attempts", 0)
        status = state.get("status", "")

        # Normalize legacy status strings
        if status in ("Pending Prerequisite", "Not Started", "locked", "LOCKED"):
            status = STATE_LOCKED if idx > 0 else STATE_UNLOCKED
        elif status in ("In Progress", "in_progress", "IN_PROGRESS"):
            status = STATE_IN_PROGRESS
        elif status in ("Completed", "completed", "COMPLETED"):
            status = STATE_COMPLETED
        elif status in ("Mastered", "mastered", "MASTERED"):
            # If marked mastered with zero recorded history and zero attempts, this is legacy fabricated data!
            if len(history) == 0 and attempts == 0:
                status = STATE_UNLOCKED if idx == 0 else STATE_LOCKED
                state["mastery"] = 0.0
                state["is_completed"] = False
                state["attempts"] = 0
            else:
                status = STATE_MASTERED
        elif status == "Awaiting Assessment":
            status = STATE_AWAITING_ASSESSMENT
        elif status == "Remediation Required":
            status = STATE_REMEDIATION_REQUIRED
        elif not status:
            status = STATE_UNLOCKED if idx == 0 else STATE_LOCKED

        state["status"] = status
        state.setdefault("is_completed", status in (STATE_COMPLETED, STATE_MASTERED))
        state.setdefault("reading_completed", False)
        state.setdefault("mastery", 0.0 if (attempts == 0 and len(history) == 0) else state.get("mastery", 0.0))
        state.setdefault("attempts", attempts)
        state.setdefault("history", history)
        return state

    def initialize_topic_for_student(
        self,
        student_id: str,
        topic: str,
        overall_mastery: float = 0.0,
        learning_pace: str = "moderate",
    ) -> Dict[str, Any]:
        """Initialize or retrieve the student's subtopic hierarchy for a parent topic.
        
        Strict Sequential Learning Rules:
        - Subtopic 1 (order 1): In Progress / Unlocked
        - Subtopics 2..N: LOCKED
        - Completed subtopics: 0
        - No subtopic marked mastered by default
        """
        norm_topic = normalize_topic_key(topic)
        subtopics = get_subtopics_for_topic(norm_topic)
        mastery_tier = evaluate_mastery_tier(overall_mastery)
        max_cycles = get_max_cycles_for_tier(mastery_tier)

        data = self._load_data()
        student_data = data.setdefault(student_id, {})
        topic_data = student_data.setdefault(norm_topic, {
            "student_id": student_id,
            "parent_topic": norm_topic,
            "overall_mastery": round(float(overall_mastery), 2),
            "mastery_tier": mastery_tier,
            "active_subtopic_id": subtopics[0].id if subtopics else "",
            "subtopics": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        })

        subtopics_map = topic_data.setdefault("subtopics", {})

        for idx, sub in enumerate(subtopics):
            if sub.id not in subtopics_map:
                # Subtopic 1 starts In Progress; subtopics 2..N start LOCKED
                initial_status = "In Progress" if idx == 0 else STATE_LOCKED

                subtopics_map[sub.id] = {
                    "id": sub.id,
                    "title": sub.title,
                    "order": sub.order,
                    "status": initial_status,
                    "mastery": 0.0,
                    "is_completed": False,
                    "reading_completed": False,
                    "learning_cycle": 1,
                    "max_cycles": max_cycles,
                    "attempts": 0,
                    "accuracy": 0.0,
                    "identified_misconceptions": [],
                    "error_categories": [],
                    "last_score": 0.0,
                    "remediation_focus": "",
                    "prerequisites": sub.prerequisites,
                    "history": [],
                }
            else:
                subtopics_map[sub.id] = self._sanitize_subtopic_state(subtopics_map[sub.id], idx)

        # Enforce sequential lock chain: subtopic i can ONLY be unlocked if subtopic i-1 is completed
        for idx in range(1, len(subtopics)):
            prev_sub_id = subtopics[idx - 1].id
            curr_sub_id = subtopics[idx].id
            prev_state = subtopics_map.get(prev_sub_id, {})
            curr_state = subtopics_map.get(curr_sub_id, {})

            prev_completed = prev_state.get("status") in (STATE_COMPLETED, STATE_MASTERED, "Completed", "Mastered") or prev_state.get("is_completed")
            if not prev_completed and curr_state.get("status") not in (STATE_COMPLETED, STATE_MASTERED, "Completed", "Mastered"):
                # Must be LOCKED
                curr_state["status"] = STATE_LOCKED
                curr_state["is_completed"] = False
                curr_state["mastery"] = 0.0

        # Calculate genuine summary metrics
        sub_list = list(subtopics_map.values())
        completed_count = sum(1 for s in sub_list if s.get("status") in (STATE_COMPLETED, STATE_MASTERED, "Completed", "Mastered") or s.get("is_completed"))
        mastered_count = sum(1 for s in sub_list if s.get("status") in (STATE_MASTERED, "Mastered"))
        total_count = len(sub_list)
        progress_pct = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0

        topic_data["overall_mastery"] = round(float(overall_mastery), 2)
        topic_data["completed_count"] = completed_count
        topic_data["mastered_count"] = mastered_count
        topic_data["total_count"] = total_count
        topic_data["progress_percent"] = progress_pct

        if not topic_data.get("active_subtopic_id") and subtopics:
            topic_data["active_subtopic_id"] = subtopics[0].id

        self._save_data(data)
        return topic_data

    def get_topic_progress(
        self,
        student_id: str,
        topic: str,
        overall_mastery: Optional[float] = None,
        learning_pace: str = "moderate",
    ) -> Dict[str, Any]:
        """Get the full subtopic progress map for a student on a parent topic."""
        norm_topic = normalize_topic_key(topic)
        data = self._load_data()
        topic_data = data.get(student_id, {}).get(norm_topic)

        if not topic_data or not topic_data.get("subtopics"):
            topic_data = self.initialize_topic_for_student(
                student_id=student_id,
                topic=norm_topic,
                overall_mastery=0.0,
                learning_pace=learning_pace,
            )

        # Sanitize and enforce sequential locks on loaded data
        subtopics_ordered = get_subtopics_for_topic(norm_topic)
        subtopics_map = topic_data.setdefault("subtopics", {})
        for idx, node in enumerate(subtopics_ordered):
            if node.id in subtopics_map:
                subtopics_map[node.id] = self._sanitize_subtopic_state(subtopics_map[node.id], idx)

        # Enforce sequential lock chain: subtopic i can ONLY be unlocked if subtopic i-1 is completed
        for idx in range(1, len(subtopics_ordered)):
            prev_sub_id = subtopics_ordered[idx - 1].id
            curr_sub_id = subtopics_ordered[idx].id
            prev_state = subtopics_map.get(prev_sub_id, {})
            curr_state = subtopics_map.get(curr_sub_id, {})

            prev_completed = prev_state.get("status") in (STATE_COMPLETED, STATE_MASTERED, "Completed", "Mastered") or prev_state.get("is_completed")
            if not prev_completed and curr_state.get("status") not in (STATE_COMPLETED, STATE_MASTERED, "Completed", "Mastered"):
                curr_state["status"] = STATE_LOCKED
                curr_state["is_completed"] = False
                curr_state["mastery"] = 0.0

        # Re-compute genuine counters
        sub_list = list(topic_data.get("subtopics", {}).values())
        completed_count = sum(1 for s in sub_list if s.get("status") in (STATE_COMPLETED, STATE_MASTERED, "Completed", "Mastered") or s.get("is_completed"))
        mastered_count = sum(1 for s in sub_list if s.get("status") in (STATE_MASTERED, "Mastered"))
        total_count = len(sub_list)
        progress_pct = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0
        avg_mastery = round(sum(s.get("mastery", 0.0) for s in sub_list) / total_count, 2) if total_count > 0 else 0.0

        topic_data["overall_mastery"] = avg_mastery
        topic_data["completed_count"] = completed_count
        topic_data["mastered_count"] = mastered_count
        topic_data["total_count"] = total_count
        topic_data["progress_percent"] = progress_pct
        return topic_data

    def get_subtopic_state(
        self,
        student_id: str,
        topic: str,
        subtopic_id_or_title: Optional[str] = None,
        overall_mastery: Optional[float] = None,
        learning_pace: str = "moderate",
    ) -> Dict[str, Any]:
        """Retrieve state for a specific subtopic, ensuring locked subtopics cannot be accessed out of order."""
        topic_progress = self.get_topic_progress(
            student_id=student_id,
            topic=topic,
            overall_mastery=overall_mastery,
            learning_pace=learning_pace,
        )

        subtopics_map = topic_progress.get("subtopics", {})
        target_sub: Optional[Dict[str, Any]] = None

        if subtopic_id_or_title:
            sub_norm = subtopic_id_or_title.strip().lower()
            for s_id, s_data in subtopics_map.items():
                if s_id.lower() == sub_norm or s_data.get("title", "").lower() == sub_norm:
                    target_sub = s_data
                    break

        if not target_sub:
            active_id = topic_progress.get("active_subtopic_id")
            target_sub = subtopics_map.get(active_id)

        if not target_sub and subtopics_map:
            target_sub = next(iter(subtopics_map.values()))

        return target_sub or {}

    def set_subtopic_in_progress(
        self,
        student_id: str,
        topic: str,
        subtopic_id: str,
    ) -> Dict[str, Any]:
        """Transition subtopic from UNLOCKED to IN_PROGRESS when student generates/opens lesson content."""
        norm_topic = normalize_topic_key(topic)
        topic_data = self.get_topic_progress(student_id, norm_topic)
        sub_data = topic_data.get("subtopics", {}).get(subtopic_id)

        if not sub_data:
            raise ValueError(f"Subtopic '{subtopic_id}' not found in topic '{topic}'.")

        if sub_data.get("status") == STATE_LOCKED:
            raise ValueError(f"Cannot begin subtopic '{subtopic_id}' because it is locked.")

        # If subtopic was just UNLOCKED or In Progress, ensure set to In Progress
        if sub_data.get("status") in (STATE_UNLOCKED, "UNLOCKED"):
            sub_data["status"] = "In Progress"

        topic_data["active_subtopic_id"] = subtopic_id
        topic_data["updated_at"] = datetime.utcnow().isoformat()

        data = self._load_data()
        data.setdefault(student_id, {})[norm_topic] = topic_data
        self._save_data(data)
        return sub_data

    def mark_reading_complete(
        self,
        student_id: str,
        topic: str,
        subtopic_id: str,
    ) -> Dict[str, Any]:
        """Track genuine reading completion.
        
        Validates that:
        1. Subtopic is not LOCKED.
        2. Sets reading_completed = True.
        3. Transitions state from IN_PROGRESS or UNLOCKED to AWAITING_ASSESSMENT.
        """
        norm_topic = normalize_topic_key(topic)
        topic_data = self.get_topic_progress(student_id, norm_topic)
        sub_data = topic_data.get("subtopics", {}).get(subtopic_id)

        if not sub_data:
            raise ValueError(f"Subtopic '{subtopic_id}' not found in topic '{topic}'.")

        if sub_data.get("status") == STATE_LOCKED:
            raise ValueError(f"Subtopic '{subtopic_id}' is locked. Complete previous subtopics first.")

        sub_data["reading_completed"] = True
        sub_data["reading_completed_at"] = datetime.utcnow().isoformat()

        # If in progress or unlocked, transition to awaiting assessment
        if sub_data.get("status") in (STATE_UNLOCKED, STATE_IN_PROGRESS, "In Progress", "UNLOCKED"):
            sub_data["status"] = STATE_AWAITING_ASSESSMENT

        topic_data["updated_at"] = datetime.utcnow().isoformat()
        data = self._load_data()
        data.setdefault(student_id, {})[norm_topic] = topic_data
        self._save_data(data)

        logger.info(
            "Reading completed for student %s on subtopic %s. Status is now %s.",
            student_id, subtopic_id, sub_data["status"]
        )
        return sub_data

    def evaluate_mastery_check(
        self,
        student_id: str,
        topic: str,
        subtopic_id: str,
        selected_option: str,
        time_taken_seconds: int = 25,
        custom_question: Optional[Dict[str, Any]] = None,
        is_remedial: bool = False,
    ) -> Dict[str, Any]:
        """Authoritative backend evaluation of subtopic mastery-check question.
        
        Enforces:
        - Cannot submit if subtopic is LOCKED.
        - Cannot submit if reading_completed is False.
        - Evaluates against correct answer.
        - INCORRECT: status -> REMEDIATION_REQUIRED, keeps next subtopic LOCKED, provides misconception feedback.
        - CORRECT: status -> COMPLETED (or MASTERED if score >= 0.85), UNLOCKS next subtopic in order.
        """
        norm_topic = normalize_topic_key(topic)
        topic_data = self.get_topic_progress(student_id, norm_topic)
        subtopics_map = topic_data.get("subtopics", {})
        sub_data = subtopics_map.get(subtopic_id)

        if not sub_data:
            raise ValueError(f"Subtopic '{subtopic_id}' not found in topic '{topic}'.")

        if sub_data.get("status") == STATE_LOCKED:
            raise ValueError(f"Subtopic '{subtopic_id}' is locked. Prerequisite subtopics must be completed first.")

        if not sub_data.get("reading_completed"):
            raise ValueError("Reading completion required before attempting the subtopic mastery check.")

        # Retrieve canonical or custom question
        question_data = custom_question or get_subtopic_question(subtopic_id, is_remedial=is_remedial)
        if not question_data:
            # Fallback to general primary question
            question_data = get_subtopic_question(subtopic_id, is_remedial=False)

        correct_opt = ""
        explanation = ""
        misconceptions = {}
        if question_data:
            raw_correct = question_data.get("correct_option") or question_data.get("correct_answer") or question_data.get("answer") or "B"
            correct_opt = str(raw_correct).strip()
            explanation = question_data.get("explanation", "Correct understanding demonstrated.")
            misconceptions = question_data.get("misconceptions", {})
        else:
            correct_opt = "B"
            explanation = "Correct answer accepted."

        # Compare answers robustly
        stud_choice = str(selected_option).strip()
        is_correct = False

        if len(correct_opt) == 1 and correct_opt.upper() in ("A", "B", "C", "D"):
            # Check letter match
            stud_letter = stud_choice[0].upper() if stud_choice else ""
            is_correct = (stud_letter == correct_opt.upper())
        else:
            # Full text match
            is_correct = (stud_choice.lower() == correct_opt.lower() or correct_opt.lower() in stud_choice.lower())

        attempts = sub_data.get("attempts", 0) + 1
        sub_data["attempts"] = attempts

        unlocked_subtopic_id = None
        remedial_question = None
        misconception_message = ""

        if is_correct:
            # Score based on attempt history
            if attempts == 1:
                score = 100.0
                new_mastery = 0.90
            elif attempts == 2:
                score = 80.0
                new_mastery = 0.78
            else:
                score = 70.0
                new_mastery = 0.70

            # Determine whether MASTERED or COMPLETED
            mastered = is_subtopic_mastered(new_mastery)
            final_status = STATE_MASTERED if mastered else STATE_COMPLETED

            sub_data["status"] = final_status
            sub_data["is_completed"] = True
            sub_data["mastery"] = round(new_mastery, 2)
            sub_data["last_score"] = score
            sub_data["accuracy"] = round(1.0 / attempts, 2)
            sub_data["remediation_focus"] = "Mastery gate passed. Ready to advance."

            # UNLOCK THE NEXT ELIGIBLE SUBTOPIC
            subtopics_ordered = get_subtopics_for_topic(norm_topic)
            for i, node in enumerate(subtopics_ordered):
                if node.id == subtopic_id and i + 1 < len(subtopics_ordered):
                    next_node = subtopics_ordered[i + 1]
                    next_state = subtopics_map.get(next_node.id)
                    if next_state and next_state.get("status") == STATE_LOCKED:
                        next_state["status"] = STATE_UNLOCKED
                        topic_data["active_subtopic_id"] = next_node.id
                        unlocked_subtopic_id = next_node.id
                        logger.info("Unlocked next subtopic: %s for student %s", next_node.id, student_id)
                    break
        else:
            # Incorrect answer
            score = 35.0
            prev_mastery = sub_data.get("mastery", 0.0)
            new_mastery = min(prev_mastery, 0.35)
            final_status = STATE_REMEDIATION_REQUIRED

            sub_data["status"] = final_status
            sub_data["mastery"] = round(new_mastery, 2)
            sub_data["last_score"] = score
            sub_data["accuracy"] = 0.0

            # Extract tailored misconception
            selected_letter = stud_choice[0].upper() if stud_choice else "A"
            misconception_message = misconceptions.get(
                selected_letter,
                f"Selected option {selected_letter} does not correctly represent {sub_data.get('title')}."
            )
            sub_data.setdefault("identified_misconceptions", []).append(misconception_message)
            sub_data["remediation_focus"] = misconception_message

            # Fetch alternative remedial question
            remedial_question = get_subtopic_question(subtopic_id, is_remedial=True)

        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "attempt": attempts,
            "selected_option": stud_choice,
            "correct_option": correct_opt,
            "is_correct": is_correct,
            "score": score,
            "mastery": round(new_mastery, 2),
            "status": final_status,
            "time_taken_seconds": time_taken_seconds,
        }
        sub_data.setdefault("history", []).append(history_entry)

        # Recalculate summary metrics
        sub_list = list(subtopics_map.values())
        completed_count = sum(1 for s in sub_list if s.get("status") in (STATE_COMPLETED, STATE_MASTERED) or s.get("is_completed"))
        mastered_count = sum(1 for s in sub_list if s.get("status") == STATE_MASTERED)
        total_count = len(sub_list)
        progress_pct = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0
        avg_mastery = round(sum(s.get("mastery", 0.0) for s in sub_list) / total_count, 2) if total_count > 0 else 0.0

        topic_data["overall_mastery"] = avg_mastery
        topic_data["completed_count"] = completed_count
        topic_data["mastered_count"] = mastered_count
        topic_data["total_count"] = total_count
        topic_data["progress_percent"] = progress_pct
        topic_data["updated_at"] = datetime.utcnow().isoformat()

        data = self._load_data()
        data.setdefault(student_id, {})[norm_topic] = topic_data
        self._save_data(data)

        return {
            "student_id": student_id,
            "topic": norm_topic,
            "subtopic_id": subtopic_id,
            "is_correct": is_correct,
            "status": final_status,
            "mastery": round(new_mastery, 2),
            "score": score,
            "attempts": attempts,
            "correct_option": correct_opt,
            "explanation": explanation,
            "misconception": misconception_message,
            "remediation_focus": sub_data.get("remediation_focus", ""),
            "remedial_question": remedial_question,
            "next_subtopic_unlocked": unlocked_subtopic_id is not None,
            "unlocked_subtopic_id": unlocked_subtopic_id,
            "completed_count": completed_count,
            "total_count": total_count,
            "progress_percent": progress_pct,
        }

    def record_cycle_attempt(
        self,
        student_id: str,
        topic: str,
        subtopic_id: str,
        score: float,
        is_correct: bool,
        accuracy: float,
        mistakes: Optional[List[Dict[str, Any]]] = None,
        weak_concepts: Optional[List[str]] = None,
        error_category: Optional[str] = None,
        time_taken_seconds: int = 30,
    ) -> Dict[str, Any]:
        """Record adaptive cycle attempt (used by legacy test submissions and tutor integration)."""
        norm_topic = normalize_topic_key(topic)
        topic_progress = self.get_topic_progress(student_id, norm_topic)
        subtopics_map = topic_progress.get("subtopics", {})
        sub_state = subtopics_map.get(subtopic_id)

        if not sub_state:
            sub_node = get_subtopic_by_id(norm_topic, subtopic_id)
            sub_state = {
                "id": subtopic_id,
                "title": sub_node.title if sub_node else subtopic_id,
                "order": sub_node.order if sub_node else 1,
                "status": STATE_IN_PROGRESS,
                "mastery": 0.0,
                "is_completed": False,
                "reading_completed": True,
                "learning_cycle": 1,
                "max_cycles": 5,
                "attempts": 0,
                "accuracy": 0.0,
                "identified_misconceptions": [],
                "error_categories": [],
                "last_score": 0.0,
                "remediation_focus": "",
                "history": [],
            }
            subtopics_map[subtopic_id] = sub_state

        attempts = sub_state.get("attempts", 0) + 1
        current_cycle = sub_state.get("learning_cycle", 1)
        max_cycles = sub_state.get("max_cycles", 5)

        norm_score = max(0.0, min(1.0, score / 100.0 if score > 1.0 else score))
        prev_mastery = sub_state.get("mastery", 0.0)
        new_mastery = round((prev_mastery * 0.4) + (norm_score * 0.6), 2) if is_correct else round(prev_mastery * 0.4, 2)

        mastered = is_subtopic_mastered(new_mastery) or (score >= 70 and is_correct)
        completed = mastered or is_correct
        status = "Mastered" if mastered else "In Progress"

        if mastered:
            progression_status = "mastered_early_exit" if current_cycle < max_cycles else "mastered"
            remediation_focus = "Mastery achieved. Ready to advance to the next subtopic."
            next_cycle = current_cycle
        elif current_cycle < max_cycles:
            progression_status = "advance_cycle"
            next_cycle = current_cycle + 1
            if weak_concepts:
                remediation_focus = f"Focus remediation on observed weakness: {weak_concepts[-1]}"
            else:
                remediation_focus = f"Reinforce subtopic core mechanics and code tracing (Cycle {next_cycle})"
        else:
            progression_status = "max_cycles_reached"
            next_cycle = current_cycle
            remediation_focus = (
                f"Maximum teaching cycles ({max_cycles}) reached for this subtopic. "
                f"Mastery remains developing ({new_mastery:.2f}). Targeted remediation recommended "
                f"before retrying assessment."
            )

        unlocked_subtopic_id = None
        if completed:
            sub_state["is_completed"] = True
            subtopics_ordered = get_subtopics_for_topic(norm_topic)
            for i, node in enumerate(subtopics_ordered):
                if node.id == subtopic_id and i + 1 < len(subtopics_ordered):
                    next_node = subtopics_ordered[i + 1]
                    next_state = subtopics_map.get(next_node.id)
                    if next_state and next_state.get("status") == STATE_LOCKED:
                        next_state["status"] = "In Progress"
                        topic_progress["active_subtopic_id"] = next_node.id
                        unlocked_subtopic_id = next_node.id
                    break

        sub_state.update({
            "attempts": attempts,
            "mastery": new_mastery,
            "last_score": round(score, 1),
            "accuracy": round(accuracy, 2),
            "status": status,
            "learning_cycle": next_cycle,
            "remediation_focus": remediation_focus,
        })

        sub_state.setdefault("history", []).append({
            "timestamp": datetime.utcnow().isoformat(),
            "cycle": current_cycle,
            "score": round(score, 1),
            "is_correct": is_correct,
            "accuracy": round(accuracy, 2),
            "weak_concepts": weak_concepts or [],
        })

        sub_list = list(subtopics_map.values())
        completed_count = sum(1 for s in sub_list if s.get("status") in (STATE_COMPLETED, STATE_MASTERED, "Completed", "Mastered") or s.get("is_completed"))
        mastered_count = sum(1 for s in sub_list if s.get("status") in (STATE_MASTERED, "Mastered"))
        total_count = len(sub_list)
        progress_pct = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0
        avg_mastery = round(sum(s.get("mastery", 0.0) for s in sub_list) / total_count, 2) if total_count > 0 else 0.0

        topic_progress["overall_mastery"] = avg_mastery
        topic_progress["completed_count"] = completed_count
        topic_progress["mastered_count"] = mastered_count
        topic_progress["total_count"] = total_count
        topic_progress["progress_percent"] = progress_pct
        topic_progress["updated_at"] = datetime.utcnow().isoformat()

        data = self._load_data()
        data.setdefault(student_id, {})[norm_topic] = topic_progress
        self._save_data(data)

        return {
            "student_id": student_id,
            "parent_topic": norm_topic,
            "subtopic_id": subtopic_id,
            "previous_cycle": current_cycle,
            "current_cycle": next_cycle,
            "max_cycles": max_cycles,
            "previous_mastery": prev_mastery,
            "new_mastery": new_mastery,
            "status": status,
            "mastery_achieved": mastered,
            "completed": completed,
            "progression_status": progression_status,
            "remediation_focus": remediation_focus,
            "unlocked_subtopic_id": unlocked_subtopic_id,
        }

    def get_student_subtopic_roadmap(self, student_id: str, topic: str) -> Dict[str, Any]:
        """Return a strictly validated roadmap of all subtopics for a parent topic with genuine states."""
        topic_progress = self.get_topic_progress(student_id, topic)
        norm_topic = normalize_topic_key(topic)
        subtopics_ordered = get_subtopics_for_topic(norm_topic)
        subtopics_map = topic_progress.get("subtopics", {})

        roadmap_items = []
        for idx, node in enumerate(subtopics_ordered):
            state = subtopics_map.get(node.id, {})
            status = state.get("status", STATE_LOCKED if idx > 0 else STATE_UNLOCKED)
            mastery = state.get("mastery", 0.0)
            is_completed = state.get("is_completed", status in (STATE_COMPLETED, STATE_MASTERED))
            reading_completed = state.get("reading_completed", False)
            is_locked = (status == STATE_LOCKED)

            lock_explanation = ""
            if is_locked and idx > 0:
                prev_node = subtopics_ordered[idx - 1]
                lock_explanation = f"Complete Subtopic {prev_node.order} ({prev_node.title}) and pass its mastery check to unlock this subtopic."

            roadmap_items.append({
                "id": node.id,
                "title": node.title,
                "order": node.order,
                "status": status,
                "mastery": mastery,
                "is_completed": is_completed,
                "reading_completed": reading_completed,
                "is_locked": is_locked,
                "can_open": not is_locked,
                "lock_explanation": lock_explanation,
                "diagnostic_level": evaluate_detailed_diagnostic_level(mastery),
                "learning_cycle": state.get("learning_cycle", 1),
                "max_cycles": state.get("max_cycles", 5),
                "prerequisites": node.prerequisites,
                "remediation_focus": state.get("remediation_focus", ""),
            })

        completed_count = sum(1 for item in roadmap_items if item["is_completed"])
        mastered_count = sum(1 for item in roadmap_items if item["status"] == STATE_MASTERED)
        total_count = len(roadmap_items)
        progress_pct = int(round((completed_count / total_count) * 100)) if total_count > 0 else 0

        from eduadapt.models.topic_context import get_curriculum_unit_for_topic

        return {
            "student_id": student_id,
            "topic": topic,
            "parent_topic": norm_topic,
            "curriculum_unit": get_curriculum_unit_for_topic(topic),
            "completed_count": completed_count,
            "mastered_count": mastered_count,
            "total_count": total_count,
            "progress_percent": progress_pct,
            "subtopics": roadmap_items,
        }

    def reset_topic_progress(self, student_id: str, topic: str) -> Dict[str, Any]:
        """Reset student's progress on a topic back to baseline sequential state."""
        norm_topic = normalize_topic_key(topic)
        data = self._load_data()
        if student_id in data and norm_topic in data[student_id]:
            del data[student_id][norm_topic]
            self._save_data(data)
        return self.initialize_topic_for_student(student_id, norm_topic)
