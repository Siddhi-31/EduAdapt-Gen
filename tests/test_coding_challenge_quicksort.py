"""Regression and Verification Test Suite for Coding Challenge Input Parsing,
Standard Input Handling, Quick Sort Execution, and Output Evaluation.

Covers:
1. Diagnosis of Quick Sort uninitialized memory & output mismatch on test case '27 15'.
2. Proper stdin parsing (handling count-prefixed and stream inputs safely).
3. Zero-initialized array safety preventing garbage value leakage.
4. Clean judge stdout (no interactive prompt pollution in submit mode).
5. Comprehensive regression tests:
   - Two array elements
   - Multiple elements
   - Already sorted input
   - Reverse-sorted input
   - Duplicate values
   - Negative values
   - Single-element input
   - Incomplete / invalid input
   - Exact case producing expected output '27 15'
6. Backend evaluation endpoint /api/practice/execute:
   - Exact token/whitespace comparison without flawed substring matching
   - Failed test case stdin and side-by-side expected vs actual output
   - Multi-testcase evaluation in submission mode
"""

import pytest
from fastapi.testclient import TestClient

from eduadapt.api import app
from eduadapt.evaluation.c_executor import CExecutor
from eduadapt.evaluation.models import ExecutionStatus
from eduadapt.teaching.response_schema import _get_challenge_defaults, normalize_topic_name

client = TestClient(app)


# ==============================================================================
# SECTION 1: QUICK SORT C CODE IMPLEMENTATIONS
# ==============================================================================

# Buggy Quick Sort: prints interactive prompts and blindly assumes first int is array size
BUGGY_QUICK_SORT_PROMPT_POLLUTED = """
#include <stdio.h>

void swap(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}

int partition(int arr[], int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return i + 1;
}

void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}

int main(void) {
    int n;
    printf("Enter number of elements: ");
    scanf("%d", &n);
    int arr[100];  // Uninitialized stack memory!
    printf("Enter elements: ");
    for (int i = 0; i < n; i++) {
        scanf("%d", &arr[i]);  // Unchecked scanf return!
    }
    quickSort(arr, 0, n - 1);
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    printf("\\n");
    return 0;
}
"""

# Robust Count-Prefixed Quick Sort: safe initialization, checked scanf, no interactive prompts
ROBUST_COUNT_PREFIXED_QUICK_SORT = """
#include <stdio.h>

void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int partition(int arr[], int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return i + 1;
}

void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}

int main(void) {
    int n = 0;
    if (scanf("%d", &n) != 1 || n <= 0) {
        return 0;
    }
    int arr[128] = {0};  // Zero-initialized
    int count = 0;
    for (int i = 0; i < n && i < 128; i++) {
        if (scanf("%d", &arr[i]) == 1) {
            count++;
        } else {
            break;
        }
    }
    if (count <= 0) {
        return 0;
    }
    quickSort(arr, 0, count - 1);
    for (int i = 0; i < count; i++) {
        printf("%d%s", arr[i], (i == count - 1) ? "" : " ");
    }
    printf("\\n");
    return 0;
}
"""

# Stream-based Quick Sort: reads space-separated integers until EOF without assuming N
STREAM_BASED_QUICK_SORT = """
#include <stdio.h>

void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int partition(int arr[], int low, int high) {
    int pivot = arr[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (arr[j] <= pivot) {
            i++;
            swap(&arr[i], &arr[j]);
        }
    }
    swap(&arr[i + 1], &arr[high]);
    return i + 1;
}

void quickSort(int arr[], int low, int high) {
    if (low < high) {
        int pi = partition(arr, low, high);
        quickSort(arr, low, pi - 1);
        quickSort(arr, pi + 1, high);
    }
}

int main(void) {
    int arr[128] = {0};  // Safely initialized
    int count = 0;
    while (count < 128 && scanf("%d", &arr[count]) == 1) {
        count++;
    }
    if (count <= 0) {
        return 0;
    }
    quickSort(arr, 0, count - 1);
    for (int i = 0; i < count; i++) {
        printf("%d%s", arr[i], (i == count - 1) ? "" : " ");
    }
    printf("\\n");
    return 0;
}
"""

