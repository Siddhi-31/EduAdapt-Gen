"""Universal Automated Test Suite for EduAdapt Coding Question Integrity,
Canonical Specification, Pseudocode Quality, Input/Output Contracts, and Sandbox Evaluation.

Covers all requirements from Parts 1 to 12 of the Master Prompt:
1. Single-integer, multiple-integer, array, string, matrix, multi-testcase, pointer,
   dynamic memory allocation, sorting, and recursion questions.
2. Mandatory regression test: Rejection of inconsistent sample output / explanation
   (e.g., sample input '15 27', sample output '27 15' with kth-largest explanation).
3. Generic pseudocode rejection (e.g., 'Print the final values separated by a space').
4. Execution verification of sample input/output against trusted C reference solution.
5. Topic switching and personalization integrity without stale question data.
6. Function-based and full-program input/output contracts.
"""

import pytest
from fastapi.testclient import TestClient

from eduadapt.api import app
from eduadapt.evaluation.c_executor import CExecutor
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.models.canonical_question import (
    CanonicalCodingQuestion,
    QuestionType,
    ValidationStatus,
)
from eduadapt.teaching.canonical_question_registry import (
    CANONICAL_QUESTIONS,
    get_canonical_question,
)
from eduadapt.teaching.question_validator import (
    FORBIDDEN_GENERIC_PSEUDOCODE_PHRASES,
    QuestionValidator,
)
from eduadapt.teaching.response_schema import ResponseParser, _get_challenge_defaults

client = TestClient(app)


# ==============================================================================
# 1. CANONICAL QUESTION SPECIFICATION & REGISTRY AUDIT
# ==============================================================================

def test_canonical_question_registry_completeness():
    """Verify that every PPS curriculum topic has an authoritative canonical specification."""
    expected_topics = [
        "Variables and Data Types",
        "Operators and Expressions",
        "Conditionals",
        "Loops",
        "Arrays",
        "Strings",
        "Functions",
        "Pointers",
        "Structures",
        "Dynamic Memory Allocation",
        "Quick Sort",
    ]

    for topic in expected_topics:
        q = get_canonical_question(topic)
        assert q is not None, f"Topic '{topic}' missing in canonical registry"
        assert q.question_id.startswith("q_")
        assert len(q.title) > 5
        assert len(q.problem_statement) > 20
        assert len(q.input_format) > 5
        assert len(q.output_format) > 5
        assert len(q.pseudocode) > 30
        assert len(q.starter_code) > 20
        assert len(q.reference_solution) > 20
        assert len(q.expected_test_cases) >= 1
        assert len(q.hidden_test_cases) >= 1
        assert len(q.hints) == 4
        assert q.validation_status == ValidationStatus.VERIFIED


