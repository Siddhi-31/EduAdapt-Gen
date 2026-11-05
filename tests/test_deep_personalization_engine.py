"""Comprehensive Test Suite for EduAdapt's Deep, Mastery-Based Personalization Engine.

Validates the full pedagogical business logic and non-agentic feedback loops:
- Test Case A: Weak learner foundation-first teaching & adaptive cycles (up to 5 cycles, early exit, honest status)
- Test Case B: Intermediate learner concept expansion & moderate challenge (up to 4 cycles)
- Test Case C: Advanced learner challenge-driven teaching & edge-case depth (up to 3 cycles)
- Test Case D: Same topic, different students (visibly differentiated teaching across tiers)
- Test Case E: Same student, different subtopics (independent subtopic mastery; declaration vs arithmetic)
- Test Case F: Persistence and navigation across topics (isolated history, subtopic progression survival)
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.curriculum.mastery_policy import (
    MASTERY_THRESHOLD_BEGINNER_MAX,
    MASTERY_THRESHOLD_DEVELOPING_MAX,
    MASTERY_THRESHOLD_INTERMEDIATE_MAX,
    MASTERY_THRESHOLD_MASTERED,
    evaluate_mastery_tier,
    evaluate_detailed_diagnostic_level,
    get_max_cycles_for_tier,
    is_subtopic_mastered,
)
from eduadapt.curriculum.pps_curriculum import (
    PPS_CURRICULUM_TREE,
    get_subtopics_for_topic,
    get_subtopic_by_id,
    normalize_topic_key,
    get_curriculum_tree_summary,
)
from eduadapt.teaching.personalization import (
    PersonalizationEngine,
    PersonalizationContext,
    InstructionalStrategy,
)
from eduadapt.teaching.generator import PersonalizedContentGenerator
from eduadapt.services.adaptive_learning import AdaptiveLearningService
from eduadapt.services.subtopic_progress_service import SubtopicProgressService
from eduadapt.services.tutor_history_service import TutorHistoryService
from eduadapt.prompts.templates import PromptManager
from eduadapt.inference.base import BaseLLMClient, GenerationResult


class RecordingLLMClient(BaseLLMClient):
    """LLM client that captures generated prompts and returns structured markdown lessons."""

    def __init__(self, model_name: str = "mistral:7b"):
        self.model_name = model_name
        self.captured_prompts = []

    def generate(self, prompt: str, **kwargs) -> GenerationResult:
        self.captured_prompts.append(prompt)

        # Synthesize realistic structured educational markdown matching prompt directives
        is_beginner = "Tier: Beginner" in prompt or "Weak Learner" in prompt
        is_intermediate = "Tier: Intermediate" in prompt or "Intermediate Learner" in prompt
        is_advanced = "Tier: Advanced" in prompt or "Advanced Learner" in prompt

        if is_beginner:
            content = (
                "### Learning Objective\n"
                "Understand what a memory address is and declare a simple pointer in C.\n\n"
                "### Conceptual Explanation\n"
                "Think of computer memory (RAM) as a row of numbered lockers. Each locker has an address. "
                "A variable stores a value inside the locker. A pointer is a variable that stores the locker address.\n"
                "The & operator finds the address. The * operator reads the value.\n\n"
                "### Visual Architecture Diagram\n"
                "```mermaid\n"
                "flowchart LR\n"
                '    Var["Variable: x = 10 (Addr: 0x1000)"]\n'
                '    Ptr["Pointer: ptr = 0x1000"] -->|dereference *| Var\n'
                "```\n\n"
                "### C Code Implementation\n"
                "```c\n"
                "#include <stdio.h>\n"
                "int main(void) {\n"
                "    int x = 10;\n"
                "    int *ptr = &x;\n"
                '    printf("Value: %d\\n", *ptr);\n'
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "### Step-by-Step Code Walkthrough\n"
                "1. int x = 10 allocates 4 bytes of memory storing value 10.\n"
                "2. int *ptr = &x stores the address of x into pointer ptr.\n"
                "3. *ptr dereferences the address to print 10.\n\n"
                "### Common Mistakes to Avoid\n"
                "- Confusing & (gets address) with * (gets value).\n"
                "- Forgetting to initialize a pointer before using it.\n\n"
                "### Quick Understanding Check\n"
                "What does &num return in C?\n"
                "A) The value of num\n"
                "B) The memory address of num\n"
                "C) The byte size of num\n"
                "D) A compile error\n"
            )
        elif is_intermediate:
            content = (
                "### Learning Objective\n"
                "Master pointer arithmetic, array indexing, and parameter mutation in C functions.\n\n"
                "### Conceptual Explanation\n"
                "Pointers and arrays share deep equivalence in C: array names evaluate to the base address. "
                "Pointer arithmetic increments by sizeof(type) bytes per step. Passing pointers allows functions to mutate caller memory.\n\n"
                "### Visual Architecture Diagram\n"
                "```mermaid\n"
                "flowchart TD\n"
                '    Arr["arr[0] at 0x2000"] -->|"+1 (+4 bytes)"| Arr1["arr[1] at 0x2004"]\n'
                "```\n\n"
                "### C Code Implementation\n"
                "```c\n"
                "#include <stdio.h>\n"
                "void swap(int *a, int *b) {\n"
                "    int t = *a; *a = *b; *b = t;\n"
                "}\n"
                "int main(void) {\n"
                "    int arr[3] = {10, 20, 30};\n"
                "    int *p = arr;\n"
                "    swap(p, p + 2);\n"
                '    printf("%d %d\\n", arr[0], arr[2]);\n'
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "### Step-by-Step Code Walkthrough\n"
                "1. Array decays to base pointer p = &arr[0].\n"
                "2. swap receives pointers to first and third elements.\n"
                "3. In-place memory mutation swaps 10 and 30.\n\n"
                "### Common Mistakes to Avoid\n"
                "- Navigating beyond array bounds with pointer increments.\n"
                "- Missing type scaling when performing address arithmetic.\n\n"
                "### Quick Understanding Check\n"
                "What does *(arr + 2) evaluate to?\n"
                "A) arr[0] + 2\n"
                "B) arr[2]\n"
                "C) &arr[2]\n"
                "D) Address offset\n"
            )
        else:  # Advanced
            content = (
                "### Learning Objective\n"
                "Analyze double indirection, pointer-to-pointer mechanics, and dynamic memory safety.\n\n"
                "### Conceptual Explanation\n"
                "Double pointers (**ptr) store the memory addresses of other pointer variables. This indirection "
                "enables dynamic multi-dimensional memory layout, caller pointer mutation across stack frames, and robust data structures.\n\n"
                "### Visual Architecture Diagram\n"
                "```mermaid\n"
                "flowchart LR\n"
                '    Dbl["pp (0x3000)"] -->|indirection| Single["p (0x2000)"] -->|indirection| Val["target = 99 (0x1000)"]\n'
                "```\n\n"
                "### C Code Implementation\n"
                "```c\n"
                "#include <stdio.h>\n"
                "#include <stdlib.h>\n"
                "void allocate_block(int **ptr, size_t n) {\n"
                "    *ptr = (int *)malloc(n * sizeof(int));\n"
                "}\n"
                "int main(void) {\n"
                "    int *buffer = NULL;\n"
                "    allocate_block(&buffer, 5);\n"
                "    if (!buffer) return 1;\n"
                "    buffer[0] = 99;\n"
                '    printf("Allocated: %d\\n", buffer[0]);\n'
                "    free(buffer); buffer = NULL;\n"
                "    return 0;\n"
                "}\n"
                "```\n\n"
                "### Step-by-Step Code Walkthrough\n"
                "1. buffer pointer is initialized to NULL to prevent wild pointer bugs.\n"
                "2. Address &buffer is passed into allocate_block as int **ptr.\n"
                "3. malloc heap allocation is assigned to *ptr, mutating caller buffer address.\n"
                "4. Memory is safely freed and pointer reset to NULL.\n\n"
                "### Common Mistakes to Avoid\n"
                "- Modifying a local pointer copy without double indirection.\n"
                "- Failing to verify heap allocation against NULL before dereferencing.\n"
                "- Dangling pointer access after free.\n\n"
                "### Quick Understanding Check\n"
                "Why is int **ptr required to allocate memory in a helper function?\n"
                "A) Because C is object-oriented\n"
                "B) To modify the caller's pointer variable via its address\n"
                "C) Pointers cannot be passed to functions\n"
                "D) Standard C forbids malloc in main\n"
            )

        return GenerationResult(
            content=content,
            model_name=self.model_name,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(content.split()),
            metadata={"captured": True},
        )


# ==============================================================================
# TEST CASE A: WEAK LEARNER — FOUNDATION-FIRST & ADAPTIVE CYCLES
# ==============================================================================
def test_case_a_weak_learner_foundational_cycles(tmp_path):
    """Test Case A: Weak learner receives foundation-first content, guided practice,
    and adaptive cycles (up to 5) with early exit when mastery is achieved.
    """
    progress_file = tmp_path / "subtopic_progress.json"
    service = SubtopicProgressService(data_file=progress_file)

    student_id = "S005_WEAK"
    topic = "Pointers"

    # Step 1: Diagnose weak learner (mastery 0.25)
    progress = service.initialize_topic_for_student(
        student_id=student_id,
        topic=topic,
        overall_mastery=0.25,
        learning_pace="slow",
    )
    assert progress["mastery_tier"] == "Beginner"
    assert progress["overall_mastery"] == 0.25

    # Check first subtopic: Introduction to Memory Addresses
    subtopics = list(progress["subtopics"].values())
    first_sub = subtopics[0]
    assert first_sub["status"] == "In Progress"
    assert first_sub["learning_cycle"] == 1
    assert first_sub["max_cycles"] == 5

    # Step 2: Generate lesson for Cycle 1
    llm = RecordingLLMClient()
    generator = PersonalizedContentGenerator(llm_client=llm)
    profile = StudentProfile(
        student_id=student_id,
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.25},
        preferred_pace="slow",
        common_misconceptions=["Confusing address & with value *"],
    )

    lesson_c1 = generator.generate_for_student(
        topic="Pointers",
        student_profile=profile,
        subtopic=first_sub["title"],
        learning_cycle=1,
        subtopic_state=first_sub,
    )

    prompt = llm.captured_prompts[0]
    assert "Tier: Beginner" in prompt
    assert "Teach this subtopic from the foundations" in prompt
    assert "Cycle 1 of 5" in prompt
    assert "Confusing address & with value *" in prompt

    # Verify beginner lesson structure
    assert "### Learning Objective" in lesson_c1.content
    assert "locker" in lesson_c1.content.lower() or "address" in lesson_c1.content.lower()

    # Step 3: Student fails Cycle 1 check (score 35%) -> advances to Cycle 2
    attempt_1 = service.record_cycle_attempt(
        student_id=student_id,
        topic="Pointers",
        subtopic_id=first_sub["id"],
        score=35.0,
        is_correct=False,
        accuracy=0.35,
        weak_concepts=["dereference operator"],
    )
    assert attempt_1["mastery_achieved"] is False
    assert attempt_1["current_cycle"] == 2
    assert "dereference" in attempt_1["remediation_focus"].lower()

    # Step 4: Early Exit check — Student achieves 85% in Cycle 2 -> exits early!
    attempt_2 = service.record_cycle_attempt(
        student_id=student_id,
        topic="Pointers",
        subtopic_id=first_sub["id"],
        score=85.0,
        is_correct=True,
        accuracy=0.85,
    )
    assert attempt_2["mastery_achieved"] is True
    assert attempt_2["status"] == "Mastered"
    assert attempt_2["progression_status"] == "mastered_early_exit"
    # Unlocked next subtopic!
    assert attempt_2["unlocked_subtopic_id"] is not None


def test_case_a_weak_learner_honest_status_after_max_cycles(tmp_path):
    """Verify that a struggling student who fails through Cycle 5 is not falsely marked complete."""
    progress_file = tmp_path / "subtopic_progress.json"
    service = SubtopicProgressService(data_file=progress_file)

    student_id = "S006_STRUGGLING"
    topic = "Pointers"
    service.initialize_topic_for_student(student_id, topic, overall_mastery=0.15, learning_pace="slow")

    sub_id = "ptr_intro_addresses"
    for cycle in range(1, 6):
        res = service.record_cycle_attempt(
            student_id=student_id,
            topic=topic,
            subtopic_id=sub_id,
            score=30.0,
            is_correct=False,
            accuracy=0.30,
            weak_concepts=["memory address"],
        )

    # After 5 cycles with low scores, topic must NOT be marked complete
    assert res["mastery_achieved"] is False
    assert res["status"] == "In Progress"
    assert res["progression_status"] == "max_cycles_reached"
    assert "Maximum teaching cycles" in res["remediation_focus"]
    assert "Targeted remediation recommended" in res["remediation_focus"]


# ==============================================================================
# TEST CASE B: INTERMEDIATE LEARNER — PRACTICAL APPLICATION & EXPANSION
# ==============================================================================
def test_case_b_intermediate_learner_concept_expansion(tmp_path):
    """Test Case B: Intermediate learner skips elementary definitions, receives
    moderate-complexity C code and practical output-tracing challenges.
    """
    llm = RecordingLLMClient()
    generator = PersonalizedContentGenerator(llm_client=llm)

    profile = StudentProfile(
        student_id="S003",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.60},
        preferred_pace="moderate",
        common_misconceptions=[],
    )

    lesson = generator.generate_for_student(
        topic="Pointers",
        student_profile=profile,
        subtopic="Pointer Arithmetic and Type Scaling",
        learning_cycle=1,
    )

    prompt = llm.captured_prompts[0]
    assert "Tier: Intermediate" in prompt
    assert "Assume the learner has satisfactory foundational knowledge" in prompt
    assert "Teach the deeper mechanics, practical applications" in prompt

    # Verify intermediate content
    assert "swap" in lesson.content.lower() or "arithmetic" in lesson.content.lower()
    assert lesson.metadata["mastery_tier"] == "Intermediate"
    assert lesson.metadata["max_cycles"] == 4


# ==============================================================================
# TEST CASE C: ADVANCED LEARNER — CHALLENGE-DRIVEN & IN-DEPTH SEMANTICS
# ==============================================================================
def test_case_c_advanced_learner_edge_case_depth(tmp_path):
    """Test Case C: Advanced learner receives concise prerequisite recaps,
    challenging applications, edge cases, and achieves mastery in fewer cycles (up to 3).
    """
    llm = RecordingLLMClient()
    generator = PersonalizedContentGenerator(llm_client=llm)

    profile = StudentProfile(
        student_id="S001",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.95},
        preferred_pace="fast",
        common_misconceptions=[],
    )

    lesson = generator.generate_for_student(
        topic="Pointers",
        student_profile=profile,
        subtopic="Pointer to Pointer (Double Indirection)",
        learning_cycle=1,
    )

    prompt = llm.captured_prompts[0]
    assert "Tier: Advanced" in prompt
    assert "Assume the learner has strong foundational mastery" in prompt
    assert "Focus on advanced applications, complex code reasoning, difficult edge cases" in prompt

    # Verify advanced metadata and content
    assert lesson.metadata["mastery_tier"] == "Advanced"
    assert lesson.metadata["max_cycles"] == 3
    assert "malloc" in lesson.content or "double" in lesson.content.lower()


# ==============================================================================
# TEST CASE D: SAME TOPIC, THREE DIFFERENT STUDENTS
# ==============================================================================
def test_case_d_same_topic_different_students(tmp_path):
    """Test Case D: Critical personalization test.
    Select Pointers for three students (Weak: S005, Intermediate: S003, Advanced: S001).
    Verify that generated prompts, metadata, and instructional strategies are visibly distinct!
    """
    llm = RecordingLLMClient()
    generator = PersonalizedContentGenerator(llm_client=llm)

    # 1. Weak student (S005)
    s_weak = StudentProfile(
        student_id="S005",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.25},
        preferred_pace="slow",
    )
    res_weak = generator.generate_for_student(topic="Pointers", student_profile=s_weak)

    # 2. Intermediate student (S003)
    s_med = StudentProfile(
        student_id="S003",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.60},
        preferred_pace="moderate",
    )
    res_med = generator.generate_for_student(topic="Pointers", student_profile=s_med)

    # 3. Advanced student (S001)
    s_adv = StudentProfile(
        student_id="S001",
        current_topic="Pointers",
        mastery_levels={"Pointers": 0.90},
        preferred_pace="fast",
    )
    res_adv = generator.generate_for_student(topic="Pointers", student_profile=s_adv)

    # Compare Prompts
    prompt_weak = llm.captured_prompts[0]
    prompt_med = llm.captured_prompts[1]
    prompt_adv = llm.captured_prompts[2]

    # Verify Prompts are distinct
    assert prompt_weak != prompt_med
    assert prompt_med != prompt_adv
    assert "Tier: Beginner" in prompt_weak
    assert "Tier: Intermediate" in prompt_med
    assert "Tier: Advanced" in prompt_adv

    # Compare Metadata
    meta_weak = res_weak.metadata
    meta_med = res_med.metadata
    meta_adv = res_adv.metadata

    assert meta_weak["mastery_tier"] == "Beginner"
    assert meta_med["mastery_tier"] == "Intermediate"
    assert meta_adv["mastery_tier"] == "Advanced"

    assert meta_weak["max_cycles"] == 5
    assert meta_med["max_cycles"] == 4
    assert meta_adv["max_cycles"] == 3

    assert meta_weak["explanation_depth"] != meta_adv["explanation_depth"]
    assert meta_weak["code_complexity"] != meta_adv["code_complexity"]
    assert meta_weak["scaffolding_level"] != meta_adv["scaffolding_level"]


# ==============================================================================
# TEST CASE E: SAME STUDENT, DIFFERENT SUBTOPICS
# ==============================================================================
def test_case_e_same_student_different_subtopics(tmp_path):
    """Test Case E: Verify that a student with high overall pointer knowledge (0.85)
    who is weak in pointer arithmetic (0.20) receives:
    - Advanced teaching on Pointer Declaration
    - Foundational/remedial teaching on Pointer Arithmetic
    - Subtopic mastery is maintained independently!
    """
    llm = RecordingLLMClient()
    generator = PersonalizedContentGenerator(llm_client=llm)

    # Student S001 has overall 0.85 mastery in pointers, but subtopic states vary
    profile = StudentProfile(
        student_id="S001",
        current_topic="Pointers",
        mastery_levels={
            "Pointers": 0.85,
            "Pointer Declaration and Initialization": 0.90,
            "Pointer Arithmetic and Type Scaling": 0.20,
        },
        preferred_pace="moderate",
    )

    # Subtopic 1: Pointer Declaration (Strong: 0.90)
    ctx_decl = PersonalizationEngine.derive_context(
        student_profile=profile,
        topic="Pointers",
        subtopic="Pointer Declaration and Initialization",
    )
    assert ctx_decl.subtopic_mastery == 0.90
    assert ctx_decl.mastery_tier == "Advanced"
    assert ctx_decl.max_cycles == 3

    res_decl = generator.generate_for_student(
        topic="Pointers",
        student_profile=profile,
        subtopic="Pointer Declaration and Initialization",
    )
    assert res_decl.metadata["mastery_tier"] == "Advanced"

    # Subtopic 2: Pointer Arithmetic (Weak gap: 0.20)
    ctx_arith = PersonalizationEngine.derive_context(
        student_profile=profile,
        topic="Pointers",
        subtopic="Pointer Arithmetic and Type Scaling",
    )
    assert ctx_arith.subtopic_mastery == 0.20
    assert ctx_arith.mastery_tier == "Beginner"
    assert "gap" in ctx_arith.pattern_name.lower() or "strong overall foundation" in ctx_arith.pattern_name.lower()
    assert ctx_arith.max_cycles == 5

    res_arith = generator.generate_for_student(
        topic="Pointers",
        student_profile=profile,
        subtopic="Pointer Arithmetic and Type Scaling",
    )
    assert res_arith.metadata["mastery_tier"] == "Beginner"

    # Ensure overall pointer mastery (0.85) did not hide the arithmetic weakness (0.20)
    assert ctx_decl.strategy.code_complexity != ctx_arith.strategy.code_complexity
    assert ctx_decl.strategy.scaffolding_level != ctx_arith.strategy.scaffolding_level


# ==============================================================================
# TEST CASE F: PERSISTENCE & TOPIC ISOLATION
# ==============================================================================
def test_case_f_navigation_and_persistence(tmp_path):
    """Test Case F: Verify persistence of subtopic progression and AI tutor history:
    1. Multi-turn AI tutor conversation for Pointers.
    2. Switch to Strings -> confirm isolated topic history.
    3. Return to Pointers -> confirm Pointers history is intact.
    4. Subtopic mastery and completed nodes survive.
    """
    tutor_file = tmp_path / "tutor_history.json"
    tutor_svc = TutorHistoryService(history_file=tutor_file)

    subtopic_file = tmp_path / "subtopic_progress.json"
    sub_svc = SubtopicProgressService(data_file=subtopic_file)

    student_id = "S001_PERSIST"

    # 1. Chat under Pointers
    tutor_svc.append_message(student_id, "Pointers", "student", "What is *ptr?")
    tutor_svc.append_message(student_id, "Pointers", "assistant", "*ptr accesses the dereferenced value.")
    hist_ptr = tutor_svc.get_history(student_id, "Pointers")
    assert len(hist_ptr) == 2

    # 2. Switch to Strings
    tutor_svc.append_message(student_id, "Strings", "student", "Why do strings end with \\0?")
    hist_str = tutor_svc.get_history(student_id, "Strings")
    assert len(hist_str) == 1
    assert hist_str[0]["text"] == "Why do strings end with \\0?"

    # 3. Return to Pointers -> history preserved without contamination!
    hist_ptr_again = tutor_svc.get_history(student_id, "Pointers")
    assert len(hist_ptr_again) == 2
    assert hist_ptr_again[0]["text"] == "What is *ptr?"

    # 4. Record subtopic progress under Pointers
    sub_svc.record_cycle_attempt(
        student_id=student_id,
        topic="Pointers",
        subtopic_id="ptr_intro_addresses",
        score=90.0,
        is_correct=True,
        accuracy=0.9,
    )
    roadmap_ptr = sub_svc.get_student_subtopic_roadmap(student_id, "Pointers")
    assert roadmap_ptr["completed_count"] >= 1

    # 5. Switch to Loops and record progress
    sub_svc.record_cycle_attempt(
        student_id=student_id,
        topic="Loops",
        subtopic_id="loop_while",
        score=50.0,
        is_correct=False,
        accuracy=0.5,
    )
    roadmap_loops = sub_svc.get_student_subtopic_roadmap(student_id, "Loops")
    assert roadmap_loops["completed_count"] == 0

    # 6. Verify Pointers progress was not altered by Loops activity
    roadmap_ptr_verified = sub_svc.get_student_subtopic_roadmap(student_id, "Pointers")
    assert roadmap_ptr_verified["completed_count"] >= 1