# Correct Pointer Swap program for the reported test case
POINTER_SWAP_CODE = """
#include <stdio.h>

void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int main(void) {
    int x = 0, y = 0;
    if (scanf("%d %d", &x, &y) == 2) {
        swap(&x, &y);
        printf("%d %d\\n", x, y);
    }
    return 0;
}
"""


# ==============================================================================
# SECTION 2: DIAGNOSIS OF REPORTED FAILURE
# ==============================================================================

def test_diagnose_quick_sort_uninitialized_memory_on_unprefixed_input():
    """Diagnose why passing raw elements '15 27' to a count-assuming Quick Sort produces garbage.

    Input: '15 27'
    Buggy behavior:
    - scanf("%d", &n) reads 15 as array size n.
    - Loop attempts to read 15 elements; only 27 is read into arr[0].
    - arr[1..14] remain uninitialized stack garbage.
    - quickSort sorts 15 elements and prints garbage values + interactive prompt.
    """
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res = executor.execute_student_code(BUGGY_QUICK_SORT_PROMPT_POLLUTED, stdin_input="15 27")
    assert res.status == ExecutionStatus.SUCCESS

    # Notice the presence of interactive prompts and more than 2 numbers in output!
    stdout = res.stdout.strip()
    assert "Enter number of elements:" in stdout
    # The output contains multiple numbers because n was read as 15
    tokens = stdout.replace("Enter number of elements: Enter elements:", "").split()
    assert len(tokens) >= 10, "Expected at least 10 numbers due to n=15 reading uninitialized stack memory"


def test_reported_case_pointer_swap_succeeds():
    """Verify that the actual problem requiring '27 15' as output from '15 27' is In-Place Swap."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res = executor.execute_student_code(POINTER_SWAP_CODE, stdin_input="15 27")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "27 15"


# ==============================================================================
# SECTION 3: REGRESSION TESTS FOR QUICK SORT
# ==============================================================================

def test_quicksort_regression_two_elements():
    """Test Quick Sort with exactly two array elements."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    # Count-prefixed format: 2 elements: 27 15 -> 15 27
    res_prefix = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="2\n27 15")
    assert res_prefix.status == ExecutionStatus.SUCCESS
    assert res_prefix.stdout.strip() == "15 27"

    # Stream format: 27 15 -> 15 27
    res_stream = executor.execute_student_code(STREAM_BASED_QUICK_SORT, stdin_input="27 15")
    assert res_stream.status == ExecutionStatus.SUCCESS
    assert res_stream.stdout.strip() == "15 27"


def test_quicksort_regression_multiple_elements():
    """Test Quick Sort with multiple unsorted array elements."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="6\n27 15 38 4 90 12")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "4 12 15 27 38 90"


def test_quicksort_regression_already_sorted():
    """Test Quick Sort with already sorted input."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="5\n10 20 30 40 50")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "10 20 30 40 50"


def test_quicksort_regression_reverse_sorted():
    """Test Quick Sort with strictly reverse-sorted input."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="5\n50 40 30 20 10")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "10 20 30 40 50"


def test_quicksort_regression_duplicate_values():
    """Test Quick Sort with identical and duplicate values."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="6\n7 2 7 1 2 7")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "1 2 2 7 7 7"


def test_quicksort_regression_negative_values():
    """Test Quick Sort with negative, zero, and mixed values."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="5\n7 -2 0 7 -5")
    assert res.status == ExecutionStatus.SUCCESS
    assert res.stdout.strip() == "-5 -2 0 7 7"


def test_quicksort_regression_single_element():
    """Test Quick Sort boundary condition: single-element array."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    res_prefix = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="1\n42")
    assert res_prefix.status == ExecutionStatus.SUCCESS
    assert res_prefix.stdout.strip() == "42"

    res_stream = executor.execute_student_code(STREAM_BASED_QUICK_SORT, stdin_input="42")
    assert res_stream.status == ExecutionStatus.SUCCESS
    assert res_stream.stdout.strip() == "42"