def test_all_canonical_reference_solutions_compile_and_pass_samples():
    """Verify that every reference solution in the registry compiles and passes its sample I/O."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered on host.")

    for topic, q in CANONICAL_QUESTIONS.items():
        res = executor.execute_student_code(q.reference_solution, stdin_input=q.sample_input)
        assert res.status == ExecutionStatus.SUCCESS, f"Topic '{topic}' reference solution failed compilation/run: {res.compiler_output or res.stderr}"

        actual = res.stdout.strip()
        expected = q.sample_output.strip()

        norm_actual = "\n".join(l.rstrip() for l in actual.replace("\r\n", "\n").splitlines()).strip()
        norm_expected = "\n".join(l.rstrip() for l in expected.replace("\r\n", "\n").splitlines()).strip()
        tokens_actual = " ".join(norm_actual.split())
        tokens_expected = " ".join(norm_expected.split())

        assert (norm_actual == norm_expected) or (tokens_actual == tokens_expected), (
            f"Topic '{topic}' sample output mismatch. Expected '{expected}', got '{actual}' on input '{q.sample_input}'"
        )


# ==============================================================================
# 2. MANDATORY REGRESSION TEST: REJECTION OF INCONSISTENT QUESTIONS
# ==============================================================================

def test_mandatory_regression_rejects_inconsistent_sample_and_explanation():
    """Mandatory regression test: Reproduce previously observed inconsistency.

    Sample input: '15 27'
    Sample output: '27 15'
    Explanation: Describes an unrelated array and kth-largest-element problem.
    Requirement: The QuestionValidator MUST reject this inconsistent question.
    """
    validator = QuestionValidator()

    inconsistent_challenge = {
        "title": "In-Place Value Swapping Using Pointers",
        "topic": "Pointers",
        "problem_statement": "Write a C program that swaps two integers using pointers.",
        "input_format": "Two space-separated integers on standard input.",
        "output_format": "The two integers swapped, separated by a space.",
        "sample_input": "15 27",
        "sample_output": "27 15",
        "expected_output": "27 15",
        # DISCONNECTED / HALLUCINATED EXPLANATION:
        "sample_explanation": "Finds the kth largest element in the partitioned array using binary search.",
        "starter_code": "#include <stdio.h>\nint main() { return 0; }",
        "reference_solution": "#include <stdio.h>\nint main() { printf(\"27 15\\n\"); return 0; }",
        "hints": [
            "Hint 1: Use pointers.",
            "Hint 2: Dereference addresses.",
            "Hint 3: Exchange values.",
            "Algorithm Swap:\n  1. temp <- *a\n  2. *a <- *b\n  3. *b <- temp\n  4. Print result",
        ],
    }

    is_valid, errors = validator.validate_coding_question(inconsistent_challenge, topic="Pointers")
    assert is_valid is False, "Validator must reject question with disconnected kth-largest explanation!"
    assert any("kth-largest" in err.lower() or "explanation coherence" in err.lower() for err in errors)

    # Verify that repair pipeline rescues the question by restoring authoritative canonical specification
    repaired = validator.validate_and_repair(inconsistent_challenge, topic="Pointers")
    assert repaired["validation_status"] == ValidationStatus.REPAIRED.value
    assert "swap" in repaired["sample_explanation"].lower()
    assert "kth" not in repaired["sample_explanation"].lower()


# ==============================================================================
# 3. PSEUDOCODE / IMPLEMENTATION DIRECTION QUALITY AUDIT
# ==============================================================================

def test_validator_rejects_generic_filler_pseudocode():
    """Verify that generic one-liners are strictly rejected from Pseudocode / Hint 4."""
    validator = QuestionValidator()

    for phrase in FORBIDDEN_GENERIC_PSEUDOCODE_PHRASES:
        ok, err = validator.validate_pseudocode(phrase)
        assert ok is False, f"Validator should reject generic filler phrase: '{phrase}'"
        assert "generic" in err.lower() or "too brief" in err.lower() or "structure" in err.lower()


def test_validator_accepts_structured_algorithmic_pseudocode():
    """Verify that multi-step, meaningful algorithmic pseudocode passes validation."""
    validator = QuestionValidator()

    good_pseudocode = (
        "Algorithm QuickSort:\n"
        "  1. Define partition(arr, low, high):\n"
        "     a. pivot <- arr[high]\n"
        "     b. i <- low - 1\n"
        "     c. For j from low to high - 1:\n"
        "        If arr[j] <= pivot: increment i, swap arr[i] and arr[j]\n"
        "     d. Swap arr[i + 1] and arr[high]\n"
        "     e. Return i + 1\n"
        "  2. Define quickSort(arr, low, high):\n"
        "     If low < high: pi <- partition(arr, low, high), recurse left and right\n"
        "  3. In main: Read N, read arr, invoke quickSort(arr, 0, N - 1), print sorted elements"
    )

    ok, err = validator.validate_pseudocode(good_pseudocode)
    assert ok is True
    assert err is None


def test_all_canonical_questions_have_meaningful_pseudocode():
    """Verify every topic's Hint 4 contains real pseudocode, not generic output instructions."""
    validator = QuestionValidator()

    for topic, q in CANONICAL_QUESTIONS.items():
        pseudo = q.pseudocode
        ok, err = validator.validate_pseudocode(pseudo)
        assert ok is True, f"Topic '{topic}' has invalid pseudocode: {err}"

        # Hint 4 must match or contain the algorithmic pseudocode
        assert len(q.hints) == 4
        h4 = q.hints[3]
        assert "Algorithm" in h4 or "1." in h4 or len(h4) > 40
        assert not any(phrase == h4.strip().lower() for phrase in FORBIDDEN_GENERIC_PSEUDOCODE_PHRASES)


# ==============================================================================
# 4. QUESTION TYPE & PARADIGM TESTS
# ==============================================================================

def test_single_integer_question_execution():
    """Test single-integer input question (Functions: Recursive Factorial)."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    q = get_canonical_question("Functions")
    res = executor.execute_student_code(q.reference_solution, stdin_input="5")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "120"


def test_multiple_integer_question_execution():
    """Test multiple-integer input question (Operators: (a + b) * c)."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    q = get_canonical_question("Operators and Expressions")
    res = executor.execute_student_code(q.reference_solution, stdin_input="3 4 5")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "35"


def test_array_count_prefixed_question_execution():
    """Test count-prefixed array input (Arrays: Find Maximum Element)."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    q = get_canonical_question("Arrays")
    res = executor.execute_student_code(q.reference_solution, stdin_input="5\n12 45 7 89 23")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "89"


def test_stream_based_array_input_execution():
    """Test stream-based array input (reading space-separated elements without N prefix)."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    # Program that counts positive numbers in an unbounded stream until EOF
    stream_c_code = """
    #include <stdio.h>
    int main(void) {
        int val = 0;
        int positive_count = 0;
        while (scanf("%d", &val) == 1) {
            if (val > 0) positive_count++;
        }
        printf("%d\\n", positive_count);
        return 0;
    }
    """
    res = executor.execute_student_code(stream_c_code, stdin_input="-5 10 20 -1 30 0")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "3"


