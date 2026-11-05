"""Authoritative Bank of Subtopic Mastery-Check & Remedial Questions for EduAdapt.

Provides curated, verified, subtopic-specific questions with:
- Concrete C code or conceptual evaluation
- Explicit correct options
- Tailored misconception explanations for incorrect options
- Alternative remedial questions for students requiring a second attempt
"""

from typing import Any, Dict, Optional

SUBTOPIC_MASTERY_BANK: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # POINTERS
    # =========================================================================
    "ptr_intro_addresses": {
        "primary": {
            "id": "q_ptr_intro_1",
            "question": "In C, what does the expression `&val` evaluate to, where `val` is an integer variable?",
            "options": [
                "A) The integer value stored inside val",
                "B) The memory address (location in RAM) where val is stored",
                "C) The byte size of the variable val",
                "D) A pointer to NULL",
            ],
            "correct_option": "B",
            "explanation": "The address-of operator `&` retrieves the exact physical/virtual RAM address allocated for `val`.",
            "misconceptions": {
                "A": "You confused `&val` (address of) with `val` (the direct value stored in the variable).",
                "C": "To find the size of `val`, use `sizeof(val)`, not the address-of operator `&`.",
                "D": "An existing variable has an allocated stack address; it does not evaluate to NULL.",
            },
        },
        "remedial": {
            "id": "q_ptr_intro_rem",
            "question": "If `printf(\"%p\", (void*)&x);` prints `0x7ffee4`, what does `0x7ffee4` represent?",
            "options": [
                "A) The memory address where variable x is located in RAM",
                "B) The current numerical value assigned to x",
                "C) The data type identifier of x",
                "D) The return code of main()",
            ],
            "correct_option": "A",
            "explanation": "The format specifier `%p` prints memory addresses in hexadecimal format.",
            "misconceptions": {
                "B": "Memory addresses (like `0x7ffee4`) indicate location in RAM, not the value stored inside.",
            },
        },
    },
    "ptr_decl_init": {
        "primary": {
            "id": "q_ptr_decl_1",
            "question": "Which statement correctly declares an integer pointer `ptr` and initializes it to point to `num`?",
            "options": [
                "A) int *ptr = num;",
                "B) int *ptr = &num;",
                "C) int ptr = &num;",
                "D) *int ptr = &num;",
            ],
            "correct_option": "B",
            "explanation": "The asterisk in `int *ptr` specifies that `ptr` is a pointer to an `int`, and `&num` assigns the address of `num`.",
            "misconceptions": {
                "A": "`num` is an integer value, not an address. A pointer variable must store a memory address using `&num`.",
                "C": "`int ptr` declares a normal integer, not a pointer; assigning an address causes a type mismatch warning/error.",
                "D": "In C, the asterisk precedes the variable name (`int *ptr`), not the type keyword (`*int`).",
            },
        },
        "remedial": {
            "id": "q_ptr_decl_rem",
            "question": "What is the recommended initial value for a pointer that does not yet point to a valid object?",
            "options": [
                "A) 0 or NULL",
                "B) 1",
                "C) &main",
                "D) -1",
            ],
            "correct_option": "A",
            "explanation": "Initializing unused pointers to `NULL` (or 0) prevents dangerous wild pointer references and segmentation faults.",
            "misconceptions": {
                "B": "1 is an arbitrary memory address and causes access violations if dereferenced.",
                "D": "-1 is not a standard null pointer representation in C.",
            },
        },
    },
    "ptr_operators": {
        "primary": {
            "id": "q_ptr_ops_1",
            "question": "Given `int x = 10; int *p = &x; *p = 25;`, what is the value of `x` after execution?",
            "options": [
                "A) 10",
                "B) 25",
                "C) The memory address of p",
                "D) Undefined behavior",
            ],
            "correct_option": "B",
            "explanation": "`*p = 25` dereferences `p`, writing directly to the memory address of `x`, mutating `x` to 25.",
            "misconceptions": {
                "A": "Dereferencing `*p = 25` modifies the target variable `x`. It does not leave `x` unchanged.",
                "C": "`*p` accesses the integer value at `p`, not the address of `p`.",
                "D": "This is completely well-defined, safe pointer dereferencing in standard C.",
            },
        },
        "remedial": {
            "id": "q_ptr_ops_rem",
            "question": "If `p` holds the address of `y`, how do you read the value stored in `y` using `p`?",
            "options": [
                "A) By writing `*p`",
                "B) By writing `&p`",
                "C) By writing `p`",
                "D) By writing `y*p`",
            ],
            "correct_option": "A",
            "explanation": "The indirection (dereference) operator `*p` reads the contents of the target address held in `p`.",
            "misconceptions": {
                "B": "`&p` gives the address of the pointer variable `p` itself, not the value of `y`.",
                "C": "`p` evaluates to the address of `y`, not the value stored in `y`.",
            },
        },
    },
    "ptr_arithmetic": {
        "primary": {
            "id": "q_ptr_arith_1",
            "question": "If `int *ptr = 1000;` (assuming `sizeof(int) == 4`), what address does `ptr + 2` evaluate to?",
            "options": [
                "A) 1002",
                "B) 1008",
                "C) 1004",
                "D) 1016",
            ],
            "correct_option": "B",
            "explanation": "Pointer arithmetic scales offsets by `sizeof(*ptr)`. Adding 2 increments by `2 * 4 = 8` bytes, yielding 1008.",
            "misconceptions": {
                "A": "Pointer arithmetic is scaled by element byte size (`sizeof(type)`), not raw bytes.",
                "C": "Adding 2 scales by `2 * sizeof(int) = 8`, whereas 1004 would be `ptr + 1`.",
                "D": "1016 would be adding 4 integer elements (`4 * 4 = 16`).",
            },
        },
        "remedial": {
            "id": "q_ptr_arith_rem",
            "question": "Why does `p++` advance by 1 byte for `char *p`, but by 4 bytes for `int *p` (on a 32-bit int system)?",
            "options": [
                "A) Pointer arithmetic scales automatically by `sizeof(*p)`",
                "B) Compilers assign arbitrary step sizes to pointers",
                "C) char pointers are slower than int pointers",
                "D) The CPU cache enforces 4-byte steps for char",
            ],
            "correct_option": "A",
            "explanation": "C standard guarantees pointer arithmetic is scaled according to the byte size of the pointed-to type.",
            "misconceptions": {
                "B": "Step size is strictly deterministic: `sizeof(T)`.",
            },
        },
    },
    "ptr_arrays": {
        "primary": {
            "id": "q_ptr_arr_1",
            "question": "For an array `int arr[5] = {10, 20, 30, 40, 50};`, which expression is equivalent to `*(arr + 3)`?",
            "options": [
                "A) arr[3]",
                "B) arr[2]",
                "C) &arr[3]",
                "D) arr + 3",
            ],
            "correct_option": "A",
            "explanation": "In C, array subscript notation `arr[i]` is defined by the standard as syntactic sugar for `*(arr + i)`.",
            "misconceptions": {
                "B": "The offset is 3, which references the 4th element (index 3), not index 2.",
                "C": "`&arr[3]` is the address of the element, not the dereferenced element value.",
                "D": "`arr + 3` is a pointer to index 3; dereferencing with `*` gives the value.",
            },
        },
        "remedial": {
            "id": "q_ptr_arr_rem",
            "question": "What does an unadorned array name `arr` decay into in most C expressions?",
            "options": [
                "A) A pointer to its first element (`&arr[0]`)",
                "B) A copy of the entire array",
                "C) The length of the array in elements",
                "D) A NULL pointer",
            ],
            "correct_option": "A",
            "explanation": "Array decay converts the array name into a pointer to its first element (`&arr[0]`).",
            "misconceptions": {
                "B": "Arrays are never copied by value when evaluated in expressions.",
                "C": "Use `sizeof(arr)/sizeof(arr[0])` to compute length, not `arr` alone.",
            },
        },
    },
    "ptr_strings": {
        "primary": {
            "id": "q_ptr_str_1",
            "question": "What is the difference between `char str[] = \"Hello\";` and `char *ptr = \"Hello\";`?",
            "options": [
                "A) `str` is a mutable array on the stack, while `ptr` points to read-only string literal memory",
                "B) `str` cannot be modified, but `ptr` can modify its characters",
                "C) There is no difference; both are fully mutable",
                "D) `ptr` cannot be reassigned to point elsewhere",
            ],
            "correct_option": "A",
            "explanation": "`char str[]` allocates mutable stack space. `char *ptr` points to read-only literal storage; modifying `*ptr` is undefined behavior.",
            "misconceptions": {
                "B": "Attempting to modify `*ptr = 'h'` on a string literal typically triggers a segmentation fault.",
                "C": "String literals are stored in read-only segments (.rodata) on most modern architectures.",
            },
        },
        "remedial": {
            "id": "q_ptr_str_rem",
            "question": "How does a C string pointer determine where the string ends in memory?",
            "options": [
                "A) By encountering the null terminator character `\\0` (ASCII 0)",
                "B) By reading the 4-byte length prefix before the string",
                "C) By checking when a newline `\\n` occurs",
                "D) When it hits an unmapped RAM address",
            ],
            "correct_option": "A",
            "explanation": "C strings are null-terminated character sequences ending at `\\0`.",
            "misconceptions": {
                "B": "Standard C strings are null-terminated; they do not have a length header like Pascal strings.",
            },
        },
    },
    "ptr_functions": {
        "primary": {
            "id": "q_ptr_fn_1",
            "question": "How does passing arguments via pointers achieve 'Call by Reference' in C?",
            "options": [
                "A) The caller passes variable addresses, enabling the function to modify caller values directly via dereferencing",
                "B) C natively passes all variables by reference without copying anything",
                "C) Pointers prevent the function from creating any stack frame",
                "D) The return statement is automatically bypassed",
            ],
            "correct_option": "A",
            "explanation": "Passing an address allows the callee to dereference the pointer and mutate the caller's original variable.",
            "misconceptions": {
                "B": "C is strictly pass-by-value; call-by-reference is simulated by passing address values.",
                "C": "Every function call creates a stack frame regardless of argument types.",
            },
        },
        "remedial": {
            "id": "q_ptr_fn_rem",
            "question": "To swap two variables `a` and `b` in a helper function `void swap(...)`, what signature is required?",
            "options": [
                "A) `void swap(int *x, int *y)`",
                "B) `void swap(int x, int y)`",
                "C) `int swap(int x)`",
                "D) `void swap(&x, &y)`",
            ],
            "correct_option": "A",
            "explanation": "Pointers (`int *x, int *y`) are required so the function can mutate the caller's variables.",
            "misconceptions": {
                "B": "`void swap(int x, int y)` receives copies by value; swaps inside do not affect caller variables.",
            },
        },
    },
    "ptr_to_ptr": {
        "primary": {
            "id": "q_ptr_to_ptr_1",
            "question": "Given `int x = 50; int *p = &x; int **pp = &p;`, what does `**pp` evaluate to?",
            "options": [
                "A) 50",
                "B) The address of x",
                "C) The address of p",
                "D) A compilation error",
            ],
            "correct_option": "A",
            "explanation": "The first dereference `*pp` evaluates to `p`. The second dereference `*(*pp)` evaluates to `x`, which is 50.",
            "misconceptions": {
                "B": "`*pp` gives the address of `x` (`p`), but `**pp` double-dereferences to the value 50.",
                "C": "`pp` holds the address of `p`, but dereferencing twice reaches `x`.",
            },
        },
        "remedial": {
            "id": "q_ptr_to_ptr_rem",
            "question": "When is a pointer-to-pointer (`int **`) commonly needed in C functions?",
            "options": [
                "A) When a function needs to modify where a caller's pointer itself points (e.g. allocating memory for it)",
                "B) Only when doing floating point division",
                "C) Whenever printf is called",
                "D) It is never permitted in standard C",
            ],
            "correct_option": "A",
            "explanation": "To mutate a caller's pointer variable inside a function, you must pass the address of that pointer (`&ptr`), which has type `**`.",
            "misconceptions": {
                "D": "Double pointers (`**`) are standard C and essential for 2D dynamic arrays and pointer mutation.",
            },
        },
    },
    "ptr_safety_debugging": {
        "primary": {
            "id": "q_ptr_safety_1",
            "question": "What is a 'dangling pointer' in C?",
            "options": [
                "A) A pointer pointing to memory that has already been deallocated or gone out of scope",
                "B) A pointer explicitly initialized to NULL",
                "C) A pointer declared inside a loop",
                "D) A pointer to a constant integer",
            ],
            "correct_option": "A",
            "explanation": "A dangling pointer holds an address to storage that is no longer valid (e.g., after `free()` or returning a local stack variable address).",
            "misconceptions": {
                "B": "A pointer initialized to NULL is a safe null pointer, not a dangling pointer.",
                "C": "Declaring a pointer inside a loop does not make it dangling unless it points to destroyed storage.",
            },
        },
        "remedial": {
            "id": "q_ptr_safety_rem",
            "question": "What immediate action should always be taken after calling `free(ptr);` to prevent accidental dangling use?",
            "options": [
                "A) Set `ptr = NULL;`",
                "B) Call `free(ptr);` a second time",
                "C) Increment `ptr++`",
                "D) Delete the file containing ptr",
            ],
            "correct_option": "A",
            "explanation": "Setting `ptr = NULL;` after deallocation ensures that any subsequent check can detect the freed pointer.",
            "misconceptions": {
                "B": "Freeing memory twice causes a fatal double-free runtime crash or security vulnerability.",
            },
        },
    },

    # =========================================================================
    # DYNAMIC MEMORY ALLOCATION
    # =========================================================================
    "dma_malloc_free": {
        "primary": {
            "id": "q_dma_malloc_1",
            "question": "What does `malloc(sizeof(int) * 5)` return if the system runs out of heap memory?",
            "options": [
                "A) NULL",
                "B) A pointer to address 0xFFFFFFFF",
                "C) It terminates the program with SIGKILL",
                "D) An array of zeros",
            ],
            "correct_option": "A",
            "explanation": "`malloc` returns `NULL` when heap allocation fails. Always check `if (ptr == NULL)` before accessing allocated memory.",
            "misconceptions": {
                "C": "`malloc` returns NULL on failure rather than aborting, leaving error recovery to the programmer.",
                "D": "`calloc` zeros memory, but both return NULL when out of memory.",
            },
        },
        "remedial": {
            "id": "q_dma_malloc_rem",
            "question": "Where does `malloc()` allocate memory from during program execution?",
            "options": [
                "A) Heap segment",
                "B) Call stack segment",
                "C) Code (.text) segment",
                "D) CPU registers",
            ],
            "correct_option": "A",
            "explanation": "Dynamic memory allocation via `malloc`/`calloc` reserves bytes from the system Heap segment.",
            "misconceptions": {
                "B": "Local stack variables live in the call stack; dynamically allocated memory lives in the heap.",
            },
        },
    },
    "dma_calloc_realloc": {
        "primary": {
            "id": "q_dma_realloc_1",
            "question": "How does `calloc(n, size)` differ from `malloc(n * size)`?",
            "options": [
                "A) `calloc` initializes all allocated bytes to zero; `malloc` leaves bytes with indeterminate/garbage values",
                "B) `calloc` allocates on the stack, while `malloc` allocates on the heap",
                "C) `calloc` does not require checking for NULL",
                "D) `malloc` can only allocate 100 bytes maximum",
            ],
            "correct_option": "A",
            "explanation": "`calloc` clears and zero-initializes all bytes in the requested allocation block.",
            "misconceptions": {
                "B": "Both `calloc` and `malloc` allocate heap memory.",
                "C": "Both functions can fail and return NULL; both must be validated.",
            },
        },
        "remedial": {
            "id": "q_dma_realloc_rem",
            "question": "What is the purpose of `realloc(ptr, new_size)` in C?",
            "options": [
                "A) Resizes an existing heap allocation, preserving existing data up to the lesser of the old and new sizes",
                "B) Frees all pointers in the current function",
                "C) Converts an integer pointer to a char pointer",
                "D) Checks whether a pointer is NULL",
            ],
            "correct_option": "A",
            "explanation": "`realloc` dynamically shrinks or expands heap blocks while preserving existing data.",
            "misconceptions": {
                "B": "To free memory, use `free()`, not `realloc()`.",
            },
        },
    },

    # =========================================================================
    # ARRAYS
    # =========================================================================
    "arr_1d_decl": {
        "primary": {
            "id": "q_arr_decl_1",
            "question": "In C, what is the valid index range for an array declared as `int arr[10];`?",
            "options": [
                "A) 0 to 9",
                "B) 1 to 10",
                "C) 0 to 10",
                "D) -1 to 9",
            ],
            "correct_option": "A",
            "explanation": "C uses zero-based indexing. An array of size $N$ spans indices $0$ through $N-1$. Accessing index 10 is an out-of-bounds error.",
            "misconceptions": {
                "B": "C indices are 0-indexed, not 1-indexed.",
                "C": "Index 10 is the 11th element and constitutes out-of-bounds access.",
            },
        },
        "remedial": {
            "id": "q_arr_decl_rem",
            "question": "What happens if you initialize an array with fewer values than its size: `int a[5] = {1, 2};`?",
            "options": [
                "A) The remaining unlisted elements are automatically initialized to zero",
                "B) The program fails to compile",
                "C) The unlisted elements contain garbage values",
                "D) The array size shrinks to 2",
            ],
            "correct_option": "A",
            "explanation": "In C, partial aggregate initializers zero-initialize all remaining array elements.",
            "misconceptions": {
                "C": "Uninitialized elements only have garbage if the array has NO initializer at all.",
            },
        },
    },
    "arr_traversal": {
        "primary": {
            "id": "q_arr_trav_1",
            "question": "Which loop header correctly traverses all elements of `int arr[N]` from first to last?",
            "options": [
                "A) `for (int i = 0; i < N; i++)`",
                "B) `for (int i = 0; i <= N; i++)`",
                "C) `for (int i = 1; i <= N; i++)`",
                "D) `for (int i = N; i > 0; i--)`",
            ],
            "correct_option": "A",
            "explanation": "Visiting indices 0 through $N-1$ requires `i = 0; i < N; i++`. Using `<= N` accesses one element past the array boundary.",
            "misconceptions": {
                "B": "`i <= N` attempts to access `arr[N]`, causing an off-by-one out-of-bounds error.",
                "C": "Starting at 1 skips the first element at index 0.",
            },
        },
        "remedial": {
            "id": "q_arr_trav_rem",
            "question": "What runtime error can occur if a loop accesses `arr[i]` when `i >= array_size` in C?",
            "options": [
                "A) Buffer overflow / memory corruption / segmentation fault",
                "B) Automatic array reallocation",
                "C) Array wraps around to index 0",
                "D) Arithmetic overflow exception",
            ],
            "correct_option": "A",
            "explanation": "C does not perform bounds checking at runtime. Out-of-bounds reads/writes cause undefined behavior, memory corruption, or crashes.",
            "misconceptions": {
                "B": "C arrays have static sizes and never reallocate automatically.",
            },
        },
    },
    "arr_2d_matrices": {
        "primary": {
            "id": "q_arr_2d_1",
            "question": "How are elements of a 2D array `int m[3][4]` arranged in physical RAM?",
            "options": [
                "A) Row-major order (row 0 elements followed contiguously by row 1, then row 2)",
                "B) Column-major order",
                "C) Non-contiguous random blocks linked by pointers",
                "D) In reverse order from bottom right to top left",
            ],
            "correct_option": "A",
            "explanation": "C stores multi-dimensional arrays in contiguous row-major format, where the rightmost index varies fastest.",
            "misconceptions": {
                "B": "Fortran and MATLAB use column-major order; C strictly uses row-major order.",
            },
        },
        "remedial": {
            "id": "q_arr_2d_rem",
            "question": "How many total integer elements are allocated for `int matrix[4][5]`?",
            "options": [
                "A) 20",
                "B) 9",
                "C) 45",
                "D) 16",
            ],
            "correct_option": "A",
            "explanation": "Total elements = rows * cols = 4 * 5 = 20 integers.",
            "misconceptions": {
                "B": "Multiply row and column dimensions, do not add them.",
            },
        },
    },
    "arr_functions": {
        "primary": {
            "id": "q_arr_fn_1",
            "question": "When passing an array to a function `void modify(int arr[], int n)`, why are caller elements affected by changes?",
            "options": [
                "A) Because arrays decay into pointers to their first element, passing the address rather than copying data",
                "B) Because functions in C automatically duplicate memory back on return",
                "C) Arrays in C are global variables by default",
                "D) Only read operations are allowed in functions",
            ],
            "correct_option": "A",
            "explanation": "Array parameters decay to pointers (`int *arr`). The function operates directly on the caller's memory buffer.",
            "misconceptions": {
                "B": "No copy-back occurs; changes happen live through the decayed pointer.",
            },
        },
        "remedial": {
            "id": "q_arr_fn_rem",
            "question": "Why is it necessary to pass the array size `n` alongside an array to a C function?",
            "options": [
                "A) Because the decayed pointer does not carry length metadata, so the function cannot infer size with `sizeof`",
                "B) Because the C compiler rejects 1-argument functions",
                "C) Array size is needed to determine the return type",
                "D) To set the processor clock frequency",
            ],
            "correct_option": "A",
            "explanation": "Inside the function, `sizeof(arr)` evaluates to the size of a pointer (4 or 8 bytes), not the original array byte size.",
            "misconceptions": {
                "C": "The return type is declared at compile time and does not depend on array size.",
            },
        },
    },

    # =========================================================================
    # LOOPS
    # =========================================================================
    "loop_while": {
        "primary": {
            "id": "q_loop_while_1",
            "question": "What happens if the condition of a `while (cond)` loop is false on the very first evaluation?",
            "options": [
                "A) The loop body executes zero times",
                "B) The loop body executes once",
                "C) A compilation error occurs",
                "D) An infinite loop begins",
            ],
            "correct_option": "A",
            "explanation": "A while loop is a pre-test loop. If the condition is false initially, the body is never executed.",
            "misconceptions": {
                "B": "A `do-while` loop executes at least once, but a standard `while` loop checks before the first iteration.",
            },
        },
        "remedial": {
            "id": "q_loop_while_rem",
            "question": "What is the consequence of forgetting to update the loop counter variable inside a `while` loop?",
            "options": [
                "A) The loop may run indefinitely (infinite loop)",
                "B) The variable automatically increments by 1",
                "C) The compiler terminates the program safely",
                "D) The loop exits immediately",
            ],
            "correct_option": "A",
            "explanation": "Without updating the loop condition variable, the test never evaluates to false, causing an infinite loop.",
            "misconceptions": {
                "B": "C compilers never automatically insert updates into while loop bodies.",
            },
        },
    },
    "loop_for": {
        "primary": {
            "id": "q_loop_for_1",
            "question": "In the standard for loop header `for (A; B; C)`, what are components A, B, and C in order?",
            "options": [
                "A) Initialization, Condition check, Step/Update expression",
                "B) Condition check, Initialization, Final return",
                "C) Increment, Decrement, Break condition",
                "D) Declaration, Printing, Halting",
            ],
            "correct_option": "A",
            "explanation": "Standard for loop syntax consists of: initialization `A`, continuation test `B`, and iteration step `C`.",
            "misconceptions": {
                "B": "Initialization occurs first, followed by condition evaluation before each iteration.",
            },
        },
        "remedial": {
            "id": "q_loop_for_rem",
            "question": "How many iterations are executed by `for (int i = 0; i < 5; i++)`?",
            "options": [
                "A) 5 (for i = 0, 1, 2, 3, 4)",
                "B) 4",
                "C) 6",
                "D) 0",
            ],
            "correct_option": "A",
            "explanation": "The counter takes values 0, 1, 2, 3, 4. When `i` becomes 5, `5 < 5` is false and the loop terminates.",
            "misconceptions": {
                "B": "Index 0 is included, so values 0..4 make 5 total iterations.",
            },
        },
    },
    "loop_dowhile": {
        "primary": {
            "id": "q_loop_dowhile_1",
            "question": "Why is a `do-while` loop classified as an exit-controlled (post-test) loop?",
            "options": [
                "A) Because the condition is evaluated after the body executes, guaranteeing at least one iteration",
                "B) Because it cannot be broken with a `break` statement",
                "C) Because it only runs on function exit",
                "D) Because it checks the condition twice per iteration",
            ],
            "correct_option": "A",
            "explanation": "The `do { ... } while (condition);` construct executes the body before evaluating the condition.",
            "misconceptions": {
                "B": "`break` works identically in `do-while` loops as in `for` and `while` loops.",
            },
        },
        "remedial": {
            "id": "q_loop_dowhile_rem",
            "question": "What syntax character must terminate the `while (cond)` line of a `do-while` loop in C?",
            "options": [
                "A) Semicolon (`;`)",
                "B) Colon (`:`)",
                "C) Curly brace (`}`) alone",
                "D) Ampersand (`&`)",
            ],
            "correct_option": "A",
            "explanation": "A `do-while` statement must end with a semicolon: `do { ... } while (condition);`.",
            "misconceptions": {
                "C": "Unlike while/for, the trailing while clause of do-while requires an explicit semicolon.",
            },
        },
    },
    "loop_control_statements": {
        "primary": {
            "id": "q_loop_ctrl_1",
            "question": "What is the key difference between `break` and `continue` inside a loop?",
            "options": [
                "A) `break` terminates the entire loop immediately; `continue` skips the rest of the current iteration and starts the next",
                "B) `continue` terminates the program; `break` pauses execution",
                "C) Both keywords behave identically",
                "D) `break` is only valid inside switch statements",
            ],
            "correct_option": "A",
            "explanation": "`break` exits the enclosing loop entirely, whereas `continue` jumps directly to the step/condition of the next cycle.",
            "misconceptions": {
                "D": "`break` is valid in loops (`for`, `while`, `do-while`) as well as `switch` blocks.",
            },
        },
        "remedial": {
            "id": "q_loop_ctrl_rem",
            "question": "In a `for (int i = 0; i < 10; i++)` loop, what does executing `if (i % 2 == 0) continue;` achieve?",
            "options": [
                "A) It skips the remainder of the loop body for even values of i",
                "B) It terminates the loop as soon as i is even",
                "C) It resets i to 0",
                "D) It converts i into an odd number",
            ],
            "correct_option": "A",
            "explanation": "`continue` skips the rest of the body for that iteration, allowing the loop to proceed with odd numbers.",
            "misconceptions": {
                "B": "Termination is done with `break`, not `continue`.",
            },
        },
    },
    "loop_nested": {
        "primary": {
            "id": "q_loop_nested_1",
            "question": "If an outer loop runs $M$ times and an inner loop runs $N$ times per outer iteration, what is total inner body executions?",
            "options": [
                "A) $M \\times N$",
                "B) $M + N$",
                "C) $M^N$",
                "D) $N / M$",
            ],
            "correct_option": "A",
            "explanation": "Nested loops execute multiplicatively. For every 1 step of outer, inner completes $N$ iterations, yielding $M \\times N$ total executions.",
            "misconceptions": {
                "B": "Loops multiply iterations, they do not add them.",
            },
        },
        "remedial": {
            "id": "q_loop_nested_rem",
            "question": "What does executing `break;` inside an inner nested loop do in C?",
            "options": [
                "A) Breaks out of the innermost loop only; the outer loop continues running",
                "B) Breaks out of all nested loops at once",
                "C) Returns from the enclosing function",
                "D) Generates a compiler error",
            ],
            "correct_option": "A",
            "explanation": "In C, `break` only terminates the immediate enclosing loop level.",
            "misconceptions": {
                "B": "To break multiple nested loops at once, use a flag variable or a `goto` statement.",
            },
        },
    },
}


def get_subtopic_question(subtopic_id: str, is_remedial: bool = False) -> Optional[Dict[str, Any]]:
    """Retrieve curated primary or remedial mastery-check question for a subtopic."""
    bank_entry = SUBTOPIC_MASTERY_BANK.get(subtopic_id)
    if not bank_entry:
        return None
    key = "remedial" if is_remedial else "primary"
    return bank_entry.get(key)
