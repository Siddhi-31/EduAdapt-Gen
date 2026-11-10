"""Deterministic and adaptive Learning Roadmap service for EduAdapt.

Grounded in curriculum prerequisites, diagnostic assessment baseline, and
verified student mastery records.
"""

from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from eduadapt.db.models.curriculum import CurriculumSubtopic, CurriculumTopic
from eduadapt.db.models.progress import StudentSubtopicMastery
from eduadapt.db.models.student import Student

# Authoritative PPS curriculum prerequisite sequence
PPS_TOPIC_SEQUENCE = [
    {
        "name": "Variables and Data Types",
        "slug": "variables-and-data-types",
        "unit": "Unit 1: Fundamentals of C",
        "estimated_minutes": 20,
        "prerequisites": [],
        "description": "C syntax, primitive types, memory representation, and I/O format specifiers.",
    },
    {
        "name": "Operators and Expressions",
        "slug": "operators-and-expressions",
        "unit": "Unit 1: Fundamentals of C",
        "estimated_minutes": 25,
        "prerequisites": ["Variables and Data Types"],
        "description": "Arithmetic, relational, logical operators, short-circuit evaluation, and precedence.",
    },
    {
        "name": "Conditionals",
        "slug": "conditionals",
        "unit": "Unit 2: Control Structures",
        "estimated_minutes": 25,
        "prerequisites": ["Operators and Expressions"],
        "description": "Decision branching, if-else trees, switch-case constructs, and control flow.",
    },
    {
        "name": "Loops",
        "slug": "loops",
        "unit": "Unit 2: Control Structures",
        "estimated_minutes": 30,
        "prerequisites": ["Conditionals"],
        "description": "While, for, do-while iteration, nested loops, break, and continue.",
    },
    {
        "name": "Arrays",
        "slug": "arrays",
        "unit": "Unit 3: Arrays & Strings",
        "estimated_minutes": 35,
        "prerequisites": ["Loops"],
        "description": "1D and 2D contiguous memory buffers, boundary safety, and traversal.",
    },
    {
        "name": "Strings",
        "slug": "strings",
        "unit": "Unit 3: Arrays & Strings",
        "estimated_minutes": 30,
        "prerequisites": ["Arrays"],
        "description": "Null-terminated character arrays, pointer traversal, and string operations.",
    },
    {
        "name": "Functions",
        "slug": "functions",
        "unit": "Unit 4: Functions & Pointers",
        "estimated_minutes": 35,
        "prerequisites": ["Loops", "Arrays"],
        "description": "Modular functions, call stack activation records, parameter passing, and recursion.",
    },
    {
        "name": "Pointers",
        "slug": "pointers",
        "unit": "Unit 4: Functions & Pointers",
        "estimated_minutes": 40,
        "prerequisites": ["Functions", "Arrays"],
        "description": "Memory addresses, dereferencing, pointer arithmetic, and pointers with functions.",
    },
    {
        "name": "Structures",
        "slug": "structures",
        "unit": "Unit 5: Structures & Dynamic Memory",
        "estimated_minutes": 35,
        "prerequisites": ["Pointers"],
        "description": "Heterogeneous record types, memory alignment, and arrays of structures.",
    },
    {
        "name": "Dynamic Memory Allocation",
        "slug": "dynamic-memory-allocation",
        "unit": "Unit 5: Structures & Dynamic Memory",
        "estimated_minutes": 45,
        "prerequisites": ["Pointers", "Structures"],
        "description": "Heap allocation via malloc/calloc/realloc, deallocation with free, and leak avoidance.",
    },
]


