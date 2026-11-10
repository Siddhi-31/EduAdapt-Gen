"""Idempotent database seeding service for EduAdapt.

Seeds:
1. Standard PPS Curriculum Topics & Subtopics
2. Predefined Diagnostic Question Bank (105 questions including mandatory Q1-Q25)
"""

from decimal import Decimal
import logging
from typing import Dict, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from eduadapt.db.models.curriculum import CurriculumSubtopic, CurriculumTopic
from eduadapt.db.models.question import Question
from eduadapt.services.diagnostic_bank import DIAGNOSTIC_QUESTIONS

logger = logging.getLogger("eduadapt.services.seed_service")

PPS_CURRICULUM = [
    {
        "name": "Variables and Data Types",
        "slug": "variables-and-data-types",
        "description": "Foundational C primitives, variable declarations, memory representations, and format specifiers.",
        "display_order": 1,
        "subtopics": [
            ("Variables & Memory Representation", "variables-memory", "Declaration, initialization, and stack memory layout.", 1),
            ("Basic Data Types", "basic-data-types", "int, char, float, double and their ranges.", 2),
            ("Format Specifiers & I/O", "format-specifiers-io", "Standard input/output with scanf and printf.", 3),
        ],
    },
    {
        "name": "Operators and Expressions",
        "slug": "operators-and-expressions",
        "description": "Arithmetic, relational, logical, bitwise, and ternary operators with operator precedence.",
        "display_order": 2,
        "subtopics": [
            ("Arithmetic Operators", "arithmetic-operators", "Basic arithmetic, modulus, and compound assignments.", 1),
            ("Relational & Logical Operators", "relational-logical", "Comparison operators, boolean logic, and short-circuiting.", 2),
            ("Operator Precedence", "operator-precedence", "Order of evaluation and associativity in C.", 3),
        ],
    },
    {
        "name": "Conditionals",
        "slug": "conditionals",
        "description": "Branching and flow-of-control constructs in C.",
        "display_order": 3,
        "subtopics": [
            ("If-Else Branching", "if-else", "Simple, nested, and chained if-else decision trees.", 1),
            ("Switch-Case", "switch-case", "Multi-way branching and jump table constructs.", 2),
        ],
    },
    {
        "name": "Loops",
        "slug": "loops",
        "description": "Iterative constructs, counter-controlled loops, condition-controlled loops, and loop control statements.",
        "display_order": 4,
        "subtopics": [
            ("While Loops", "while-loops", "Pre-test condition iteration.", 1),
            ("For Loops", "for-loops", "Index-based iteration and multi-counter loops.", 2),
            ("Do-While & Loop Control", "do-while-control", "Post-test loops, break, and continue.", 3),
            ("Nested Loops", "nested-loops", "Multi-dimensional iteration and pattern generation.", 4),
        ],
    },
    {
        "name": "Arrays",
        "slug": "arrays",
        "description": "Contiguous memory allocations and linear data collections.",
        "display_order": 5,
        "subtopics": [
            ("1D Arrays", "1d-arrays", "Array declaration, indexing, boundary safety, and traversal.", 1),
            ("2D Arrays & Matrices", "2d-arrays", "Row-major layout and matrix operations.", 2),
            ("Array Algorithms", "array-algorithms", "Searching and sorting in contiguous buffers.", 3),
        ],
    },
    {
        "name": "Strings",
        "slug": "strings",
        "description": "Null-terminated character arrays, pointer traversal, and string library functions.",
        "display_order": 6,
        "subtopics": [
            ("Character Arrays & Null Terminator", "char-arrays-null", "String representation and null byte semantics.", 1),
            ("String Manipulation Functions", "string-manipulation", "strlen, strcpy, strcmp, strcat implementations.", 2),
        ],
    },
    {
        "name": "Functions",
        "slug": "functions",
        "description": "Modular programming, activation records, parameter passing, and recursion.",
        "display_order": 7,
        "subtopics": [
            ("Function Definition & Prototypes", "function-prototypes", "Declaration, call stack, and return values.", 1),
            ("Call by Value vs Reference", "call-by-value-reference", "Value copies versus memory references.", 2),
            ("Recursion", "recursion", "Base cases, call stack unwinding, and recurrence relations.", 3),
        ],
    },
    {
        "name": "Pointers",
        "slug": "pointers",
        "description": "Direct memory addressing, indirection, pointer arithmetic, and pointers with functions.",
        "display_order": 8,
        "subtopics": [
            ("Pointer Basics & Dereferencing", "pointer-basics", "Address-of (&) and dereferencing (*) operators.", 1),
            ("Pointer Arithmetic", "pointer-arithmetic", "Scaling with data type size and array indexing.", 2),
            ("Pointers and Functions", "pointers-functions", "Passing addresses and return by reference.", 3),
            ("Pointers to Pointers", "double-pointers", "Multiple indirection and dynamic buffer manipulation.", 4),
        ],
    },
    {
        "name": "Structures",
        "slug": "structures",
        "description": "User-defined composite types, memory alignment, and arrays of structures.",
        "display_order": 9,
        "subtopics": [
            ("Structure Definition & Member Access", "structure-definition", "struct declaration, member access via dot operator.", 1),
            ("Arrays of Structures & Arrow Operator", "arrays-structures-arrow", "Pointers to structs and arrow (->) operator.", 2),
        ],
    },
    {
        "name": "Dynamic Memory Allocation",
        "slug": "dynamic-memory-allocation",
        "description": "Heap memory management with malloc, calloc, realloc, and free.",
        "display_order": 10,
        "subtopics": [
            ("Malloc, Free & Memory Leaks", "malloc-free-leaks", "Allocating and releasing heap memory.", 1),
            ("Calloc & Realloc", "calloc-realloc", "Zeroed allocations and dynamic resizing.", 2),
        ],
    },
]


