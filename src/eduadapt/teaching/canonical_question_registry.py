"""Authoritative Canonical Coding Question Registry for EduAdapt.

Provides verified, mathematically and logically coherent canonical specifications
for all Programming for Problem Solving (PPS) curriculum topics, difficulties,
and input/output paradigms. Every entry is self-contained with:
- Exact problem statement
- Strict Input/Output contract
- Full step-by-step Algorithmic Pseudocode / Implementation Direction
- Compatible Starter Code
- Tested, runnable C Reference Solution
- Verified Sample Input and Output
- Complete Expected and Hidden Test Cases
"""

from typing import Dict, List, Optional
from eduadapt.models.canonical_question import (
    CanonicalCodingQuestion,
    QuestionType,
    ValidationStatus,
)


CANONICAL_QUESTIONS: Dict[str, CanonicalCodingQuestion] = {
    # --------------------------------------------------------------------------
    # 1. POINTERS: In-Place Value Swapping (Pointer Operators & Functions)
    # --------------------------------------------------------------------------
    "Pointers": CanonicalCodingQuestion(
        question_id="q_ptr_swap_v1",
        version="1.0.0",
        topic="Pointers",
        subtopic="ptr_operators",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Pass addresses to functions using the address-of operator (&) and dereference pointers (*) to modify caller variables in-place.",
        title="In-Place Value Swapping Using Pointers",
        problem_statement=(
            "Write a C program that swaps the values of two integers using pointers and a helper function `swap(int *a, int *b)`.\n"
            "The program must read two space-separated integers `x` and `y` from standard input.\n"
            "Pass their memory addresses to `swap(&x, &y)` so the function exchanges the contents of the variables in-place.\n"
            "Finally, print the swapped values separated by a single space, followed by a newline."
        ),
        input_format="Two space-separated integers on standard input.",
        output_format="The two swapped integers separated by a single space.",
        constraints="-10000 <= x, y <= 10000; Standard C99; mutation must occur through pointer dereferencing in swap().",
        algorithmic_approach="Pass-by-reference simulation using pointer parameters and temporary value buffering.",
        pseudocode=(
            "Algorithm InPlacePointerSwap:\n"
            "  1. Define helper function swap(pointer a, pointer b):\n"
            "     a. Declare integer temp\n"
            "     b. Store the dereferenced value of a into temp: temp <- *a\n"
            "     c. Assign the dereferenced value of b to the location of a: *a <- *b\n"
            "     d. Assign temp to the location of b: *b <- temp\n"
            "  2. In main():\n"
            "     a. Declare integer variables x and y initialized to 0\n"
            "     b. Read x and y from stdin using scanf(\"%d %d\", &x, &y)\n"
            "     c. If scanf successfully reads exactly 2 integers:\n"
            "        i. Call swap(&x, &y), passing the addresses of x and y using '&'\n"
            "        ii. Print the resulting values formatted as \"%d %d\\n\", x, y\n"
            "     d. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "// Helper function to swap two integers via their memory addresses\n"
            "void swap(int *a, int *b) {\n"
            "    // Write your implementation here\n"
            "}\n\n"
            "int main(void) {\n"
            "    int x = 0, y = 0;\n"
            "    if (scanf(\"%d %d\", &x, &y) == 2) {\n"
            "        swap(&x, &y);\n"
            "        printf(\"%d %d\\n\", x, y);\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "void swap(int *a, int *b) {\n"
            "    int temp = *a;\n"
            "    *a = *b;\n"
            "    *b = temp;\n"
            "}\n\n"
            "int main(void) {\n"
            "    int x = 0, y = 0;\n"
            "    if (scanf(\"%d %d\", &x, &y) == 2) {\n"
            "        swap(&x, &y);\n"
            "        printf(\"%d %d\\n\", x, y);\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="15 27",
        sample_output="27 15",
        sample_explanation="Addresses &x and &y are passed to swap(). In swap(), *a holds 15 and *b holds 27. Swapping them updates x to 27 and y to 15 in the caller scope.",
        expected_test_cases=[
            {"input": "15 27", "expected_output": "27 15"},
            {"input": "100 200", "expected_output": "200 100"},
        ],
        hidden_test_cases=[
            {"input": "0 5", "expected_output": "5 0"},
            {"input": "-10 42", "expected_output": "42 -10"},
            {"input": "77 77", "expected_output": "77 77"},
            {"input": "-99 -1", "expected_output": "-1 -99"},
        ],
        hints=[
            "Pointers store memory addresses. To modify a caller's variable from a function, pass its address using the '&' operator.",
            "Inside `swap(int *a, int *b)`, parameter `a` is a pointer to an integer. Use `*a` to inspect or overwrite the value stored at that address.",
            "Use a temporary local variable: store `*a` into `temp`, copy `*b` into `*a`, then store `temp` into `*b`.",
            "Algorithm InPlacePointerSwap:\n  1. temp <- *a\n  2. *a <- *b\n  3. *b <- temp\n  In main: read x and y with scanf, invoke swap(&x, &y), and print '%d %d\\n'.",
        ],
        hint_1="Pointers store memory addresses. To modify a caller's variable from a function, pass its address using the '&' operator.",
        hint_2="Inside `swap(int *a, int *b)`, parameter `a` is a pointer to an integer. Use `*a` to inspect or overwrite the value stored at that address.",
        hint_3="Use a temporary local variable: store `*a` into `temp`, copy `*b` into `*a`, then store `temp` into `*b`.",
        hint_4="Algorithm InPlacePointerSwap:\n  1. temp <- *a\n  2. *a <- *b\n  3. *b <- temp\n  In main: read x and y with scanf, invoke swap(&x, &y), and print '%d %d\\n'.",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 2. DYNAMIC MEMORY ALLOCATION: Heap Array Allocation & Deallocation
    # --------------------------------------------------------------------------
    "Dynamic Memory Allocation": CanonicalCodingQuestion(
        question_id="q_dma_alloc_v1",
        version="1.0.0",
        topic="Dynamic Memory Allocation",
        subtopic="dma_malloc_free",
        difficulty="Intermediate",
        mastery_tier="Intermediate",
        learning_objective="Allocate memory dynamically on the heap using malloc(), verify pointers against NULL, and free memory cleanly in C.",
        title="Dynamic Integer Array Allocation and Deallocation",
        problem_statement=(
            "Write a C program that dynamically allocates memory on the heap for an array of integers using `malloc()`.\n"
            "The program must first read an integer `size` indicating the number of elements.\n"
            "If `size <= 0`, exit immediately without allocating.\n"
            "Next, allocate `size * sizeof(int)` bytes on the heap and check that the returned pointer is not NULL.\n"
            "Read `size` integers into the allocated block, print them separated by a single space, and free the memory using `free()`."
        ),
        input_format="An integer `size` followed by `size` space-separated integers on standard input.",
        output_format="The array elements separated by a single space.",
        constraints="1 <= size <= 1000; valid C99; explicit NULL check; free memory before termination.",
        algorithmic_approach="Heap memory management with pointer validation and contiguous traversal.",
        pseudocode=(
            "Algorithm DynamicArrayAllocation:\n"
            "  1. Read integer size from stdin\n"
            "  2. If size <= 0, terminate immediately\n"
            "  3. Allocate heap memory: array <- (int *)malloc(size * sizeof(int))\n"
            "  4. If array == NULL, terminate with exit code 1 (allocation failure guard)\n"
            "  5. Loop i from 0 to size - 1:\n"
            "     a. Read integer into array[i] using scanf(\"%d\", &array[i])\n"
            "  6. Loop i from 0 to size - 1:\n"
            "     a. Print array[i]\n"
            "     b. If i < size - 1, print a space \" \", else print \"\\n\"\n"
            "  7. Release heap block: free(array)\n"
            "  8. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n\n"
            "int main(void) {\n"
            "    int size = 0;\n"
            "    if (scanf(\"%d\", &size) != 1 || size <= 0) {\n"
            "        return 0;\n"
            "    }\n\n"
            "    // Write your implementation here:\n"
            "    // 1. Allocate heap memory for 'size' integers using malloc()\n"
            "    // 2. Check if allocation succeeded (array != NULL)\n"
            "    // 3. Read 'size' space-separated integers into the array\n"
            "    // 4. Print the elements separated by space followed by newline\n"
            "    // 5. Free the allocated heap memory with free()\n\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n\n"
            "int main(void) {\n"
            "    int size = 0;\n"
            "    if (scanf(\"%d\", &size) != 1 || size <= 0) {\n"
            "        return 0;\n"
            "    }\n\n"
            "    int *array = (int *)malloc(size * sizeof(int));\n"
            "    if (array == NULL) {\n"
            "        return 1;\n"
            "    }\n\n"
            "    for (int i = 0; i < size; i++) {\n"
            "        scanf(\"%d\", &array[i]);\n"
            "    }\n\n"
            "    for (int i = 0; i < size; i++) {\n"
            "        printf(\"%d%s\", array[i], (i == size - 1) ? \"\" : \" \");\n"
            "    }\n"
            "    printf(\"\\n\");\n\n"
            "    free(array);\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="5\n10 20 30 40 50",
        sample_output="10 20 30 40 50",
        sample_explanation="Memory for 5 integers is allocated on the heap via malloc, populated with 10 20 30 40 50, printed to stdout, and freed.",
        expected_test_cases=[
            {"input": "5\n10 20 30 40 50", "expected_output": "10 20 30 40 50"},
            {"input": "3\n1 2 3", "expected_output": "1 2 3"},
        ],
        hidden_test_cases=[
            {"input": "1\n99", "expected_output": "99"},
            {"input": "4\n-5 0 5 10", "expected_output": "-5 0 5 10"},
            {"input": "6\n100 200 300 400 500 600", "expected_output": "100 200 300 400 500 600"},
        ],
        hints=[
            "Dynamic memory allocation requires the `<stdlib.h>` header.",
            "Calculate allocation size as `size * sizeof(int)`. Check `if (array == NULL)` before accessing it.",
            "Treat the returned pointer like an array: read into `array[i]` and print each element.",
            "Algorithm DynamicArrayAllocation:\n  1. Read size\n  2. array = malloc(size * sizeof(int))\n  3. Guard: if (array == NULL) exit\n  4. Read elements into array[i]\n  5. Print elements with single space separation\n  6. free(array)",
        ],
        hint_1="Dynamic memory allocation requires the `<stdlib.h>` header.",
        hint_2="Calculate allocation size as `size * sizeof(int)`. Check `if (array == NULL)` before accessing it.",
        hint_3="Treat the returned pointer like an array: read into `array[i]` and print each element.",
        hint_4="Algorithm DynamicArrayAllocation:\n  1. Read size\n  2. array = malloc(size * sizeof(int))\n  3. Guard: if (array == NULL) exit\n  4. Read elements into array[i]\n  5. Print elements with single space separation\n  6. free(array)",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 3. QUICK SORT: In-Place Lomuto Divide-and-Conquer Sorting
    # --------------------------------------------------------------------------
    "Quick Sort": CanonicalCodingQuestion(
        question_id="q_sort_quick_v1",
        version="1.0.0",
        topic="Quick Sort",
        subtopic="arr_sorting",
        difficulty="Intermediate",
        mastery_tier="Intermediate",
        learning_objective="Implement the divide-and-conquer Quick Sort algorithm with in-place Lomuto partitioning to sort array elements in ascending order.",
        title="Quick Sort Array Sorting",
        problem_statement=(
            "Write a C program that sorts an array of integers in ascending order using the Quick Sort algorithm.\n"
            "The program must read an integer `N` representing the number of elements, followed by `N` space-separated integers on standard input.\n"
            "Sort the array in-place using a partition function and recursive `quickSort(int arr[], int low, int high)`.\n"
            "Print the sorted integers separated by a single space, followed by a newline.\n"
            "Do not print interactive prompts such as 'Enter elements'."
        ),
        input_format="An integer N, followed by N space-separated integers on standard input.",
        output_format="The sorted integers in ascending order, separated by a single space.",
        constraints="1 <= N <= 100; -10000 <= arr[i] <= 10000; valid C99; in-place recursion.",
        algorithmic_approach="Divide and conquer with Lomuto in-place pivot partitioning.",
        pseudocode=(
            "Algorithm QuickSort:\n"
            "  1. Define partition(arr, low, high):\n"
            "     a. Choose pivot <- arr[high]\n"
            "     b. Initialize partition index i <- low - 1\n"
            "     c. Loop j from low to high - 1:\n"
            "        i. If arr[j] <= pivot:\n"
            "           Increment i\n"
            "           Swap arr[i] and arr[j]\n"
            "     d. Swap arr[i + 1] and arr[high] (place pivot in final sorted position)\n"
            "     e. Return i + 1 as partition index\n"
            "  2. Define quickSort(arr, low, high):\n"
            "     a. If low < high:\n"
            "        i. pi <- partition(arr, low, high)\n"
            "        ii. quickSort(arr, low, pi - 1)  (sort left subarray)\n"
            "        iii. quickSort(arr, pi + 1, high) (sort right subarray)\n"
            "  3. In main():\n"
            "     a. Read N. If N <= 0, return 0\n"
            "     b. Read N integers into zero-initialized array arr\n"
            "     c. Invoke quickSort(arr, 0, N - 1)\n"
            "     d. Print sorted elements separated by space"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "void swap(int *a, int *b) {\n"
            "    int temp = *a;\n"
            "    *a = *b;\n"
            "    *b = temp;\n"
            "}\n\n"
            "int partition(int arr[], int low, int high) {\n"
            "    // Write your partition implementation here\n"
            "}\n\n"
            "void quickSort(int arr[], int low, int high) {\n"
            "    // Write your recursive quickSort implementation here\n"
            "}\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) != 1 || n <= 0) {\n"
            "        return 0;\n"
            "    }\n"
            "    int arr[128] = {0};\n"
            "    int count = 0;\n"
            "    for (int i = 0; i < n && i < 128; i++) {\n"
            "        if (scanf(\"%d\", &arr[i]) == 1) {\n"
            "            count++;\n"
            "        } else {\n"
            "            break;\n"
            "        }\n"
            "    }\n"
            "    if (count <= 0) {\n"
            "        return 0;\n"
            "    }\n"
            "    quickSort(arr, 0, count - 1);\n"
            "    for (int i = 0; i < count; i++) {\n"
            "        printf(\"%d%s\", arr[i], (i == count - 1) ? \"\" : \" \");\n"
            "    }\n"
            "    printf(\"\\n\");\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "void swap(int *a, int *b) {\n"
            "    int temp = *a;\n"
            "    *a = *b;\n"
            "    *b = temp;\n"
            "}\n\n"
            "int partition(int arr[], int low, int high) {\n"
            "    int pivot = arr[high];\n"
            "    int i = low - 1;\n"
            "    for (int j = low; j < high; j++) {\n"
            "        if (arr[j] <= pivot) {\n"
            "            i++;\n"
            "            swap(&arr[i], &arr[j]);\n"
            "        }\n"
            "    }\n"
            "    swap(&arr[i + 1], &arr[high]);\n"
            "    return i + 1;\n"
            "}\n\n"
            "void quickSort(int arr[], int low, int high) {\n"
            "    if (low < high) {\n"
            "        int pi = partition(arr, low, high);\n"
            "        quickSort(arr, low, pi - 1);\n"
            "        quickSort(arr, pi + 1, high);\n"
            "    }\n"
            "}\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) != 1 || n <= 0) {\n"
            "        return 0;\n"
            "    }\n"
            "    int arr[128] = {0};\n"
            "    int count = 0;\n"
            "    for (int i = 0; i < n && i < 128; i++) {\n"
            "        if (scanf(\"%d\", &arr[i]) == 1) {\n"
            "            count++;\n"
            "        } else {\n"
            "            break;\n"
            "        }\n"
            "    }\n"
            "    if (count <= 0) {\n"
            "        return 0;\n"
            "    }\n"
            "    quickSort(arr, 0, count - 1);\n"
            "    for (int i = 0; i < count; i++) {\n"
            "        printf(\"%d%s\", arr[i], (i == count - 1) ? \"\" : \" \");\n"
            "    }\n"
            "    printf(\"\\n\");\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="6\n27 15 38 4 90 12",
        sample_output="4 12 15 27 38 90",
        sample_explanation="The 6 integers {27, 15, 38, 4, 90, 12} are partitioned around pivots recursively and sorted into ascending order.",
        expected_test_cases=[
            {"input": "6\n27 15 38 4 90 12", "expected_output": "4 12 15 27 38 90"},
            {"input": "2\n27 15", "expected_output": "15 27"},
        ],
        hidden_test_cases=[
            {"input": "4\n10 20 30 40", "expected_output": "10 20 30 40"},
            {"input": "5\n50 40 30 20 10", "expected_output": "10 20 30 40 50"},
            {"input": "5\n7 2 7 1 2", "expected_output": "1 2 2 7 7"},
            {"input": "5\n7 -2 0 7 -5", "expected_output": "-5 -2 0 7 7"},
            {"input": "1\n42", "expected_output": "42"},
        ],
        hints=[
            "Choose `arr[high]` as the pivot and initialize partition boundary `i = low - 1`.",
            "Traverse `j` from `low` to `high - 1`. If `arr[j] <= pivot`, increment `i` and swap `arr[i]` with `arr[j]`.",
            "After the loop, place the pivot in its correct sorted position by swapping `arr[i + 1]` with `arr[high]`.",
            "Algorithm QuickSort:\n  1. pi = partition(arr, low, high)\n  2. quickSort(arr, low, pi - 1)\n  3. quickSort(arr, pi + 1, high)\n  In main: read N, read array, invoke quickSort(arr, 0, N - 1), print sorted array.",
        ],
        hint_1="Choose `arr[high]` as the pivot and initialize partition boundary `i = low - 1`.",
        hint_2="Traverse `j` from `low` to `high - 1`. If `arr[j] <= pivot`, increment `i` and swap `arr[i]` with `arr[j]`.",
        hint_3="After the loop, place the pivot in its correct sorted position by swapping `arr[i + 1]` with `arr[high]`.",
        hint_4="Algorithm QuickSort:\n  1. pi = partition(arr, low, high)\n  2. quickSort(arr, low, pi - 1)\n  3. quickSort(arr, pi + 1, high)\n  In main: read N, read array, invoke quickSort(arr, 0, N - 1), print sorted array.",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 4. ARRAYS: Find Maximum Element (Count-Prefixed Array)
    # --------------------------------------------------------------------------
    "Arrays": CanonicalCodingQuestion(
        question_id="q_arr_max_v1",
        version="1.0.0",
        topic="Arrays",
        subtopic="arr_traversal",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Traverse linear array structures and maintain running extremes using conditional checks in C.",
        title="Find Maximum Element in Array",
        problem_statement=(
            "Write a C program that reads an integer `N`, followed by `N` space-separated integers, and prints the maximum value found in the array.\n"
            "If `N <= 0`, exit immediately without printing."
        ),
        input_format="An integer N, followed by N space-separated integers.",
        output_format="The maximum integer in the array followed by a newline.",
        constraints="1 <= N <= 100; -10000 <= arr[i] <= 10000; standard C99.",
        algorithmic_approach="Linear scan with extreme value accumulator.",
        pseudocode=(
            "Algorithm FindMaximumElement:\n"
            "  1. Read integer N from stdin\n"
            "  2. If N <= 0, return 0\n"
            "  3. Declare array arr of size 128 initialized to 0\n"
            "  4. Loop i from 0 to N - 1:\n"
            "     a. Read arr[i] using scanf(\"%d\", &arr[i])\n"
            "  5. Initialize maxVal <- arr[0]\n"
            "  6. Loop i from 1 to N - 1:\n"
            "     a. If arr[i] > maxVal:\n"
            "        maxVal <- arr[i]\n"
            "  7. Print maxVal formatted as \"%d\\n\"\n"
            "  8. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) != 1 || n <= 0) return 0;\n"
            "    int arr[128] = {0};\n"
            "    for (int i = 0; i < n; i++) {\n"
            "        scanf(\"%d\", &arr[i]);\n"
            "    }\n\n"
            "    // Write your implementation here: find the maximum element in arr and print it\n\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) != 1 || n <= 0) return 0;\n"
            "    int arr[128] = {0};\n"
            "    for (int i = 0; i < n; i++) {\n"
            "        scanf(\"%d\", &arr[i]);\n"
            "    }\n\n"
            "    int maxVal = arr[0];\n"
            "    for (int i = 1; i < n; i++) {\n"
            "        if (arr[i] > maxVal) {\n"
            "            maxVal = arr[i];\n"
            "        }\n"
            "    }\n"
            "    printf(\"%d\\n\", maxVal);\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="5\n12 45 7 89 23",
        sample_output="89",
        sample_explanation="Among the 5 array elements {12, 45, 7, 89, 23}, 89 is the maximum value.",
        expected_test_cases=[
            {"input": "5\n12 45 7 89 23", "expected_output": "89"},
            {"input": "3\n100 100 100", "expected_output": "100"},
        ],
        hidden_test_cases=[
            {"input": "4\n-10 -5 -20 -1", "expected_output": "-1"},
            {"input": "1\n42", "expected_output": "42"},
            {"input": "6\n0 0 0 0 0 1", "expected_output": "1"},
        ],
        hints=[
            "Initialize `maxVal = arr[0]` with the first element of the array.",
            "Loop `i` from index 1 to N - 1.",
            "Whenever `arr[i] > maxVal`, update `maxVal = arr[i]`.",
            "Algorithm FindMaximumElement:\n  1. Read N\n  2. Read array elements\n  3. maxVal = arr[0]\n  4. For i from 1 to N - 1: if arr[i] > maxVal then maxVal = arr[i]\n  5. Print maxVal followed by newline",
        ],
        hint_1="Initialize `maxVal = arr[0]` with the first element of the array.",
        hint_2="Loop `i` from index 1 to N - 1.",
        hint_3="Whenever `arr[i] > maxVal`, update `maxVal = arr[i]`.",
        hint_4="Algorithm FindMaximumElement:\n  1. Read N\n  2. Read array elements\n  3. maxVal = arr[0]\n  4. For i from 1 to N - 1: if arr[i] > maxVal then maxVal = arr[i]\n  5. Print maxVal followed by newline",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 5. STRINGS: In-Place String Reversal
    # --------------------------------------------------------------------------
    "Strings": CanonicalCodingQuestion(
        question_id="q_str_rev_v1",
        version="1.0.0",
        topic="Strings",
        subtopic="str_basics_null",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Manipulate null-terminated character sequences, compute lengths, and reverse strings without memory corruption in C.",
        title="String Reversal In-Place",
        problem_statement=(
            "Write a C program that reads a single-word string (up to 100 characters) from standard input and prints it reversed.\n"
            "Your program must maintain the terminating null character `'\\0'`."
        ),
        input_format="A single-word string on standard input.",
        output_format="The reversed string printed to standard output followed by a newline.",
        constraints="1 <= string length <= 100; single word; valid null termination.",
        algorithmic_approach="Two-pointer symmetric swap until midpoint.",
        pseudocode=(
            "Algorithm StringReversal:\n"
            "  1. Declare char array str of size 128 initialized to zeros\n"
            "  2. Read string using scanf(\"%127s\", str)\n"
            "  3. Calculate length: loop len from 0 while str[len] != '\\0'\n"
            "  4. Set left <- 0, right <- len - 1\n"
            "  5. While left < right:\n"
            "     a. char temp <- str[left]\n"
            "     b. str[left] <- str[right]\n"
            "     c. str[right] <- temp\n"
            "     d. left <- left + 1\n"
            "     e. right <- right - 1\n"
            "  6. Print reversed string: printf(\"%s\\n\", str)\n"
            "  7. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n"
            "#include <string.h>\n\n"
            "int main(void) {\n"
            "    char str[128] = {0};\n"
            "    if (scanf(\"%127s\", str) == 1) {\n"
            "        // Write your implementation here: reverse str in-place and print it with a trailing newline\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n"
            "#include <string.h>\n\n"
            "int main(void) {\n"
            "    char str[128] = {0};\n"
            "    if (scanf(\"%127s\", str) == 1) {\n"
            "        int len = 0;\n"
            "        while (str[len] != '\\0') len++;\n"
            "        int left = 0, right = len - 1;\n"
            "        while (left < right) {\n"
            "            char temp = str[left];\n"
            "            str[left] = str[right];\n"
            "            str[right] = temp;\n"
            "            left++;\n"
            "            right--;\n"
            "        }\n"
            "        printf(\"%s\\n\", str);\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="hello",
        sample_output="olleh",
        sample_explanation="Characters of 'hello' are exchanged pairwise: 'h'<->'o', 'e'<->'l', yielding 'olleh'.",
        expected_test_cases=[
            {"input": "hello", "expected_output": "olleh"},
            {"input": "world", "expected_output": "dlrow"},
        ],
        hidden_test_cases=[
            {"input": "a", "expected_output": "a"},
            {"input": "radar", "expected_output": "radar"},
            {"input": "programming", "expected_output": "gnimmargorp"},
        ],
        hints=[
            "Determine the string length by scanning until the null terminator `'\\0'`.",
            "Use two indices: `left = 0` and `right = length - 1`.",
            "Swap `str[left]` and `str[right]`, then increment `left++` and decrement `right--` until `left >= right`.",
            "Algorithm StringReversal:\n  1. Read string\n  2. Compute length len\n  3. left = 0, right = len - 1\n  4. While left < right: swap(str[left], str[right]), left++, right--\n  5. Print '%s\\n', str",
        ],
        hint_1="Determine the string length by scanning until the null terminator `'\\0'`.",
        hint_2="Use two indices: `left = 0` and `right = length - 1`.",
        hint_3="Swap `str[left]` and `str[right]`, then increment `left++` and decrement `right--` until `left >= right`.",
        hint_4="Algorithm StringReversal:\n  1. Read string\n  2. Compute length len\n  3. left = 0, right = len - 1\n  4. While left < right: swap(str[left], str[right]), left++, right--\n  5. Print '%s\\n', str",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 6. FUNCTIONS: Recursive Factorial (Single-Integer Question)
    # --------------------------------------------------------------------------
    "Functions": CanonicalCodingQuestion(
        question_id="q_fn_fact_v1",
        version="1.0.0",
        topic="Functions",
        subtopic="fn_recursion",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Construct recursive functions with explicit base criteria and call-stack unwinding in C.",
        title="Recursive Factorial Calculation",
        problem_statement=(
            "Write a C program that computes the factorial of an integer `N` using a recursive function `factorial(int n)`.\n"
            "Read N from standard input and print `N!` as a 64-bit integer (`long long`)."
        ),
        input_format="A single non-negative integer N (0 <= N <= 12).",
        output_format="The factorial of N followed by a newline.",
        constraints="0 <= N <= 12; must use recursion with base case `n <= 1`.",
        algorithmic_approach="Divide and conquer recursion with base case termination.",
        pseudocode=(
            "Algorithm RecursiveFactorial:\n"
            "  1. Define function factorial(integer n) returning long long:\n"
            "     a. Base Case: If n <= 1, return 1\n"
            "     b. Recursive Case: Return n * factorial(n - 1)\n"
            "  2. In main():\n"
            "     a. Declare integer n initialized to 0\n"
            "     b. Read n using scanf(\"%d\", &n)\n"
            "     c. If n >= 0:\n"
            "        i. result <- factorial(n)\n"
            "        ii. Print result formatted as \"%lld\\n\"\n"
            "     d. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "long long factorial(int n) {\n"
            "    // Write your implementation here: recursively compute n!\n"
            "}\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) == 1 && n >= 0) {\n"
            "        printf(\"%lld\\n\", factorial(n));\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "long long factorial(int n) {\n"
            "    if (n <= 1) return 1;\n"
            "    return (long long)n * factorial(n - 1);\n"
            "}\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) == 1 && n >= 0) {\n"
            "        printf(\"%lld\\n\", factorial(n));\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="5",
        sample_output="120",
        sample_explanation="5! = 5 * 4 * 3 * 2 * 1 = 120, calculated via recursive descent to base case 1.",
        expected_test_cases=[
            {"input": "5", "expected_output": "120"},
            {"input": "0", "expected_output": "1"},
        ],
        hidden_test_cases=[
            {"input": "1", "expected_output": "1"},
            {"input": "6", "expected_output": "720"},
            {"input": "10", "expected_output": "3628800"},
            {"input": "12", "expected_output": "479001600"},
        ],
        hints=[
            "Identify the base case: when `n <= 1`, the factorial is `1`.",
            "In the recursive step, compute `n * factorial(n - 1)`.",
            "Use `long long` return type to prevent arithmetic overflow.",
            "Algorithm RecursiveFactorial:\n  1. factorial(n): if n <= 1 return 1 else return n * factorial(n - 1)\n  2. In main: read n, call factorial(n), print '%lld\\n'",
        ],
        hint_1="Identify the base case: when `n <= 1`, the factorial is `1`.",
        hint_2="In the recursive step, compute `n * factorial(n - 1)`.",
        hint_3="Use `long long` return type to prevent arithmetic overflow.",
        hint_4="Algorithm RecursiveFactorial:\n  1. factorial(n): if n <= 1 return 1 else return n * factorial(n - 1)\n  2. In main: read n, call factorial(n), print '%lld\\n'",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 7. LOOPS: Sum of First N Natural Numbers (Entry-Controlled Iteration)
    # --------------------------------------------------------------------------
    "Loops": CanonicalCodingQuestion(
        question_id="q_loop_sum_v1",
        version="1.0.0",
        topic="Loops",
        subtopic="loop_for",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Utilize iteration structures (for/while loops) to aggregate sequential numeric data in C.",
        title="Sum of First N Natural Numbers",
        problem_statement=(
            "Write a C program that reads a positive integer `N` and computes the sum of the first N natural numbers (1 to N) using a loop.\n"
            "Print the total sum followed by a newline."
        ),
        input_format="A single positive integer N on standard input.",
        output_format="The integer total sum followed by a newline.",
        constraints="1 <= N <= 1000; iteration must use a loop construct.",
        algorithmic_approach="Sequential numeric accumulation using entry-controlled loop.",
        pseudocode=(
            "Algorithm SumOfNaturalNumbers:\n"
            "  1. Declare integer variables n <- 0, sum <- 0\n"
            "  2. Read n using scanf(\"%d\", &n)\n"
            "  3. If n <= 0, return 0\n"
            "  4. Loop i from 1 to n:\n"
            "     a. sum <- sum + i\n"
            "  5. Print sum formatted as \"%d\\n\"\n"
            "  6. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) != 1 || n <= 0) return 0;\n\n"
            "    // Write your implementation here: compute the sum of 1 to n using a loop and print it\n\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int n = 0;\n"
            "    if (scanf(\"%d\", &n) != 1 || n <= 0) return 0;\n"
            "    int sum = 0;\n"
            "    for (int i = 1; i <= n; i++) {\n"
            "        sum += i;\n"
            "    }\n"
            "    printf(\"%d\\n\", sum);\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="5",
        sample_output="15",
        sample_explanation="Sum of numbers from 1 to 5: 1 + 2 + 3 + 4 + 5 = 15.",
        expected_test_cases=[
            {"input": "5", "expected_output": "15"},
            {"input": "10", "expected_output": "55"},
        ],
        hidden_test_cases=[
            {"input": "1", "expected_output": "1"},
            {"input": "100", "expected_output": "5050"},
            {"input": "20", "expected_output": "210"},
        ],
        hints=[
            "Initialize an accumulator `int sum = 0;` before the loop.",
            "Iterate from `i = 1` up to and including `n`.",
            "In each iteration, add `i` to `sum`: `sum += i;`.",
            "Algorithm SumOfNaturalNumbers:\n  1. Read N\n  2. sum = 0\n  3. For i from 1 to N: sum += i\n  4. Print '%d\\n', sum",
        ],
        hint_1="Initialize an accumulator `int sum = 0;` before the loop.",
        hint_2="Iterate from `i = 1` up to and including `n`.",
        hint_3="In each iteration, add `i` to `sum`: `sum += i;`.",
        hint_4="Algorithm SumOfNaturalNumbers:\n  1. Read N\n  2. sum = 0\n  3. For i from 1 to N: sum += i\n  4. Print '%d\\n', sum",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 8. CONDITIONALS: Number Sign Classifier (Multi-Way Branching)
    # --------------------------------------------------------------------------
    "Conditionals": CanonicalCodingQuestion(
        question_id="q_cond_sign_v1",
        version="1.0.0",
        topic="Conditionals",
        subtopic="cond_if_else",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Control program execution flow using branching logic (if / else if / else) in C.",
        title="Number Sign Classifier",
        problem_statement=(
            "Write a C program that reads an integer from standard input and classifies it as 'Positive', 'Negative', or 'Zero'.\n"
            "Print the classification followed by a newline."
        ),
        input_format="A single integer on standard input.",
        output_format="'Positive', 'Negative', or 'Zero' followed by a newline.",
        constraints="-100000 <= num <= 100000; Standard C99 branching.",
        algorithmic_approach="Relational evaluation with mutually exclusive multi-way branches.",
        pseudocode=(
            "Algorithm NumberSignClassifier:\n"
            "  1. Declare integer num initialized to 0\n"
            "  2. Read num using scanf(\"%d\", &num)\n"
            "  3. If num > 0:\n"
            "     a. Print \"Positive\\n\"\n"
            "  4. Else if num < 0:\n"
            "     a. Print \"Negative\\n\"\n"
            "  5. Else:\n"
            "     a. Print \"Zero\\n\"\n"
            "  6. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int num = 0;\n"
            "    if (scanf(\"%d\", &num) == 1) {\n"
            "        // Write your implementation here: print Positive, Negative, or Zero based on num\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int num = 0;\n"
            "    if (scanf(\"%d\", &num) == 1) {\n"
            "        if (num > 0) printf(\"Positive\\n\");\n"
            "        else if (num < 0) printf(\"Negative\\n\");\n"
            "        else printf(\"Zero\\n\");\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="-7",
        sample_output="Negative",
        sample_explanation="-7 is less than zero, satisfying the else-if condition num < 0, outputting 'Negative'.",
        expected_test_cases=[
            {"input": "-7", "expected_output": "Negative"},
            {"input": "42", "expected_output": "Positive"},
        ],
        hidden_test_cases=[
            {"input": "0", "expected_output": "Zero"},
            {"input": "-1", "expected_output": "Negative"},
            {"input": "1000", "expected_output": "Positive"},
        ],
        hints=[
            "Use an `if (num > 0)` branch for strictly positive values.",
            "Use `else if (num < 0)` for negative values.",
            "Use a terminal `else` branch for when the number is exactly zero.",
            "Algorithm NumberSignClassifier:\n  1. Read num\n  2. If num > 0: print Positive\n  3. Else if num < 0: print Negative\n  4. Else: print Zero",
        ],
        hint_1="Use an `if (num > 0)` branch for strictly positive values.",
        hint_2="Use `else if (num < 0)` for negative values.",
        hint_3="Use a terminal `else` branch for when the number is exactly zero.",
        hint_4="Algorithm NumberSignClassifier:\n  1. Read num\n  2. If num > 0: print Positive\n  3. Else if num < 0: print Negative\n  4. Else: print Zero",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 9. STRUCTURES: Student Record Formatter (Custom Aggregate Types)
    # --------------------------------------------------------------------------
    "Structures": CanonicalCodingQuestion(
        question_id="q_struct_student_v1",
        version="1.0.0",
        topic="Structures",
        subtopic="struct_decl_access",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Define heterogeneous aggregate types with struct and access fields with the dot member operator in C.",
        title="Student Record Formatter Using Struct",
        problem_statement=(
            "Define a structure `struct Student` with fields `int id` and `int marks`.\n"
            "Read `id` and `marks` from standard input, populate the structure, and print them formatted as `ID: <id>, Marks: <marks>`."
        ),
        input_format="Two space-separated integers: id and marks.",
        output_format="Formatted string: ID: <id>, Marks: <marks> followed by a newline.",
        constraints="1 <= id <= 10000; 0 <= marks <= 100; valid C99 struct.",
        algorithmic_approach="Heterogeneous record aggregation and direct member access.",
        pseudocode=(
            "Algorithm StudentRecordFormatter:\n"
            "  1. Declare struct Student with fields int id and int marks\n"
            "  2. In main():\n"
            "     a. Instantiate variable s of type struct Student\n"
            "     b. Read s.id and s.marks using scanf(\"%d %d\", &s.id, &s.marks)\n"
            "     c. Print record: printf(\"ID: %d, Marks: %d\\n\", s.id, s.marks)\n"
            "     d. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "struct Student {\n"
            "    int id;\n"
            "    int marks;\n"
            "};\n\n"
            "int main(void) {\n"
            "    struct Student s = {0, 0};\n"
            "    if (scanf(\"%d %d\", &s.id, &s.marks) == 2) {\n"
            "        // Write your implementation here: print formatted as \"ID: <id>, Marks: <marks>\\n\"\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "struct Student {\n"
            "    int id;\n"
            "    int marks;\n"
            "};\n\n"
            "int main(void) {\n"
            "    struct Student s = {0, 0};\n"
            "    if (scanf(\"%d %d\", &s.id, &s.marks) == 2) {\n"
            "        printf(\"ID: %d, Marks: %d\\n\", s.id, s.marks);\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="101 95",
        sample_output="ID: 101, Marks: 95",
        sample_explanation="Structure fields s.id and s.marks are populated with 101 and 95 and printed formatted.",
        expected_test_cases=[
            {"input": "101 95", "expected_output": "ID: 101, Marks: 95"},
            {"input": "202 88", "expected_output": "ID: 202, Marks: 88"},
        ],
        hidden_test_cases=[
            {"input": "5 100", "expected_output": "ID: 5, Marks: 100"},
            {"input": "999 0", "expected_output": "ID: 999, Marks: 0"},
        ],
        hints=[
            "Declare `struct Student { int id; int marks; };` before `main()`.",
            "Instantiate the variable: `struct Student s;`.",
            "Access structure members using the dot member operator: `&s.id` and `&s.marks` in `scanf`.",
            "Algorithm StudentRecordFormatter:\n  1. Define struct Student { int id; int marks; }\n  2. Read s.id and s.marks\n  3. Print 'ID: %d, Marks: %d\\n'",
        ],
        hint_1="Declare `struct Student { int id; int marks; };` before `main()`.",
        hint_2="Instantiate the variable: `struct Student s;`.",
        hint_3="Access structure members using the dot member operator: `&s.id` and `&s.marks` in `scanf`.",
        hint_4="Algorithm StudentRecordFormatter:\n  1. Define struct Student { int id; int marks; }\n  2. Read s.id and s.marks\n  3. Print 'ID: %d, Marks: %d\\n'",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 10. OPERATORS AND EXPRESSIONS: Precedence Evaluator (Multiple-Integer Question)
    # --------------------------------------------------------------------------
    "Operators and Expressions": CanonicalCodingQuestion(
        question_id="q_op_prec_v1",
        version="1.0.0",
        topic="Operators and Expressions",
        subtopic="op_precedence_assoc",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Apply arithmetic operator precedence and grouping parentheses to evaluate numeric expressions in C.",
        title="Arithmetic Precedence Evaluator",
        problem_statement=(
            "Write a C program that reads three integers `a`, `b`, and `c` from standard input and evaluates the expression `(a + b) * c`.\n"
            "Print the integer result followed by a newline."
        ),
        input_format="Three space-separated integers on standard input.",
        output_format="The integer result of (a + b) * c followed by a newline.",
        constraints="-1000 <= a, b, c <= 1000; standard operator evaluation.",
        algorithmic_approach="Explicit parenthetical expression evaluation overriding default precedence.",
        pseudocode=(
            "Algorithm ArithmeticPrecedenceEvaluator:\n"
            "  1. Declare integers a <- 0, b <- 0, c <- 0\n"
            "  2. Read a, b, c using scanf(\"%d %d %d\", &a, &b, &c)\n"
            "  3. Evaluate result <- (a + b) * c\n"
            "  4. Print result formatted as \"%d\\n\"\n"
            "  5. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int a = 0, b = 0, c = 0;\n"
            "    if (scanf(\"%d %d %d\", &a, &b, &c) == 3) {\n"
            "        // Write your implementation here: evaluate (a + b) * c and print the result\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    int a = 0, b = 0, c = 0;\n"
            "    if (scanf(\"%d %d %d\", &a, &b, &c) == 3) {\n"
            "        int result = (a + b) * c;\n"
            "        printf(\"%d\\n\", result);\n"
            "    }\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="3 4 5",
        sample_output="35",
        sample_explanation="(3 + 4) * 5 = 7 * 5 = 35. Parentheses ensure addition executes before multiplication.",
        expected_test_cases=[
            {"input": "3 4 5", "expected_output": "35"},
            {"input": "2 3 4", "expected_output": "20"},
        ],
        hidden_test_cases=[
            {"input": "0 10 2", "expected_output": "20"},
            {"input": "-5 5 10", "expected_output": "0"},
            {"input": "1 1 1", "expected_output": "2"},
        ],
        hints=[
            "Parentheses `()` have higher precedence than the multiplication `*` and addition `+` operators.",
            "Group `(a + b)` so addition occurs first.",
            "Multiply the sum by `c`: `(a + b) * c`.",
            "Algorithm ArithmeticPrecedenceEvaluator:\n  1. Read a, b, c\n  2. Compute (a + b) * c\n  3. Print '%d\\n', result",
        ],
        hint_1="Parentheses `()` have higher precedence than the multiplication `*` and addition `+` operators.",
        hint_2="Group `(a + b)` so addition occurs first.",
        hint_3="Multiply the sum by `c`: `(a + b) * c`.",
        hint_4="Algorithm ArithmeticPrecedenceEvaluator:\n  1. Read a, b, c\n  2. Compute (a + b) * c\n  3. Print '%d\\n', result",
        validation_status=ValidationStatus.VERIFIED,
    ),

    # --------------------------------------------------------------------------
    # 11. VARIABLES AND DATA TYPES: Primitive Type Sizes
    # --------------------------------------------------------------------------
    "Variables and Data Types": CanonicalCodingQuestion(
        question_id="q_var_sizeof_v1",
        version="1.0.0",
        topic="Variables and Data Types",
        subtopic="var_primitives",
        difficulty="Beginner",
        mastery_tier="Beginner",
        learning_objective="Inspect memory byte allocations of primitive C data types with the sizeof operator.",
        title="C Primitive Data Type Footprints",
        problem_statement=(
            "Write a C program that prints the byte size of standard C datatypes: `char`, `int`, and `float`.\n"
            "Output must be formatted exactly as: `char: 1, int: 4, float: 4` followed by a newline."
        ),
        input_format="No standard input required.",
        output_format="char: 1, int: 4, float: 4 followed by a newline.",
        constraints="Use standard sizeof operator on standard 32/64-bit architecture.",
        algorithmic_approach="Compile-time memory type introspection.",
        pseudocode=(
            "Algorithm PrimitiveTypeFootprints:\n"
            "  1. In main():\n"
            "     a. Query sizeof(char), sizeof(int), and sizeof(float)\n"
            "     b. Print formatted string: \"char: %zu, int: %zu, float: %zu\\n\", sizeof(char), sizeof(int), sizeof(float)\n"
            "     c. Return 0"
        ),
        question_type=QuestionType.FULL_PROGRAM,
        starter_code=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    // Write your implementation here: print char, int, float sizes formatted as \"char: %zu, int: %zu, float: %zu\\n\"\n"
            "    return 0;\n"
            "}\n"
        ),
        reference_solution=(
            "#include <stdio.h>\n\n"
            "int main(void) {\n"
            "    printf(\"char: %zu, int: %zu, float: %zu\\n\", sizeof(char), sizeof(int), sizeof(float));\n"
            "    return 0;\n"
            "}\n"
        ),
        sample_input="",
        sample_output="char: 1, int: 4, float: 4",
        sample_explanation="sizeof(char) is guaranteed 1 byte in C; int and float are 4 bytes on standard target systems.",
        expected_test_cases=[
            {"input": "", "expected_output": "char: 1, int: 4, float: 4"},
        ],
        hidden_test_cases=[
            {"input": "", "expected_output": "char: 1, int: 4, float: 4"},
        ],
        hints=[
            "Use the `sizeof(type)` operator to query byte sizes.",
            "Format using `%zu` specifier for `size_t` return types in C99.",
            "Print the exact formatted output: `char: %zu, int: %zu, float: %zu\\n`.",
            "Algorithm PrimitiveTypeFootprints:\n  1. Print 'char: %zu, int: %zu, float: %zu\\n' with sizeof(char), sizeof(int), sizeof(float)",
        ],
        hint_1="Use the `sizeof(type)` operator to query byte sizes.",
        hint_2="Format using `%zu` specifier for `size_t` return types in C99.",
        hint_3="Print the exact formatted output: `char: %zu, int: %zu, float: %zu\\n`.",
        hint_4="Algorithm PrimitiveTypeFootprints:\n  1. Print 'char: %zu, int: %zu, float: %zu\\n' with sizeof(char), sizeof(int), sizeof(float)",
        validation_status=ValidationStatus.VERIFIED,
    ),
}


def get_canonical_question(topic: str) -> CanonicalCodingQuestion:
    """Retrieve verified canonical coding question for the specified topic."""
    from eduadapt.teaching.response_schema import normalize_topic_name
    norm = normalize_topic_name(topic)
    return CANONICAL_QUESTIONS.get(norm) or CANONICAL_QUESTIONS.get("Pointers")