async def generate_student_roadmap(
    session: AsyncSession,
    student: Student,
    target_topic: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a verified, personalized learning roadmap for a student.

    Rules:
    1. If diagnostic has not been completed, no personalized roadmap is returned.
    2. Completed requires verified activity completion.
    3. Mastered requires demonstrated accuracy >= 80% with multiple checks.
    4. Completed and Mastered are distinct states.
    5. Prior prerequisites must be completed before downstream topics unlock.
    """
    if not student.has_completed_diagnostic:
        return {
            "has_completed_diagnostic": False,
            "message": "Initial Diagnostic Assessment required. Complete the diagnostic to unlock your personalized curriculum roadmap.",
            "stages": [],
            "completed_count": 0,
            "mastered_count": 0,
            "total_count": len(PPS_TOPIC_SEQUENCE),
            "progress_percent": 0,
            "current_topic": None,
            "next_topic": None,
        }

    # Fetch all student subtopic mastery records
    stmt_mastery = (
        select(StudentSubtopicMastery)
        .options(selectinload(StudentSubtopicMastery.subtopic).selectinload(CurriculumSubtopic.topic))
        .where(StudentSubtopicMastery.student_id == student.id)
    )
    res_mastery = await session.execute(stmt_mastery)
    mastery_records = list(res_mastery.scalars().all())

    # Build topic performance map
    topic_stats: Dict[str, Dict[str, Any]] = {}
    for topic_def in PPS_TOPIC_SEQUENCE:
        t_name = topic_def["name"]
        topic_stats[t_name] = {
            "attempts": 0,
            "successes": 0,
            "mastery_sum": 0.0,
            "subtopics_completed": 0,
            "subtopics_mastered": 0,
        }

    for rec in mastery_records:
        if rec.subtopic and rec.subtopic.topic:
            t_name = rec.subtopic.topic.name
            if t_name in topic_stats:
                st = topic_stats[t_name]
                st["attempts"] += rec.attempts or 0
                st["successes"] += rec.successes or 0
                m_score = float(rec.mastery_score or 0.0)
                st["mastery_sum"] += m_score
                if rec.mastery_status == "mastered" or m_score >= 80.0:
                    st["subtopics_mastered"] += 1
                    st["subtopics_completed"] += 1
                elif rec.attempts > 0 and (rec.successes > 0 or rec.mastery_status == "completed"):
                    st["subtopics_completed"] += 1

    # Traverse sequence and compute states
    completed_topics_set = set()
    mastered_topics_set = set()
    stages: List[Dict[str, Any]] = []
    current_topic_assigned = False
    current_focus_topic = None
    next_topic_in_sequence = None

    student_level = student.current_skill_level or "Beginner"

    for idx, t_def in enumerate(PPS_TOPIC_SEQUENCE):
        t_name = t_def["name"]
        prereqs = t_def["prerequisites"]
        prereqs_met = all(p in completed_topics_set for p in prereqs)

        st = topic_stats[t_name]
        is_mastered = st["subtopics_mastered"] >= 2 and st["attempts"] >= 3
        is_completed = is_mastered or (st["subtopics_completed"] >= 2 and st["attempts"] >= 2)
        has_activity = st["attempts"] > 0

        status = "locked"
        if is_mastered:
            status = "mastered"
            completed_topics_set.add(t_name)
            mastered_topics_set.add(t_name)
        elif is_completed:
            status = "completed"
            completed_topics_set.add(t_name)
        elif prereqs_met:
            if has_activity:
                status = "in_progress"
            elif not current_topic_assigned:
                status = "current"
                current_topic_assigned = True
                current_focus_topic = t_name
            else:
                status = "upcoming"
        else:
            status = "locked"

        if status == "in_progress" and not current_topic_assigned:
            status = "current"
            current_topic_assigned = True
            current_focus_topic = t_name

        stages.append({
            "sequence_no": idx + 1,
            "title": t_name,
            "unit": t_def["unit"],
            "status": status,
            "estimated_minutes": t_def["estimated_minutes"],
            "recommended_difficulty": student_level,
            "description": t_def["description"],
            "prerequisites": prereqs,
            "prerequisites_met": prereqs_met,
            "is_locked": status == "locked",
            "mastery_score": round(st["mastery_sum"] / max(1, st["subtopics_completed"]), 1) if st["subtopics_completed"] > 0 else 0.0,
            "is_completed": status in ("completed", "mastered"),
            "is_mastered": status == "mastered",
        })

    # If all unlocked topics are completed, current focus is the last or first in-progress
    if not current_focus_topic:
        for s in stages:
            if s["status"] in ("current", "in_progress"):
                current_focus_topic = s["title"]
                break
        if not current_focus_topic and stages:
            current_focus_topic = stages[0]["title"]
            if stages[0]["status"] not in ("completed", "mastered"):
                stages[0]["status"] = "current"

    # Identify next in sequence
    for s in stages:
        if s["status"] in ("upcoming", "locked") and s["title"] != current_focus_topic:
            next_topic_in_sequence = s["title"]
            break

    completed_count = len(completed_topics_set)
    mastered_count = len(mastered_topics_set)
    total_count = len(stages)
    progress_pct = round((completed_count / total_count) * 100) if total_count > 0 else 0

    return {
        "has_completed_diagnostic": True,
        "student_id": student.student_code or str(student.id),
        "student_name": student.full_name,
        "learning_level": student_level,
        "learning_pace": student.learning_pace or "Moderate",
        "current_topic": target_topic or current_focus_topic or PPS_TOPIC_SEQUENCE[0]["name"],
        "current_focus_topic": current_focus_topic or PPS_TOPIC_SEQUENCE[0]["name"],
        "next_in_sequence": next_topic_in_sequence or "PPS Capstone Application",
        "completed_count": completed_count,
        "mastered_count": mastered_count,
        "total_count": total_count,
        "progress_percent": progress_pct,
        "stages": stages,
    }