async def seed_database_async(session: AsyncSession) -> Dict[str, int]:
    """Idempotently seed curriculum topics, subtopics, and diagnostic questions."""
    topics_seeded = 0
    subtopics_seeded = 0
    questions_seeded = 0

    # 1. Seed PPS Curriculum Topics & Subtopics
    for topic_data in PPS_CURRICULUM:
        stmt = select(CurriculumTopic).where(CurriculumTopic.slug == topic_data["slug"])
        res = await session.execute(stmt)
        topic = res.scalar_one_or_none()
        if not topic:
            topic = CurriculumTopic(
                name=topic_data["name"],
                slug=topic_data["slug"],
                description=topic_data["description"],
                display_order=topic_data["display_order"],
                is_active=True,
            )
            session.add(topic)
            await session.flush()
            topics_seeded += 1

        for sub_name, sub_slug, sub_desc, sub_order in topic_data["subtopics"]:
            stmt_sub = select(CurriculumSubtopic).where(
                CurriculumSubtopic.topic_id == topic.id,
                CurriculumSubtopic.slug == sub_slug,
            )
            res_sub = await session.execute(stmt_sub)
            subtopic = res_sub.scalar_one_or_none()
            if not subtopic:
                subtopic = CurriculumSubtopic(
                    topic_id=topic.id,
                    name=sub_name,
                    slug=sub_slug,
                    description=sub_desc,
                    display_order=sub_order,
                    is_active=True,
                )
                session.add(subtopic)
                await session.flush()
                subtopics_seeded += 1

    # 2. Seed Predefined Diagnostic Question Bank
    for q in DIAGNOSTIC_QUESTIONS:
        # Match by question text prefix to ensure idempotency
        stmt_q = select(Question).where(Question.question_text == q["question_text"])
        res_q = await session.execute(stmt_q)
        existing = res_q.scalar_one_or_none()
        if not existing:
            new_q = Question(
                subtopic_id=None,
                category=q["category"],
                question_text=q["question_text"],
                question_type="MCQ",
                difficulty_level=q["difficulty_level"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                marks=Decimal("1.00"),
                is_active=True,
            )
            session.add(new_q)
            questions_seeded += 1

    await session.commit()
    logger.info(
        "Database seed complete: %d topics, %d subtopics, %d questions seeded.",
        topics_seeded,
        subtopics_seeded,
        questions_seeded,
    )
    return {
        "topics_seeded": topics_seeded,
        "subtopics_seeded": subtopics_seeded,
        "questions_seeded": questions_seeded,
    }


def seed_database_sync(session: Session) -> Dict[str, int]:
    """Synchronous version for CLI script execution."""
    topics_seeded = 0
    subtopics_seeded = 0
    questions_seeded = 0

    for topic_data in PPS_CURRICULUM:
        topic = session.query(CurriculumTopic).filter_by(slug=topic_data["slug"]).first()
        if not topic:
            topic = CurriculumTopic(
                name=topic_data["name"],
                slug=topic_data["slug"],
                description=topic_data["description"],
                display_order=topic_data["display_order"],
                is_active=True,
            )
            session.add(topic)
            session.flush()
            topics_seeded += 1

        for sub_name, sub_slug, sub_desc, sub_order in topic_data["subtopics"]:
            subtopic = session.query(CurriculumSubtopic).filter_by(
                topic_id=topic.id,
                slug=sub_slug,
            ).first()
            if not subtopic:
                subtopic = CurriculumSubtopic(
                    topic_id=topic.id,
                    name=sub_name,
                    slug=sub_slug,
                    description=sub_desc,
                    display_order=sub_order,
                    is_active=True,
                )
                session.add(subtopic)
                session.flush()
                subtopics_seeded += 1

    for q in DIAGNOSTIC_QUESTIONS:
        existing = session.query(Question).filter_by(question_text=q["question_text"]).first()
        if not existing:
            new_q = Question(
                subtopic_id=None,
                category=q["category"],
                question_text=q["question_text"],
                question_type="MCQ",
                difficulty_level=q["difficulty_level"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"],
                marks=Decimal("1.00"),
                is_active=True,
            )
            session.add(new_q)
            questions_seeded += 1

    session.commit()
    return {
        "topics_seeded": topics_seeded,
        "subtopics_seeded": subtopics_seeded,
        "questions_seeded": questions_seeded,
    }
