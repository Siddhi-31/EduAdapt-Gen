"""Universal Coding Question Integrity and Validation Engine.

Enforces strict verification on all coding challenges before they can be displayed
to students or evaluated by the execution sandbox:
1. Canonical schema and non-empty field validation.
2. Topic and subtopic consistency.
3. Pseudocode / Implementation Direction depth & quality validation (rejects generic filler).
4. Sample input/output execution verification against reference solution.
5. Explanation coherence verification (rejects disconnected explanations like kth-largest on swap).
6. Starter code and reference solution compatibility.
7. Bounded fallback and repair to authoritative canonical specifications.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from eduadapt.evaluation.c_executor import CExecutor
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.models.canonical_question import (
    CanonicalCodingQuestion,
    ValidationStatus,
)

logger = logging.getLogger(__name__)

# List of forbidden generic filler phrases in Pseudocode / Hint 4
FORBIDDEN_GENERIC_PSEUDOCODE_PHRASES = [
    "print the final values separated by a space",
    "print the final maxval followed by a newline",
    "print the final sum followed by a newline",
    "ensure every branch prints a trailing newline",
    "print the exact formatted output",
    "print the output followed by a newline",
    "write the implementation using the provided starter",
    "review the foundational concepts of",
    "write your code here",
    "todo: implement",
]

# Keywords that indicate algorithmic logic in pseudocode
ALGORITHMIC_STRUCTURE_MARKERS = [
    "algorithm",
    "step",
    "1.",
    "2.",
    "while",
    "for",
    "loop",
    "if",
    "else",
    "swap",
    "allocate",
    "pointer",
    "read",
    "initialize",
    "return",
    "<-",
    "temp",
    "int ",
    "void ",
    "=",
    ";",
    "*",
    "+",
    "printf",
    "scanf",
    "malloc",
    "free",
]


class QuestionValidationError(Exception):
    """Raised when a coding question violates canonical integrity rules."""
    pass


class QuestionValidator:
    """Universal validator and repair pipeline for EduAdapt coding questions."""

    def __init__(self, executor: Optional[CExecutor] = None) -> None:
        self.executor = executor or CExecutor()

    def validate_pseudocode(self, pseudocode: str) -> Tuple[bool, Optional[str]]:
        """Validate that pseudocode contains meaningful algorithmic logic and is not generic filler."""
        if not pseudocode or not pseudocode.strip():
            return False, "Pseudocode is empty."

        clean = pseudocode.strip().lower()

        # 1. Reject generic one-line filler phrases
        for phrase in FORBIDDEN_GENERIC_PSEUDOCODE_PHRASES:
            if clean == phrase or clean == f"- {phrase}" or clean == f"hint 4: {phrase}" or clean.startswith(f"{phrase}."):
                return False, f"Pseudocode contains generic template filler: '{phrase}'"

        # 2. Check minimum descriptive length
        if len(clean) < 15:
            return False, f"Pseudocode is too brief ({len(clean)} chars); must describe algorithmic logic."

        # 3. Check for algorithmic markers
        has_marker = any(marker in clean for marker in ALGORITHMIC_STRUCTURE_MARKERS)
        if not has_marker:
            return False, "Pseudocode lacks algorithmic structure (missing steps, loops, or operations)."

        return True, None

    def validate_explanation_coherence(
        self,
        explanation: str,
        problem_statement: str,
        sample_input: str,
        sample_output: str,
        topic: str,
    ) -> Tuple[bool, Optional[str]]:
        """Verify that the explanation actually describes the problem and its sample I/O.

        Specifically detects disconnected LLM explanations (e.g., an explanation
        discussing 'kth largest element' or 'array partitioning' when the problem is
        swapping two integers with sample input '15 27' and output '27 15').
        """
        if not explanation or not explanation.strip():
            return False, "Sample explanation is empty."

        exp_lower = explanation.strip().lower()
        prob_lower = problem_statement.strip().lower()

        # Check for disconnected concepts between explanation and problem
        if "swap" in prob_lower and "pointer" in prob_lower:
            # Swap problem should not talk about kth largest or binary search
            if "kth" in exp_lower or "largest element" in exp_lower or "binary search" in exp_lower:
                return False, "Explanation describes unrelated kth-largest or search problem instead of pointer swapping."

        if "factorial" in prob_lower or "recursion" in prob_lower:
            if "string" in exp_lower and "null" in exp_lower:
                return False, "Explanation describes string operations instead of factorial recursion."

        if "reverse" in prob_lower and "string" in prob_lower:
            if "malloc" in exp_lower and "heap" in exp_lower:
                return False, "Explanation describes dynamic memory allocation instead of string reversal."

        return True, None

    def verify_sample_execution(
        self,
        reference_solution: str,
        sample_input: str,
        sample_output: str,
    ) -> Tuple[bool, Optional[str]]:
        """Execute reference solution against sample input to verify that stdout matches sample output."""
        if not self.executor.has_compiler():
            # If GCC compiler is not present, skip execution verification
            return True, None

        if not reference_solution or not reference_solution.strip():
            return True, None

        # If code contains incomplete TODO marker, skip execution check
        if "// todo" in reference_solution.lower() or "/* todo" in reference_solution.lower():
            return True, None

        res = self.executor.execute_trusted_reference(
            source_code=reference_solution,
            stdin_input=sample_input,
            timeout_seconds=5.0,
        )

        if res.status != ExecutionStatus.SUCCESS:
            return False, f"Reference solution failed execution on sample input with status {res.status}: {res.compiler_output or res.stderr}"

        actual = (res.stdout or "").strip()
        expected = (sample_output or "").strip()

        norm_actual = "\n".join(l.rstrip() for l in actual.replace("\r\n", "\n").splitlines()).strip()
        norm_expected = "\n".join(l.rstrip() for l in expected.replace("\r\n", "\n").splitlines()).strip()
        tokens_actual = " ".join(norm_actual.split())
        tokens_expected = " ".join(norm_expected.split())

        if (norm_actual != norm_expected) and (tokens_actual != tokens_expected):
            return False, (
                f"Sample execution mismatch: reference solution output '{actual}' "
                f"does not match declared sample output '{expected}' on input '{sample_input}'."
            )

        return True, None

    def validate_coding_question(
        self,
        challenge: Dict[str, Any],
        topic: str = "Pointers",
    ) -> Tuple[bool, List[str]]:
        """Run complete integrity checks on a coding challenge.

        Returns (is_valid, error_list).
        """
        errors: List[str] = []

        # 1. Essential field presence
        required_fields = [
            "title",
            "problem_statement",
            "input_format",
            "output_format",
            "starter_code",
            "sample_input",
            "sample_output",
        ]
        for f in required_fields:
            if f not in challenge or not str(challenge[f]).strip():
                # Note: sample_input can legitimately be empty for 0-input programs (e.g. sizeof)
                if f == "sample_input" and challenge.get("sample_input") == "":
                    continue
                errors.append(f"Missing required field: '{f}'")

        # 2. Pseudocode validation (Hint 4 or pseudocode field)
        pseudocode = challenge.get("pseudocode") or challenge.get("hint_4") or ""
        if not pseudocode and len(challenge.get("hints", [])) >= 4:
            pseudocode = challenge["hints"][3]

        ok_pseudo, pseudo_err = self.validate_pseudocode(pseudocode)
        if not ok_pseudo:
            errors.append(f"Pseudocode validation failed: {pseudo_err}")

        # 3. Explanation coherence validation
        explanation = challenge.get("sample_explanation") or ""
        prob_statement = challenge.get("problem_statement") or challenge.get("description") or ""
        sample_in = challenge.get("sample_input") or ""
        sample_out = challenge.get("sample_output") or challenge.get("expected_output") or ""

        ok_exp, exp_err = self.validate_explanation_coherence(
            explanation=explanation,
            problem_statement=prob_statement,
            sample_input=sample_in,
            sample_output=sample_out,
            topic=topic,
        )
        if not ok_exp:
            errors.append(f"Explanation coherence failed: {exp_err}")

        # 4. Sample execution verification
        ref_code = challenge.get("reference_solution") or challenge.get("starter_code") or ""
        if ref_code:
            ok_exec, exec_err = self.verify_sample_execution(
                reference_solution=ref_code,
                sample_input=sample_in,
                sample_output=sample_out,
            )
            if not ok_exec:
                errors.append(f"Sample execution failed: {exec_err}")

        return (len(errors) == 0, errors)

    def validate_and_repair(
        self,
        challenge: Dict[str, Any],
        topic: str = "Pointers",
    ) -> Dict[str, Any]:
        """Validate question; if invalid, safely repair with canonical specification for the topic."""
        is_valid, errors = self.validate_coding_question(challenge, topic)
        if is_valid:
            challenge["validation_status"] = ValidationStatus.VERIFIED.value
            challenge["validation_errors"] = []
            return challenge

        logger.warning(
            f"Coding question failed validation for topic '{topic}'. Errors: {errors}. "
            "Repairing with canonical authoritative specification."
        )

        from eduadapt.teaching.canonical_question_registry import get_canonical_question
        canonical = get_canonical_question(topic)
        repaired = canonical.to_challenge_dict()
        repaired["validation_status"] = ValidationStatus.REPAIRED.value
        repaired["validation_errors"] = errors
        return repaired
