"""Canonical Coding Question Specification for EduAdapt.

Defines the authoritative single-source-of-truth data model for all coding questions
across all PPS curriculum topics, difficulty tiers, and question paradigms.
Ensures that problem statement, input contract, output contract, starter code,
reference solution, pseudocode, sample cases, and hidden test cases are
strictly coherent, logically correct, and verifiable.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """Categorization of coding challenge execution harness."""
    FULL_PROGRAM = "FULL_PROGRAM"        # Standard C program with main() reading stdin and writing stdout
    FUNCTION_BASED = "FUNCTION_BASED"    # Function signature implemented by student, tested by evaluation harness


class ValidationStatus(str, Enum):
    """Integrity validation status of a coding question."""
    VERIFIED = "VERIFIED"    # Question passed all schema, compilation, sample I/O, and pseudocode checks
    REPAIRED = "REPAIRED"    # Question was safely repaired using canonical registry
    REJECTED = "REJECTED"    # Question failed critical validation and was rejected


class CanonicalCodingQuestion(BaseModel):
    """Authoritative single-source specification for an EduAdapt coding question."""

    question_id: str = Field(..., description="Unique deterministic identifier (e.g. q_ptr_swap_v1)")
    version: str = Field(default="1.0.0", description="Semantic specification version")
    topic: str = Field(..., description="Normalized PPS curriculum topic (e.g. 'Pointers')")
    subtopic: str = Field(default="", description="Specific curriculum subtopic key (e.g. 'ptr_operators')")
    difficulty: str = Field(default="Intermediate", description="Beginner | Intermediate | Advanced")
    mastery_tier: str = Field(default="Intermediate", description="Target student mastery tier")
    learning_objective: str = Field(..., description="Pedagogical objective grounded in PPS C programming")

    title: str = Field(..., description="Clear problem title")
    problem_statement: str = Field(..., description="Complete, unambiguous problem description")
    input_format: str = Field(..., description="Exact stdin format specification")
    output_format: str = Field(..., description="Exact stdout format specification")
    constraints: str = Field(default="Standard C99; valid memory bounds", description="Algorithmic and input constraints")

    algorithmic_approach: str = Field(default="", description="High-level algorithmic approach (e.g., Divide & Conquer, In-Place Dereferencing)")
    pseudocode: str = Field(..., description="Detailed, meaningful step-by-step algorithmic pseudocode and implementation direction")

    question_type: QuestionType = Field(default=QuestionType.FULL_PROGRAM, description="FULL_PROGRAM or FUNCTION_BASED")
    function_signature: Optional[str] = Field(default=None, description="Exact function prototype when FUNCTION_BASED")
    evaluation_harness: Optional[str] = Field(default=None, description="Harness driver code for testing function implementations")

    starter_code: str = Field(..., description="Starter code with valid headers, types, and input parsing")
    reference_solution: str = Field(..., description="Complete, verified, runnable C reference solution")

    sample_input: str = Field(default="", description="Standard input for sample test case")
    sample_output: str = Field(default="", description="Expected stdout produced by reference solution on sample input")
    sample_explanation: str = Field(default="", description="Pedagogical explanation of sample transformation")

    expected_test_cases: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of visible test cases with 'input' and 'expected_output'",
    )
    hidden_test_cases: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of verified hidden test cases with 'input' and 'expected_output'",
    )

    hints: List[str] = Field(
        default_factory=list,
        description="4-tier progressive hint ladder: Conceptual, Approach, Algorithm, Pseudocode",
    )
    hint_1: str = Field(default="", description="Tier 1: High-level conceptual guidance")
    hint_2: str = Field(default="", description="Tier 2: Algorithmic strategy & approach")
    hint_3: str = Field(default="", description="Tier 3: Step-by-step logic breakdown")
    hint_4: str = Field(default="", description="Tier 4: Detailed pseudocode / implementation direction")

    validation_status: ValidationStatus = Field(default=ValidationStatus.VERIFIED, description="Current verification status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation issues if any")

    def to_challenge_dict(self) -> Dict[str, Any]:
        """Convert canonical question model to the dictionary format expected by the frontend and APIs."""
        h1 = self.hint_1 or (self.hints[0] if len(self.hints) > 0 else "")
        h2 = self.hint_2 or (self.hints[1] if len(self.hints) > 1 else "")
        h3 = self.hint_3 or (self.hints[2] if len(self.hints) > 2 else "")
        h4 = self.hint_4 or self.pseudocode or (self.hints[3] if len(self.hints) > 3 else "")
        final_hints = [h1, h2, h3, h4]

        return {
            "question_id": self.question_id,
            "version": self.version,
            "title": self.title,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "difficulty": self.difficulty,
            "mastery_tier": self.mastery_tier,
            "learning_objective": self.learning_objective,
            "problem_statement": self.problem_statement,
            "description": self.problem_statement,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "constraints": self.constraints,
            "algorithmic_approach": self.algorithmic_approach,
            "pseudocode": self.pseudocode,
            "question_type": self.question_type.value,
            "function_signature": self.function_signature,
            "evaluation_harness": self.evaluation_harness,
            "starter_code": self.starter_code,
            "reference_solution": self.reference_solution,
            "sample_input": self.sample_input,
            "sample_output": self.sample_output,
            "expected_output": self.sample_output,
            "sample_explanation": self.sample_explanation,
            "expected_test_cases": self.expected_test_cases,
            "hidden_test_cases": self.hidden_test_cases,
            "hints": final_hints,
            "hint_1": h1,
            "hint_2": h2,
            "hint_3": h3,
            "hint_4": h4,
            "validation_status": self.validation_status.value,
            "validation_errors": self.validation_errors,
        }
