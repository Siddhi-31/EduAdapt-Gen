"""Centralized Mastery Policy and Pedagogical Thresholds for EduAdapt.

Defines defensible, unified thresholds and cycle limits across all modules.
Strictly non-agentic and deterministic.
"""

from typing import Dict, Any, List

# Core mastery score thresholds (0.0 to 1.0)
MASTERY_THRESHOLD_BEGINNER_MAX = 0.40       # < 0.40: Beginner / Foundational weakness
MASTERY_THRESHOLD_DEVELOPING_MAX = 0.55     # 0.40 - 0.55: Developing / Below target
MASTERY_THRESHOLD_INTERMEDIATE_MAX = 0.70   # 0.55 - 0.70: Intermediate / Satisfactory understanding
MASTERY_THRESHOLD_ADVANCED_MAX = 0.85       # 0.70 - 0.85: Advanced / Strong understanding
MASTERY_THRESHOLD_COMPLETED = 0.70          # >= 0.70: Passing threshold for subtopic completion gate
MASTERY_THRESHOLD_MASTERED = 0.85           # >= 0.85: Definitive threshold for subtopic mastery badge

# Canonical Subtopic Progression States
STATE_LOCKED = "LOCKED"
STATE_UNLOCKED = "UNLOCKED"
STATE_IN_PROGRESS = "IN_PROGRESS"
STATE_AWAITING_ASSESSMENT = "AWAITING_ASSESSMENT"
STATE_REMEDIATION_REQUIRED = "REMEDIATION_REQUIRED"
STATE_COMPLETED = "COMPLETED"
STATE_MASTERED = "MASTERED"

VALID_SUBTOPIC_STATES = {
    STATE_LOCKED,
    STATE_UNLOCKED,
    STATE_IN_PROGRESS,
    STATE_AWAITING_ASSESSMENT,
    STATE_REMEDIATION_REQUIRED,
    STATE_COMPLETED,
    STATE_MASTERED,
}

# Maximum permitted adaptive teaching cycles per learner tier
MAX_CYCLES_WEAK_LEARNER = 5         # Weak learner: up to 5 adaptive teaching cycles
MAX_CYCLES_INTERMEDIATE_LEARNER = 4  # Intermediate learner: up to 4 adaptive teaching cycles
MAX_CYCLES_ADVANCED_LEARNER = 3     # Advanced learner: up to 3 adaptive teaching cycles

# Error categories for diagnostic error analysis
ERROR_CATEGORIES = {
    "CONCEPTUAL": "Misunderstanding of the underlying programming concept or invariant",
    "SYNTACTIC": "Syntax, typing, formatting, or compiler-enforced errors",
    "LOGICAL": "Flawed control flow, off-by-one errors, or improper algorithm sequencing",
    "OUTPUT_PREDICTION": "Incorrect mental simulation of memory state or execution trace",
    "MEMORY_SAFETY": "Improper dereferencing, buffer boundaries, leaks, or uninitialized access",
}


def evaluate_mastery_tier(mastery_score: float) -> str:
    """Classify a numeric mastery score into a canonical tier."""
    score = float(mastery_score)
    if score < MASTERY_THRESHOLD_BEGINNER_MAX:
        return "Beginner"
    elif score < MASTERY_THRESHOLD_INTERMEDIATE_MAX:
        return "Intermediate"
    else:
        return "Advanced"


def evaluate_detailed_diagnostic_level(mastery_score: float) -> str:
    """Determine fine-grained diagnostic classification for reporting."""
    score = float(mastery_score)
    if score < MASTERY_THRESHOLD_BEGINNER_MAX:
        return "Beginner / Foundational Weakness"
    elif score < MASTERY_THRESHOLD_DEVELOPING_MAX:
        return "Developing / Below Target Mastery"
    elif score < MASTERY_THRESHOLD_INTERMEDIATE_MAX:
        return "Intermediate / Satisfactory Understanding"
    elif score < MASTERY_THRESHOLD_ADVANCED_MAX:
        return "Advanced / Strong Understanding"
    else:
        return "Mastered / Ready to Progress"


def get_max_cycles_for_tier(mastery_tier: str) -> int:
    """Return maximum permitted adaptive teaching cycles for the student's mastery tier."""
    tier = str(mastery_tier).strip().capitalize()
    if tier == "Beginner":
        return MAX_CYCLES_WEAK_LEARNER
    elif tier == "Intermediate":
        return MAX_CYCLES_INTERMEDIATE_LEARNER
    else:
        return MAX_CYCLES_ADVANCED_LEARNER


def is_subtopic_mastered(score: float, required_threshold: float = MASTERY_THRESHOLD_MASTERED) -> bool:
    """Determine whether evidence satisfies the mastery requirement."""
    return float(score) >= required_threshold


def is_subtopic_completed(status: str) -> bool:
    """Return True if status satisfies completion condition."""
    return str(status).strip().upper() in (STATE_COMPLETED, STATE_MASTERED, "MASTERED")


def can_access_subtopic(status: str) -> bool:
    """Return True if subtopic is permitted to be viewed or practiced."""
    norm = str(status).strip().upper()
    return norm not in (STATE_LOCKED, "PENDING PREREQUISITE")