def test_string_question_null_terminator_execution():
    """Test string input and manipulation respecting null terminator (Strings)."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    q = get_canonical_question("Strings")
    res = executor.execute_student_code(q.reference_solution, stdin_input="hello")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "olleh"


def test_matrix_2d_array_question_execution():
    """Test 2D matrix input and row summation."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    matrix_c_code = """
    #include <stdio.h>
    int main(void) {
        int r = 0, c = 0;
        if (scanf("%d %d", &r, &c) != 2 || r <= 0 || c <= 0) return 0;
        int mat[10][10];
        for (int i = 0; i < r; i++) {
            int row_sum = 0;
            for (int j = 0; j < c; j++) {
                scanf("%d", &mat[i][j]);
                row_sum += mat[i][j];
            }
            printf("%d%s", row_sum, (i == r - 1) ? "" : " ");
        }
        printf("\\n");
        return 0;
    }
    """
    res = executor.execute_student_code(matrix_c_code, stdin_input="2 3\n1 2 3\n4 5 6")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "6 15"


def test_multi_testcase_question_execution():
    """Test questions supporting multiple test cases (T followed by test cases)."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    multi_tc_code = """
    #include <stdio.h>
    int main(void) {
        int t = 0;
        if (scanf("%d", &t) != 1) return 0;
        while (t--) {
            int n = 0;
            if (scanf("%d", &n) == 1) {
                printf("%d\\n", n * n);
            }
        }
        return 0;
    }
    """
    res = executor.execute_student_code(multi_tc_code, stdin_input="3\n2\n5\n10")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip().split() == ["4", "25", "100"]


def test_dynamic_memory_allocation_question_execution():
    """Test Dynamic Memory Allocation question execution with malloc and free."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    q = get_canonical_question("Dynamic Memory Allocation")
    res = executor.execute_student_code(q.reference_solution, stdin_input="4\n10 20 30 40")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "10 20 30 40"


def test_quick_sort_question_execution():
    """Test Quick Sort question execution with Lomuto partition."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    q = get_canonical_question("Quick Sort")
    res = executor.execute_student_code(q.reference_solution, stdin_input="5\n50 40 30 20 10")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "10 20 30 40 50"


def test_structures_question_execution():
    """Test Structures question with dot operator access."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler discovered.")

    q = get_canonical_question("Structures")
    res = executor.execute_student_code(q.reference_solution, stdin_input="101 95")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "ID: 101, Marks: 95"


# ==============================================================================
# 5. TOPIC SWITCHING & STALE DATA ISOLATION TESTS
# ==============================================================================

def test_topic_switching_cleans_and_updates_all_question_components():
    """Verify that switching topics updates problem statement, starter code, pseudocode, and test cases."""
    # 1. Fetch for Pointers
    q_ptr = ResponseParser.parse_coding_challenge("", topic="Pointers")
    assert q_ptr["topic"] == "Pointers"
    assert "swap" in q_ptr["title"].lower()
    assert "swap" in q_ptr["problem_statement"].lower()
    assert "temp" in q_ptr["pseudocode"].lower()
    assert q_ptr["sample_input"] == "15 27"
    assert q_ptr["expected_output"] == "27 15"

    # 2. Switch to Strings
    q_str = ResponseParser.parse_coding_challenge("", topic="Strings")
    assert q_str["topic"] == "Strings"
    assert "reversal" in q_str["title"].lower()
    assert "reverse" in q_str["problem_statement"].lower()
    assert "left" in q_str["pseudocode"].lower()
    assert q_str["sample_input"] == "hello"
    assert q_str["expected_output"] == "olleh"
    # Ensure zero leakage from Pointers into Strings!
    assert "swap" not in q_str["problem_statement"].lower()
    assert "15 27" not in str(q_str["expected_test_cases"])

    # 3. Switch to Dynamic Memory Allocation
    q_dma = ResponseParser.parse_coding_challenge("", topic="Dynamic Memory Allocation")
    assert q_dma["topic"] == "Dynamic Memory Allocation"
    assert "malloc" in q_dma["problem_statement"].lower()
    assert "free" in q_dma["starter_code"].lower()
    assert "olleh" not in str(q_dma["expected_test_cases"])


def test_validator_rejects_sample_output_contradicting_reference_solution():
    """Verify that if sample output is fabricated or contradicts code execution, it is rejected."""
    validator = QuestionValidator()

    fraudulent_challenge = {
        "title": "Factorial Calculator",
        "topic": "Functions",
        "problem_statement": "Write a C program to calculate factorial.",
        "input_format": "Integer N",
        "output_format": "N!",
        "sample_input": "5",
        "sample_output": "9999",  # Deliberately fake expected output (5! is 120)
        "sample_explanation": "5! is computed.",
        "starter_code": "#include <stdio.h>\nint main() { printf(\"120\\n\"); return 0; }",
        "reference_solution": "#include <stdio.h>\nint main() { printf(\"120\\n\"); return 0; }",
        "hints": [
            "Hint 1: Recursion.",
            "Hint 2: Base case.",
            "Hint 3: Multiply.",
            "Algorithm Factorial:\n  1. If n <= 1 return 1\n  2. Else return n * factorial(n - 1)",
        ],
    }

    if validator.executor.has_compiler():
        is_valid, errors = validator.validate_coding_question(fraudulent_challenge, topic="Functions")
        assert is_valid is False
        assert any("sample execution mismatch" in err.lower() for err in errors)