def test_quicksort_regression_incomplete_and_invalid_input():
    """Test Quick Sort robustness when stdin has fewer elements than N or is empty."""
    executor = CExecutor()
    if not executor.has_compiler():
        pytest.skip("No C compiler available.")

    # Incomplete: header declares 5, but only 2 elements provided
    res_incomplete = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="5\n10 20")
    assert res_incomplete.status == ExecutionStatus.SUCCESS
    # Safely sorts only the 2 read elements, NO random uninitialized memory printed!
    assert res_incomplete.stdout.strip() == "10 20"

    # Empty stdin: returns cleanly without hanging or crashing
    res_empty = executor.execute_student_code(ROBUST_COUNT_PREFIXED_QUICK_SORT, stdin_input="")
    assert res_empty.status == ExecutionStatus.SUCCESS
    assert res_empty.stdout.strip() == ""


# ==============================================================================
# SECTION 4: EVALUATION SYSTEM & API VERIFICATION
# ==============================================================================

def test_api_practice_execute_quicksort_submission_pass():
    """Verify that correct Quick Sort code is ACCEPTED with exact token matching."""
    res = client.post(
        "/api/practice/execute",
        json={
            "student_id": "S001",
            "topic": "Quick Sort",
            "source_code": ROBUST_COUNT_PREFIXED_QUICK_SORT,
            "expected_output": "4 12 15 27 38 90",
            "stdin_input": "6\n27 15 38 4 90 12",
            "is_submission": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ACCEPTED"
    assert data["passed"] is True
    assert data["actual_output"] == "4 12 15 27 38 90"
    assert data["expected_output"] == "4 12 15 27 38 90"
    assert data["stdin_input"] == "6\n27 15 38 4 90 12"


def test_api_practice_execute_quicksort_submission_wrong_answer_side_by_side():
    """Verify that WRONG_ANSWER preserves expected vs actual output and failed test case stdin."""
    res = client.post(
        "/api/practice/execute",
        json={
            "student_id": "S001",
            "topic": "Quick Sort",
            "source_code": ROBUST_COUNT_PREFIXED_QUICK_SORT,
            "expected_output": "99 99 99",  # Deliberate mismatch
            "stdin_input": "3\n3 2 1",
            "is_submission": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "WRONG_ANSWER"
    assert data["passed"] is False
    assert data["expected_output"] == "99 99 99"
    assert data["actual_output"] == "1 2 3"
    assert data["stdin_input"] == "3\n3 2 1"
    assert data["input"] == "3\n3 2 1"


def test_api_practice_execute_multi_testcase_evaluation():
    """Verify multi-testcase evaluation in submission mode."""
    test_cases = [
        {"input": "2\n27 15", "expected_output": "15 27"},
        {"input": "5\n5 4 3 2 1", "expected_output": "1 2 3 4 5"},
        {"input": "3\n-10 0 -20", "expected_output": "-20 -10 0"},
    ]

    res = client.post(
        "/api/practice/execute",
        json={
            "student_id": "S001",
            "topic": "Quick Sort",
            "source_code": ROBUST_COUNT_PREFIXED_QUICK_SORT,
            "test_cases": test_cases,
            "is_submission": True,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ACCEPTED"
    assert data["passed"] is True


def test_quicksort_defaults_in_response_schema():
    """Verify that _get_challenge_defaults includes Quick Sort with all competitive specs."""
    norm = normalize_topic_name("Quick Sort")
    assert norm == "Quick Sort"

    defaults = _get_challenge_defaults("Quick Sort")
    assert defaults["title"] == "Quick Sort Array Sorting"
    assert "quickSort" in defaults["starter_code"]
    assert "arr[128] = {0}" in defaults["starter_code"]
    assert len(defaults["expected_test_cases"]) >= 2
    assert len(defaults["hidden_test_cases"]) >= 4
    assert len(defaults["hints"]) == 4
