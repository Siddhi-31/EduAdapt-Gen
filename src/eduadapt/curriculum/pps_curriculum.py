"""Canonical PPS (Programming for Problem Solving) Curriculum Hierarchy.

Defines the parent-topic and subtopic tree across all 5 units of the PPS syllabus.
Provides subtopic metadata, prerequisites, learning objectives, and pedagogical guidance
for Beginner, Intermediate, and Advanced tiers.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class SubtopicNode:
    """Individual subtopic curriculum unit."""
    id: str
    title: str
    parent_topic: str
    order: int
    prerequisites: List[str] = field(default_factory=list)
    learning_objective: str = ""
    key_concepts: List[str] = field(default_factory=list)
    beginner_guidance: str = ""
    intermediate_guidance: str = ""
    advanced_guidance: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "parent_topic": self.parent_topic,
            "order": self.order,
            "prerequisites": self.prerequisites,
            "learning_objective": self.learning_objective,
            "key_concepts": self.key_concepts,
            "beginner_guidance": self.beginner_guidance,
            "intermediate_guidance": self.intermediate_guidance,
            "advanced_guidance": self.advanced_guidance,
        }


# Complete PPS Syllabus Subtopic Registry
PPS_CURRICULUM_TREE: Dict[str, List[SubtopicNode]] = {
    "Pointers": [
        SubtopicNode(
            id="ptr_intro_addresses",
            title="Introduction to Memory Addresses and Pointer Concept",
            parent_topic="Pointers",
            order=1,
            prerequisites=[],
            learning_objective="Understand how variables occupy RAM, what a memory address represents, and how pointers store addresses.",
            key_concepts=["RAM cells", "Byte addresses", "Hexadecimal address representation", "Pointer variable concept"],
            beginner_guidance="Explain what a variable is in memory using an intuitive house address or locker analogy. Avoid pointer arithmetic or complex syntax.",
            intermediate_guidance="Recap memory address spaces, stack frame layout, and sizeof(pointer) on 32-bit vs 64-bit architectures.",
            advanced_guidance="Explore virtual address spaces, memory alignment boundaries, and hardware architecture address models.",
        ),
        SubtopicNode(
            id="ptr_decl_init",
            title="Pointer Declaration and Initialization",
            parent_topic="Pointers",
            order=2,
            prerequisites=["ptr_intro_addresses"],
            learning_objective="Declare pointer variables of various types and safely initialize them to variable addresses or NULL.",
            key_concepts=["int *ptr syntax", "Asterisk binding", "Initialization at declaration", "Uninitialized pointer danger"],
            beginner_guidance="Show exact line-by-line syntax: int *p = &x. Explain that * in declaration specifies the type, not dereference.",
            intermediate_guidance="Contrast int* p, q (where q is int) with int *p, *q. Emphasize type compatibility.",
            advanced_guidance="Analyze compiler warning diagnostics with incompatible pointer assignments and const qualifiers (const int * vs int * const).",
        ),
        SubtopicNode(
            id="ptr_operators",
            title="Address-of (&) and Dereference (*) Operators",
            parent_topic="Pointers",
            order=3,
            prerequisites=["ptr_decl_init"],
            learning_objective="Distinguish between the address-of operator (&) and dereference operator (*) and use them to read and write memory.",
            key_concepts=["& operator (address-of)", "* operator (indirection/dereference)", "L-value vs R-value dereferencing"],
            beginner_guidance="Clarify the duality: & gets the address, * follows the address to the value. Provide a visual arrow diagram. Practice small code.",
            intermediate_guidance="Trace execution with multiple variables and intermediate pointer reassignment. Include output prediction.",
            advanced_guidance="Demonstrate chained indirection, operator precedence with prefix/postfix operators (*ptr++, (*ptr)++), and memory modification side-effects.",
        ),
        SubtopicNode(
            id="ptr_arithmetic",
            title="Pointer Arithmetic and Type Scaling",
            parent_topic="Pointers",
            order=4,
            prerequisites=["ptr_operators"],
            learning_objective="Perform pointer addition, subtraction, and comparisons, understanding scaling by sizeof(type).",
            key_concepts=["ptr + 1 scaling", "sizeof(type) byte jumps", "Pointer subtraction (ptrdiff_t)", "Illegal pointer arithmetic operations"],
            beginner_guidance="Explain why ptr + 1 does NOT mean address + 1 byte for integers. Use visual memory boxes showing 4-byte steps.",
            intermediate_guidance="Demonstrate array traversal using pointers and calculating element distances via pointer subtraction.",
            advanced_guidance="Explore undefined behavior when navigating beyond array bounds (arr + N), pointer comparisons across different blocks, and compiler optimizations.",
        ),
        SubtopicNode(
            id="ptr_arrays",
            title="Pointers and Array Equivalence",
            parent_topic="Pointers",
            order=5,
            prerequisites=["ptr_arithmetic"],
            learning_objective="Understand the relationship between arrays and pointers in C, array name decay, and subscripting equivalence.",
            key_concepts=["Array name as constant pointer", "arr[i] == *(arr + i)", "Array decay in expressions", "sizeof(arr) vs sizeof(ptr)"],
            beginner_guidance="Show that arr[0] is *arr and arr[i] is *(arr + i). Highlight that array names cannot be reassigned (arr++ is illegal).",
            intermediate_guidance="Navigate 2D arrays via pointers, row pointers, and pointer offsets in matrix calculations.",
            advanced_guidance="Deconstruct array-to-pointer decay nuances, decay suppression in sizeof and & operators, and VLA pointer arithmetic.",
        ),
        SubtopicNode(
            id="ptr_strings",
            title="Pointers and Strings",
            parent_topic="Pointers",
            order=6,
            prerequisites=["ptr_arrays"],
            learning_objective="Manipulate null-terminated strings using character pointers and pointer traversal.",
            key_concepts=["char *str vs char str[]", "String literals in read-only memory", "Traversing until '\\0'", "Pointer-based string algorithms"],
            beginner_guidance="Explain how char *p points to the first character and advances until '\\0'. Warn against modifying string literals.",
            intermediate_guidance="Implement custom string functions (my_strlen, my_strcpy) using idiomatic pointer loops (while (*dest++ = *src++)).",
            advanced_guidance="Analyze memory segmentation: data section (read-only) vs stack arrays, segmentation faults on literal mutation, and memory alignment.",
        ),
        SubtopicNode(
            id="ptr_functions",
            title="Pointers and Functions (Call by Reference)",
            parent_topic="Pointers",
            order=7,
            prerequisites=["ptr_operators"],
            learning_objective="Implement call-by-reference semantics in C by passing memory addresses to functions to mutate caller state.",
            key_concepts=["Call by value limitation", "Simulating pass by reference", "Swap function implementation", "Returning pointers safely"],
            beginner_guidance="Walk through the classic swap(&a, &b) problem. Explain why regular pass-by-value fails to swap values outside the function.",
            intermediate_guidance="Design modular functions returning multiple results via pointer output arguments. Emphasize const-correctness for read-only pointer params.",
            advanced_guidance="Analyze stack frame lifecycle: demonstrate why returning the address of a local automatic variable leads to undefined behavior / dangling pointers.",
        ),
        SubtopicNode(
            id="ptr_to_ptr",
            title="Pointer to Pointer (Double Indirection)",
            parent_topic="Pointers",
            order=8,
            prerequisites=["ptr_operators"],
            learning_objective="Understand double indirection (int **ptr), pointer variables that store addresses of other pointers.",
            key_concepts=["Double asterisk syntax (**)", "Memory address of a pointer", "Modifying pointer variables inside functions", "Dynamic 2D allocation"],
            beginner_guidance="Use a two-step chain analogy: key to a box that contains another key. Show visual two-hop diagram.",
            intermediate_guidance="Use double pointers to allocate dynamic 2D matrices (array of pointers) and modify caller pointer variables in functions.",
            advanced_guidance="Explore triple indirection, command line arguments (char **argv), and ragged dynamic data structures.",
        ),
        SubtopicNode(
            id="ptr_safety_debugging",
            title="NULL, Dangling, Wild Pointers and Debugging",
            parent_topic="Pointers",
            order=9,
            prerequisites=["ptr_operators"],
            learning_objective="Identify, debug, and prevent NULL pointer dereferences, wild pointers, and dangling pointers in C.",
            key_concepts=["NULL macro and nullptr", "Dangling pointer after free or scope exit", "Wild (uninitialized) pointers", "Defensive pointer coding"],
            beginner_guidance="Show what NULL is (safe zero address). Teach the golden rule: initialize pointers to NULL, check before dereferencing, set to NULL after free.",
            intermediate_guidance="Trace memory bugs causing segmentation faults. Use debug prints and address sanitizers to pinpoint invalid accesses.",
            advanced_guidance="Analyze use-after-free vulnerabilities, double-free corruption, buffer under/overflows, and memory auditing best practices.",
        ),
    ],
    "Loops": [
        SubtopicNode(
            id="loop_while",
            title="While Loop and Entry-Controlled Iteration",
            parent_topic="Loops",
            order=1,
            prerequisites=[],
            learning_objective="Understand entry-controlled looping using while, condition testing, and termination predicates.",
            key_concepts=["Entry condition check", "Loop body", "Counter variable initialization", "Termination condition"],
            beginner_guidance="Explain looping as repeating steps while a light is green. Show initialization, condition, body, increment step-by-step.",
            intermediate_guidance="Write sentinel-controlled loops, accumulator patterns, and handle multi-condition while statements.",
            advanced_guidance="Analyze loop invariants, termination proofs, and compiler optimizations like loop unrolling.",
        ),
        SubtopicNode(
            id="loop_for",
            title="For Loop Mechanics and Multi-Variable Headers",
            parent_topic="Loops",
            order=2,
            prerequisites=["loop_while"],
            learning_objective="Master for loop structure: initialization, condition, update expressions, and loop scoping.",
            key_concepts=["Header structure (init; cond; step)", "Variable scope in C99 for loops", "Comma operator in headers", "Counting loops"],
            beginner_guidance="Break down for (init; test; step) into its 3 explicit sections. Trace counter values on paper.",
            intermediate_guidance="Implement multi-index loops using comma operator, reverse iteration, and step increments other than 1.",
            advanced_guidance="Discuss infinite for (;;) loops, omitted header components, side effects in step expressions, and cache locality.",
        ),
        SubtopicNode(
            id="loop_dowhile",
            title="Do-While Loop and Exit-Controlled Iteration",
            parent_topic="Loops",
            order=3,
            prerequisites=["loop_while"],
            learning_objective="Understand exit-controlled execution where the body is guaranteed to run at least once.",
            key_concepts=["Exit-condition check", "Guaranteed single execution", "Menu-driven programs", "Semicolon requirement after while(cond);"],
            beginner_guidance="Emphasize the critical difference: do-while checks condition AFTER running the body. Point out the trailing semicolon.",
            intermediate_guidance="Implement interactive menu systems and input validation loops requiring repeated user prompts.",
            advanced_guidance="Contrast assembly generation of entry vs exit controlled loops and jump instructions.",
        ),
        SubtopicNode(
            id="loop_control_statements",
            title="Loop Jump Statements: Break and Continue",
            parent_topic="Loops",
            order=4,
            prerequisites=["loop_for"],
            learning_objective="Direct loop execution flow using break (immediate exit) and continue (skip to next iteration).",
            key_concepts=["break statement semantics", "continue statement semantics", "Flow chart divergence", "Avoiding goto"],
            beginner_guidance="Show break as 'emergency exit' and continue as 'skip rest of this turn'. Trace with simple numbers.",
            intermediate_guidance="Apply break for early search termination and continue for filtering invalid data items.",
            advanced_guidance="Explain continue behavior difference between while (skips step) vs for (executes step expression).",
        ),
        SubtopicNode(
            id="loop_nested",
            title="Nested Loops and Pattern Printing",
            parent_topic="Loops",
            order=5,
            prerequisites=["loop_for"],
            learning_objective="Coordinate multi-level nested loops to traverse grids, generate geometric patterns, and process 2D data.",
            key_concepts=["Outer loop vs inner loop", "Total iteration calculation (O(N*M))", "Resetting inner counter", "2D coordinate grids"],
            beginner_guidance="Use clock hands analogy: outer loop is hour hand, inner loop is minute hand. Draw row-by-row output.",
            intermediate_guidance="Generate triangle, pyramid, and numerical patterns. Trace loop variable dependencies (e.g. inner runs up to outer).",
            advanced_guidance="Analyze algorithmic time complexity of nested structures and optimize loop interchange for memory cache hierarchies.",
        ),
    ],
    "Arrays": [
        SubtopicNode(
            id="arr_1d_decl",
            title="One-Dimensional Array Declaration and Memory Layout",
            parent_topic="Arrays",
            order=1,
            prerequisites=[],
            learning_objective="Declare, initialize, and understand the contiguous memory layout of 1D arrays in C.",
            key_concepts=["Contiguous memory allocation", "Fixed compile-time size", "Zero-based indexing", "sizeof(array)"],
            beginner_guidance="Show an array as a row of connected mailboxes with indices 0 to N-1. Emphasize zero-based indexing.",
            intermediate_guidance="Demonstrate partial initialization (int arr[5] = {1, 2}), designated initializers in C99, and stack bounds.",
            advanced_guidance="Analyze memory alignment and padding in arrays of compound types and stack allocation limits.",
        ),
        SubtopicNode(
            id="arr_traversal",
            title="Array Indexing, Bounds Checking, and Traversal",
            parent_topic="Arrays",
            order=2,
            prerequisites=["arr_1d_decl"],
            learning_objective="Traverse arrays using loops, read/write elements, and avoid out-of-bounds errors.",
            key_concepts=["Array traversal loops", "No runtime bounds checking in C", "Buffer overflow risk", "Index computation"],
            beginner_guidance="Trace loop index i from 0 to size-1. Warn that arr[size] is out of bounds and dangerous.",
            intermediate_guidance="Implement classic array algorithms: linear search, finding min/max, reversing array in-place.",
            advanced_guidance="Analyze memory corruption and security vulnerabilities stemming from off-by-one out-of-bounds writes.",
        ),
        SubtopicNode(
            id="arr_2d_matrices",
            title="Two-Dimensional Arrays and Matrix Operations",
            parent_topic="Arrays",
            order=3,
            prerequisites=["arr_traversal"],
            learning_objective="Declare, populate, and manipulate 2D arrays in row-major order.",
            key_concepts=["Row-major memory storage", "Row and column indices arr[r][c]", "Matrix addition and multiplication", "2D initialization"],
            beginner_guidance="Visualize a table of rows and columns. Show how nested loops map outer loop to rows and inner loop to columns.",
            intermediate_guidance="Implement matrix operations: transpose, symmetric check, matrix multiplication with dimension validation.",
            advanced_guidance="Deconstruct row-major address calculation formula: Base + (row * cols + col) * sizeof(type).",
        ),
        SubtopicNode(
            id="arr_functions",
            title="Passing Arrays to Functions and Array Decay",
            parent_topic="Arrays",
            order=4,
            prerequisites=["arr_traversal"],
            learning_objective="Pass arrays to functions safely by passing the base address and explicit array length.",
            key_concepts=["Array decay to pointer", "Explicit length parameter necessity", "Modifying array elements inside functions", "const array parameters"],
            beginner_guidance="Explain why functions need both the array and its size passed as arguments. Show how changes persist outside.",
            intermediate_guidance="Pass 2D arrays to functions: explain why column dimensions must be explicitly specified in parameters.",
            advanced_guidance="Compare C99 Variable Length Arrays (VLA) in function headers with pointer-to-pointer dynamically passed matrices.",
        ),
    ],
    "Strings": [
        SubtopicNode(
            id="str_basics_null",
            title="Character Arrays and the Null Terminator ('\\0')",
            parent_topic="Strings",
            order=1,
            prerequisites=[],
            learning_objective="Understand how C represents strings as null-terminated character sequences.",
            key_concepts=["Null character '\\0' (ASCII 0)", "Array size = length + 1", "String literals", "printf %s format"],
            beginner_guidance="Explain that C has no native 'string' primitive—only character arrays ending with '\\0'. Draw memory boxes with '\\0'.",
            intermediate_guidance="Contrast char str[5] = \"hello\" (compile error/missing null) with char str[] = \"hello\".",
            advanced_guidance="Analyze string pooling in compilers, read-only memory sections, and security implications of unterminated strings.",
        ),
        SubtopicNode(
            id="str_io",
            title="String Input and Output Operations",
            parent_topic="Strings",
            order=2,
            prerequisites=["str_basics_null"],
            learning_objective="Read and write strings safely using standard C I/O functions.",
            key_concepts=["scanf %s limitation (whitespace break)", "fgets() buffer-safe input", "puts() vs printf()", "Stripping trailing newline"],
            beginner_guidance="Explain why scanf(\"%s\") stops at spaces. Teach fgets(str, sizeof(str), stdin) as the safe standard practice.",
            intermediate_guidance="Handle newline trimming from fgets and clear lingering input buffer characters safely.",
            advanced_guidance="Analyze buffer overflow attacks using deprecated gets() and format string vulnerabilities in printf.",
        ),
        SubtopicNode(
            id="str_library_functions",
            title="Standard String Manipulation Functions (<string.h>)",
            parent_topic="Strings",
            order=3,
            prerequisites=["str_basics_null"],
            learning_objective="Use and implement standard string functions: strlen, strcpy, strcat, and strcmp.",
            key_concepts=["strlen() vs sizeof()", "strcpy() and strncpy()", "strcat() and strncat()", "strcmp() lexicographical comparison"],
            beginner_guidance="Walk through each function: strlen counts until '\\0', strcmp returns 0 if strings match, strcpy copies characters.",
            intermediate_guidance="Write custom implementations of strlen and strcmp using loops. Explain why bounded functions (strncat) are safer.",
            advanced_guidance="Implement high-performance vector/pointer string routines and explore strstr, strtok, and locale-aware comparisons.",
        ),
    ],
    "Functions": [
        SubtopicNode(
            id="fn_decl_def",
            title="Function Declaration, Definition, and Prototypes",
            parent_topic="Functions",
            order=1,
            prerequisites=[],
            learning_objective="Structure modular C programs using function declarations, prototypes, and definitions.",
            key_concepts=["Function prototype header", "Return types", "Parameter lists", "Forward declaration necessity"],
            beginner_guidance="Explain functions as reusable machines that take inputs, do work, and return an output. Show prototype before main.",
            intermediate_guidance="Organize multi-function code, header files, and understand compiler type-checking enabled by prototypes.",
            advanced_guidance="Analyze linkage (extern vs static functions) and inline function optimizations.",
        ),
        SubtopicNode(
            id="fn_call_by_value",
            title="Parameter Passing and Call Stack Frames",
            parent_topic="Functions",
            order=2,
            prerequisites=["fn_decl_def"],
            learning_objective="Understand pass-by-value semantics and how the call stack allocates and unwinds function frames.",
            key_concepts=["Pass by value copy semantics", "Activation records (stack frames)", "Scope of local variables", "Stack unwinding on return"],
            beginner_guidance="Show that modifying a parameter inside a function does NOT alter the original variable in main. Draw stack frames.",
            intermediate_guidance="Trace memory addresses of caller vs callee variables to prove independent memory locations.",
            advanced_guidance="Inspect calling conventions (cdecl, ABI), register parameter passing, and stack frame pointer management.",
        ),
        SubtopicNode(
            id="fn_recursion",
            title="Recursion Principles and Base Cases",
            parent_topic="Functions",
            order=3,
            prerequisites=["fn_call_by_value"],
            learning_objective="Implement recursive functions with correct base cases and progress steps to prevent stack overflow.",
            key_concepts=["Base case terminating condition", "Recursive leap of faith", "Call stack buildup", "Stack overflow risk"],
            beginner_guidance="Break down recursion into two parts: 1) When to STOP (base case), 2) How to simplify the problem (recursive step). Use factorial.",
            intermediate_guidance="Trace recursive call stacks step-by-step for Fibonacci and GCD. Compute call tree depth.",
            advanced_guidance="Contrast head vs tail recursion, compiler tail-call optimization (TCO), and recursion-to-iteration transformations.",
        ),
    ],
    "Variables and Data Types": [
        SubtopicNode(
            id="var_primitives",
            title="Fundamental Data Types and sizeof Operator",
            parent_topic="Variables and Data Types",
            order=1,
            prerequisites=[],
            learning_objective="Identify and declare fundamental types (int, char, float, double) and query their memory footprints.",
            key_concepts=["int, char, float, double", "Signed vs unsigned specifiers", "sizeof operator in C", "Range and precision"],
            beginner_guidance="Introduce integer, character, and decimal numbers with simple everyday examples. Show sizeof output.",
            intermediate_guidance="Explain 2's complement representation for signed integers, float IEEE 754 precision, and integer overflow.",
            advanced_guidance="Analyze architecture-dependent type widths (LP64 vs LLP64), fixed-width integer types (<stdint.h>), and bitwise bit patterns.",
        ),
        SubtopicNode(
            id="var_scope_qualifiers",
            title="Variable Scope, Lifetime, and Type Casting",
            parent_topic="Variables and Data Types",
            order=2,
            prerequisites=["var_primitives"],
            learning_objective="Manage local vs global variable scope, storage classes, and explicit type conversion.",
            key_concepts=["Local block scope vs global scope", "Implicit vs explicit type casting", "const qualifier", "static variables"],
            beginner_guidance="Explain that variables inside { } only exist inside those braces. Show (float)a / b to avoid integer truncation.",
            intermediate_guidance="Demonstrate static local variables retaining values across calls, and arithmetic type promotion rules.",
            advanced_guidance="Explore volatile keyword in hardware-mapped memory, register storage hints, and sequence points in conversions.",
        ),
    ],
    "Operators and Expressions": [
        SubtopicNode(
            id="op_arith_rel_log",
            title="Arithmetic, Relational, and Logical Operators",
            parent_topic="Operators and Expressions",
            order=1,
            prerequisites=[],
            learning_objective="Construct expressions using arithmetic (+,-,*,/,%), relational (==,!=,<,>), and logical (&&,||,!) operators.",
            key_concepts=["Integer division truncation", "Modulus operator (%) with integers", "Boolean truth values (0 = False, non-zero = True)", "Short-circuit evaluation"],
            beginner_guidance="Explain that 7 / 2 evaluates to 3 in integer math. Clarify the difference between assignment (=) and comparison (==).",
            intermediate_guidance="Leverage logical short-circuit evaluation in guard conditions (e.g. ptr != NULL && *ptr > 0).",
            advanced_guidance="Analyze bitwise operators (&, |, ^, ~, <<, >>), mask manipulation, and undefined shifts.",
        ),
        SubtopicNode(
            id="op_precedence_assoc",
            title="Operator Precedence, Associativity, and Evaluation Order",
            parent_topic="Operators and Expressions",
            order=2,
            prerequisites=["op_arith_rel_log"],
            learning_objective="Evaluate complex C expressions deterministically according to precedence and associativity tables.",
            key_concepts=["Precedence hierarchy", "Left-to-right vs right-to-left associativity", "Parentheses override", "Sequence points"],
            beginner_guidance="Compare operator precedence to BODMAS/PEMDAS. Show how parentheses prevent unexpected evaluations.",
            intermediate_guidance="Trace expressions combining unary, arithmetic, and relational operators (e.g. *ptr++ vs (*ptr)++).",
            advanced_guidance="Examine undefined behavior in unsequenced modifications (i = i++ + ++i) and compiler evaluation liberties.",
        ),
    ],
    "Conditionals": [
        SubtopicNode(
            id="cond_if_else",
            title="Decision Making with If, If-Else, and Else-If Ladders",
            parent_topic="Conditionals",
            order=1,
            prerequisites=[],
            learning_objective="Implement branching logic using if, if-else chains, and multi-condition boolean guards.",
            key_concepts=["Condition evaluation (true/false)", "If-else branching", "Else-if ladder", "Dangling else ambiguity"],
            beginner_guidance="Explain if-else as a fork in the road: if condition is true, take path A; otherwise take path B. Emphasize { } braces.",
            intermediate_guidance="Structure clean multi-way decision ladders and resolve nested if-else dangling else ambiguities.",
            advanced_guidance="Analyze branch prediction hints, ternary operator expressions, and conditional execution bytecode.",
        ),
        SubtopicNode(
            id="cond_switch",
            title="Multi-Way Branching with Switch-Case Statements",
            parent_topic="Conditionals",
            order=2,
            prerequisites=["cond_if_else"],
            learning_objective="Use switch-case statements for discrete value dispatching, break statements, and default fallbacks.",
            key_concepts=["Integer/char expression requirement", "case labels and constants", "Fall-through behavior", "default label"],
            beginner_guidance="Compare switch to a menu: pick an option and jump directly to that case. Explain why 'break' is needed after each case.",
            intermediate_guidance="Implement menu dispatchers and intentional fall-through patterns for grouped cases.",
            advanced_guidance="Examine compiler switch optimization: jump tables vs binary search trees in assembly.",
        ),
    ],
    "Structures": [
        SubtopicNode(
            id="struct_decl_access",
            title="Structure Declaration, Memory Layout, and Dot Operator",
            parent_topic="Structures",
            order=1,
            prerequisites=[],
            learning_objective="Define custom heterogeneous data records using struct and access members via dot operator.",
            key_concepts=["Heterogeneous composite records", "struct declaration syntax", "Member access with dot (.)", "Structure memory layout"],
            beginner_guidance="Compare arrays (homogenous, same type) with structures (heterogeneous, e.g. student with id, name, and gpa).",
            intermediate_guidance="Declare arrays of structures, pass structures by value vs pointer, and use typedef for clean type aliases.",
            advanced_guidance="Analyze structure memory alignment, padding bytes, structure packing pragmas, and unions.",
        ),
        SubtopicNode(
            id="struct_pointers_arrow",
            title="Pointers to Structures and the Arrow Operator (->)",
            parent_topic="Structures",
            order=2,
            prerequisites=["struct_decl_access"],
            learning_objective="Manipulate structures through pointers using the arrow operator (->) for efficient parameter passing.",
            key_concepts=["struct Student *ptr", "Arrow operator (ptr->member)", "Equivalence to (*ptr).member", "Efficient pass-by-reference"],
            beginner_guidance="Explain that copying large structures wastes memory, so we pass a pointer. Show ptr->id as shorthand for (*ptr).id.",
            intermediate_guidance="Build self-referential structures (linked list node prototypes) with pointer members.",
            advanced_guidance="Implement opaque pointer design patterns and memory-efficient nested record representations in C.",
        ),
    ],
    "Dynamic Memory Allocation": [
        SubtopicNode(
            id="dma_malloc_free",
            title="Heap Allocation with malloc and Deallocation with free",
            parent_topic="Dynamic Memory Allocation",
            order=1,
            prerequisites=[],
            learning_objective="Allocate heap memory at runtime using malloc(), check for NULL, and release memory with free().",
            key_concepts=["Heap vs stack memory", "malloc(size * sizeof(type))", "NULL check validation", "free() and memory leak prevention"],
            beginner_guidance="Explain heap memory as rented storage: you must ask for it (malloc), check if granted (!= NULL), and return it (free).",
            intermediate_guidance="Dynamically allocate 1D arrays whose sizes are entered by users at runtime. Prevent dangling pointers by setting ptr = NULL.",
            advanced_guidance="Inspect heap fragmentation, metadata overhead of heap allocators, and memory debugging with Valgrind.",
        ),
        SubtopicNode(
            id="dma_calloc_realloc",
            title="Zeroed Allocation (calloc) and Resizing (realloc)",
            parent_topic="Dynamic Memory Allocation",
            order=2,
            prerequisites=["dma_malloc_free"],
            learning_objective="Allocate contiguous zero-initialized memory with calloc and expand or shrink allocations with realloc.",
            key_concepts=["calloc(count, size) zeroing", "realloc(ptr, new_size) mechanics", "Safe realloc temporary pointer pattern", "In-place vs relocated expansion"],
            beginner_guidance="Contrast malloc (uninitialized garbage values) with calloc (automatically zeroes out all bytes).",
            intermediate_guidance="Demonstrate growing dynamic arrays using realloc with proper temporary pointer assignment to avoid memory leaks on failure.",
            advanced_guidance="Analyze heap block coalescing, realloc pointer relocation implications, and building resizable dynamic vectors in C.",
        ),
    ],
}


def normalize_topic_key(topic: str) -> str:
    """Normalize any topic string to match PPS_CURRICULUM_TREE keys."""
    norm = topic.strip().lower()
    if "point" in norm:
        return "Pointers"
    elif "loop" in norm or "while" in norm or "for" in norm:
        return "Loops"
    elif "array" in norm:
        return "Arrays"
    elif "string" in norm:
        return "Strings"
    elif "func" in norm or "recur" in norm:
        return "Functions"
    elif "dynamic" in norm or "malloc" in norm or "dma" in norm or "heap" in norm:
        return "Dynamic Memory Allocation"
    elif "struct" in norm or "union" in norm:
        return "Structures"
    elif "cond" in norm or "if" in norm or "switch" in norm:
        return "Conditionals"
    elif "op" in norm or "expr" in norm:
        return "Operators and Expressions"
    elif "var" in norm or "type" in norm or "data" in norm:
        return "Variables and Data Types"
    return "Pointers"


def get_subtopics_for_topic(topic: str) -> List[SubtopicNode]:
    """Retrieve ordered subtopics list for a curriculum topic."""
    key = normalize_topic_key(topic)
    return PPS_CURRICULUM_TREE.get(key, PPS_CURRICULUM_TREE["Pointers"])


def get_subtopic_by_id(topic: str, subtopic_id: str) -> Optional[SubtopicNode]:
    """Find a specific subtopic by id or name."""
    subtopics = get_subtopics_for_topic(topic)
    sub_id_norm = subtopic_id.strip().lower()
    for s in subtopics:
        if s.id.lower() == sub_id_norm or s.title.lower() == sub_id_norm:
            return s
    # Fallback to first if not matched
    return subtopics[0] if subtopics else None


def get_curriculum_tree_summary() -> Dict[str, Any]:
    """Return JSON-serializable overview of all units, topics, and subtopics."""
    result = {}
    for parent_topic, subtopics in PPS_CURRICULUM_TREE.items():
        result[parent_topic] = [s.to_dict() for s in subtopics]
    return result
