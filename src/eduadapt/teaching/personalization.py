"""Centralized Personalization Engine for EduAdapt.

Provides deterministic, student-adaptive instructional strategies derived from
REAL StudentProfile and Learning Twin states. Strictly non-agentic.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
from eduadapt.interfaces.student_model import StudentProfile
from eduadapt.curriculum.mastery_policy import (
    MASTERY_THRESHOLD_BEGINNER_MAX,
    MASTERY_THRESHOLD_DEVELOPING_MAX,
    MASTERY_THRESHOLD_INTERMEDIATE_MAX,
    MASTERY_THRESHOLD_ADVANCED_MAX,
    MASTERY_THRESHOLD_MASTERED,
    evaluate_mastery_tier,
    evaluate_detailed_diagnostic_level,
    get_max_cycles_for_tier,
)
from eduadapt.curriculum.pps_curriculum import (
    get_subtopics_for_topic,
    get_subtopic_by_id,
    normalize_topic_key,
)


@dataclass
class InstructionalStrategy:
    """Explicit pedagogical dimensions for personalized teaching."""

    explanation_depth: str
    teaching_approach: str
    cognitive_difficulty: str
    code_complexity: str
    example_selection: str
    step_granularity: str
    scaffolding_level: str
    practice_complexity: str
    diagram_type: str
    diagram_recommendation: str
    feedback_style: str
    misconception_strategy: str
    roadmap_sequencing: str
    response_structure: str
    amount_of_explanation: str
    revision_strategy: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "explanation_depth": self.explanation_depth,
            "teaching_approach": self.teaching_approach,
            "cognitive_difficulty": self.cognitive_difficulty,
            "code_complexity": self.code_complexity,
            "example_selection": self.example_selection,
            "step_granularity": self.step_granularity,
            "scaffolding_level": self.scaffolding_level,
            "practice_complexity": self.practice_complexity,
            "diagram_type": self.diagram_type,
            "diagram_recommendation": self.diagram_recommendation,
            "feedback_style": self.feedback_style,
            "misconception_strategy": self.misconception_strategy,
            "roadmap_sequencing": self.roadmap_sequencing,
            "response_structure": self.response_structure,
            "amount_of_explanation": self.amount_of_explanation,
            "revision_strategy": self.revision_strategy,
        }


@dataclass
class PersonalizationContext:
    """Normalized context and pedagogical strategy for prompt generation."""

    student_id: str
    target_topic: str
    topic_mastery: float
    overall_mastery: float
    mastery_tier: str  # "Beginner", "Intermediate", "Advanced"
    learning_pace: str  # "slow", "moderate", "fast"
    preferred_learning_style: str
    recommended_difficulty: str
    predicted_mastery_level: str
    subtopic: Optional[str] = None
    subtopic_id: Optional[str] = None
    subtopic_mastery: Optional[float] = None
    learning_cycle: int = 1
    max_cycles: int = 5
    remediation_focus: Optional[str] = None
    previous_errors: List[str] = field(default_factory=list)
    completed_subtopics: List[str] = field(default_factory=list)
    pending_subtopics: List[str] = field(default_factory=list)
    prerequisite_mastery: Optional[float] = None
    target_mastery_threshold: float = MASTERY_THRESHOLD_MASTERED
    common_misconceptions: List[str] = field(default_factory=list)
    accuracy: Optional[float] = None
    attempt_count: Optional[float] = None
    average_time_seconds: Optional[float] = None
    pattern_name: str = "General Adaptive"
    strategy: Optional[InstructionalStrategy] = None
    personalization_summary: Dict[str, str] = field(default_factory=dict)

    def get_personalization_applied_bullets(self) -> List[str]:
        """Human-readable bullet points explaining what personalization was applied."""
        if not self.strategy:
            return ["Strategy: General PPS curriculum progression"]

        effective_sub = self.subtopic or self.target_topic
        eff_mastery = self.subtopic_mastery if self.subtopic_mastery is not None else self.topic_mastery

        bullets = [
            f"Topic: {self.target_topic} • Subtopic: {effective_sub}",
            f"Subtopic Mastery: {eff_mastery:.2f} ({self.mastery_tier} Tier - {evaluate_detailed_diagnostic_level(eff_mastery)})",
            f"Teaching Cycle: Cycle {self.learning_cycle} of {self.max_cycles} ({'Targeted Remediation' if self.learning_cycle > 1 else 'Initial Instruction'})",
            f"Learning Pace: {self.learning_pace.capitalize()} pace instruction",
            f"Teaching Approach: {self.strategy.teaching_approach}",
            f"Explanation Depth: {self.strategy.explanation_depth}",
            f"Code Complexity: {self.strategy.code_complexity}",
            f"Scaffolding Level: {self.strategy.scaffolding_level}",
            f"Concept Focus: {self.personalization_summary.get('concept_focus', 'Core curriculum mechanics and invariants')}",
            f"Pedagogical Rationale: {self.personalization_summary.get('rationale', '')}",
        ]
        if self.remediation_focus:
            bullets.append(f"Remediation Target: {self.remediation_focus}")
        return bullets


def select_diagram_type_for_topic(topic: str, mastery_tier: str) -> str:
    """Deterministically select appropriate PPS educational diagram based on topic."""
    norm = topic.strip().lower()
    if "pointer" in norm:
        return "pointer_memory_diagram"
    elif "loop" in norm or "while" in norm or "for" in norm:
        return "loop_execution_flowchart"
    elif "cond" in norm or "if" in norm or "switch" in norm:
        return "conditional_decision_diagram"
    elif "array" in norm:
        return "array_index_memory_diagram"
    elif "function" in norm or "recursion" in norm:
        return "function_call_stack_diagram"
    elif "string" in norm:
        return "string_null_terminator_diagram"
    elif "struct" in norm or "union" in norm:
        return "struct_memory_layout_diagram"
    elif "operator" in norm or "expression" in norm:
        return "expression_evaluation_tree"
    elif "variable" in norm or "data type" in norm:
        return "variable_storage_diagram"
    else:
        return "concept_flowchart"


def build_diagram_directive(diagram_type: str, topic: str, mastery_tier: str) -> str:
    """Produce precise Mermaid generation instructions for the LLM."""
    if diagram_type == "pointer_memory_diagram":
        return (
            "Generate a Mermaid diagram (flowchart LR or TD) illustrating memory layout for pointers. "
            "Show memory addresses (e.g. 0x1000, 0x2000), variable names, stored values, and arrows "
            "indicating pointer dereferencing (*ptr -> value). Use simple node IDs with alphanumeric characters."
        )
    elif diagram_type == "loop_execution_flowchart":
        return (
            "Generate a Mermaid flowchart (flowchart TD) illustrating loop execution flow. "
            "Include 4 distinct stages: Initialization -> Condition Check (Decision diamond) -> "
            "Loop Body (if True) -> Update / Increment step -> Loop back to Condition. "
            "Also show Exit branch (if False). Keep node labels concise and valid."
        )
    elif diagram_type == "conditional_decision_diagram":
        return (
            "Generate a Mermaid flowchart (flowchart TD) showing decision branching. "
            "Display Condition test diamond { condition? }, True branch path, False/Else branch path, "
            "and convergence at subsequent code. Use clear, unescaped node labels."
        )
    elif diagram_type == "array_index_memory_diagram":
        return (
            "Generate a Mermaid diagram (flowchart LR) showing array elements in contiguous memory. "
            "Display indices (0, 1, 2, ...) above or within elements, corresponding stored values, "
            "and 0-based boundary notation arr[0] to arr[N-1]."
        )
    elif diagram_type == "function_call_stack_diagram":
        return (
            "Generate a Mermaid flowchart (flowchart TD) showing function execution. "
            "Illustrate caller (main) -> parameter passing by value -> callee stack execution -> "
            "return value back to caller."
        )
    elif diagram_type == "string_null_terminator_diagram":
        return (
            "Generate a Mermaid diagram (flowchart LR) showing null-terminated string memory cells. "
            "Show each character cell followed by the mandatory '\\0' null terminator at the final index."
        )
    else:
        return (
            f"Generate a clear Mermaid flowchart (flowchart TD) outlining the core logical flow of {topic}. "
            "Keep node IDs alphanumeric and labels clear for a PPS C programming student."
        )


class PersonalizationEngine:
    """Centralized personalization engine for PPS educational content."""

    @staticmethod
    def derive_context(
        student_profile: StudentProfile,
        topic: str,
        learning_state: Optional[Dict[str, Any]] = None,
        performance_history: Optional[str] = None,
        subtopic: Optional[str] = None,
        learning_cycle: Optional[int] = None,
        remediation_focus: Optional[str] = None,
        subtopic_state: Optional[Dict[str, Any]] = None,
    ) -> PersonalizationContext:
        """Derive normalized personalization context from real student profile and state.

        Does not invent missing data. When a field is unavailable, uses explicit neutral defaults.
        Subtopic-specific mastery takes precedence over general topic mastery.
        """
        raw_state = learning_state or {}
        sub_raw = subtopic_state or {}

        # 1. Topic-specific mastery vs overall mastery
        topic_mastery: float
        if topic in student_profile.mastery_levels:
            topic_mastery = float(student_profile.mastery_levels[topic])
        elif "mastery" in raw_state and raw_state["mastery"] is not None:
            topic_mastery = float(raw_state["mastery"])
        else:
            topic_mastery = 0.0

        # Overall mastery from Learning Twin or average of known topic masteries
        overall_mastery: float
        if "mastery" in raw_state and raw_state["mastery"] is not None:
            overall_mastery = float(raw_state["mastery"])
        elif student_profile.mastery_levels:
            overall_mastery = sum(student_profile.mastery_levels.values()) / len(student_profile.mastery_levels)
        else:
            overall_mastery = topic_mastery

        # Subtopic resolution & subtopic-specific mastery
        valid_nodes = get_subtopics_for_topic(normalize_topic_key(topic))
        valid_ids = {n.id for n in valid_nodes}
        valid_titles = {n.title.strip().lower() for n in valid_nodes}

        # Sanitize any subtopic string that belongs to a different topic
        if subtopic:
            clean_sub = subtopic.strip().lower()
            if subtopic not in valid_ids and clean_sub not in valid_titles:
                logger.warning("Sanitizing mismatched subtopic '%s' for topic '%s'", subtopic, topic)
                subtopic = sub_raw.get("title") or (valid_nodes[0].title if valid_nodes else None)

        target_subtopic = subtopic or sub_raw.get("title") or sub_raw.get("id")
        subtopic_id = sub_raw.get("id") or (valid_nodes[0].id if valid_nodes else None)
        subtopic_mastery: float

        if sub_raw and sub_raw.get("attempts", 0) > 0 and "mastery" in sub_raw and sub_raw["mastery"] is not None:
            subtopic_mastery = float(sub_raw["mastery"])
            effective_mastery_for_tier = subtopic_mastery
        elif target_subtopic and target_subtopic in student_profile.mastery_levels and student_profile.mastery_levels[target_subtopic] > 0:
            subtopic_mastery = float(student_profile.mastery_levels[target_subtopic])
            effective_mastery_for_tier = subtopic_mastery
        elif target_subtopic and subtopic_id and subtopic_id in student_profile.mastery_levels and student_profile.mastery_levels[subtopic_id] > 0:
            subtopic_mastery = float(student_profile.mastery_levels[subtopic_id])
            effective_mastery_for_tier = subtopic_mastery
        else:
            subtopic_mastery = float(sub_raw["mastery"]) if (sub_raw and "mastery" in sub_raw and sub_raw["mastery"] is not None) else 0.0
            effective_mastery_for_tier = topic_mastery

        # 2. Strict documented mastery tier evaluation
        if effective_mastery_for_tier < MASTERY_THRESHOLD_BEGINNER_MAX:
            mastery_tier = "Beginner"
        elif effective_mastery_for_tier < MASTERY_THRESHOLD_INTERMEDIATE_MAX:
            mastery_tier = "Intermediate"
        else:
            mastery_tier = "Advanced"

        # 3. Learning pace normalization
        raw_pace = (
            raw_state.get("learning_pace")
            or student_profile.preferred_pace
            or "moderate"
        )
        pace_str = str(raw_pace).strip().lower()
        if "slow" in pace_str or pace_str == "easy":
            normalized_pace = "slow"
        elif "fast" in pace_str:
            normalized_pace = "fast"
        else:
            normalized_pace = "moderate"

        # 4. Learning style & difficulties
        learning_style = student_profile.learning_style or "balanced"
        recommended_difficulty = str(
            raw_state.get("recommended_difficulty") or ("Easy" if mastery_tier == "Beginner" else ("Hard" if mastery_tier == "Advanced" else "Medium"))
        )
        predicted_mastery_level = str(
            raw_state.get("predicted_mastery_level") or mastery_tier
        )

        accuracy_val = (
            float(raw_state["accuracy"])
            if "accuracy" in raw_state and raw_state["accuracy"] is not None
            else None
        )
        attempts_val = (
            float(raw_state["attempts"])
            if "attempts" in raw_state and raw_state["attempts"] is not None
            else None
        )
        time_val = (
            float(raw_state["time_taken"])
            if "time_taken" in raw_state and raw_state["time_taken"] is not None
            else None
        )

        # 5. Adaptive Cycle Tracking
        max_cycles = get_max_cycles_for_tier(mastery_tier)
        cycle_num = int(learning_cycle or sub_raw.get("learning_cycle") or 1)
        cycle_num = max(1, min(max_cycles, cycle_num))

        # Identified misconceptions and previous errors
        misconceptions = list(student_profile.common_misconceptions or [])
        if sub_raw.get("identified_misconceptions"):
            for m in sub_raw["identified_misconceptions"]:
                if m not in misconceptions:
                    misconceptions.append(m)

        err_cats = list(sub_raw.get("error_categories") or [])
        rem_focus = remediation_focus or sub_raw.get("remediation_focus") or ""

        # 6. Diagram Selection
        diagram_target = target_subtopic or topic
        diagram_type = select_diagram_type_for_topic(diagram_target, mastery_tier)
        diagram_directive = build_diagram_directive(diagram_type, diagram_target, mastery_tier)

        strategy, pattern_name = PersonalizationEngine._compute_strategy(
            mastery_tier=mastery_tier,
            topic_mastery=effective_mastery_for_tier,
            overall_mastery=overall_mastery,
            learning_pace=normalized_pace,
            diagram_type=diagram_type,
            diagram_directive=diagram_directive,
            learning_cycle=cycle_num,
            remediation_focus=rem_focus,
        )

        # Derive pedagogical rationale and concept focus from observed profile state
        subject_name = f"{topic}: {target_subtopic}" if target_subtopic and target_subtopic != topic else topic
        if misconceptions:
            concept_focus = f"Identified error patterns: {'; '.join(misconceptions)}"
        else:
            concept_focus = f"Core syllabus fundamentals and memory mechanics for {subject_name}"

        # Granular student-adaptive explanation
        if mastery_tier == "Beginner":
            if overall_mastery >= MASTERY_THRESHOLD_INTERMEDIATE_MAX:
                rationale = (
                    f"Student has strong overall programming knowledge ({overall_mastery:.2f}), "
                    f"but is developing in {subject_name} ({subtopic_mastery:.2f}). Instruction bridges known C concepts "
                    f"to this specific mechanism with guided diagnostics (Cycle {cycle_num} of {max_cycles})."
                )
            elif normalized_pace == "slow":
                rationale = (
                    f"Student is establishing fundamentals at a measured pace ({subtopic_mastery:.2f} mastery); "
                    f"Cycle {cycle_num} of {max_cycles} teaches from core memory primitives, uses intuitive real-world analogies, "
                    f"provides small (<15 lines) C code, and granular line-by-line tracing."
                )
            else:
                rationale = (
                    f"Student has introductory mastery ({subtopic_mastery:.2f}); "
                    f"Cycle {cycle_num} of {max_cycles} focuses directly on core syntactic rules, memory representations, "
                    f"and targeted diagnostic checks to resolve prerequisite gaps quickly."
                )
        elif mastery_tier == "Intermediate":
            rationale = (
                f"Student has established basic understanding ({subtopic_mastery:.2f} mastery); "
                f"Cycle {cycle_num} of {max_cycles} recaps essential rules and advances to practical multi-statement C programs, "
                f"execution flow tracing, and output prediction."
            )
        else:
            rationale = (
                f"Student demonstrates strong mastery ({subtopic_mastery:.2f}); "
                f"Cycle {cycle_num} of {max_cycles} skips introductory definitions to focus on advanced C semantics, "
                f"edge cases, pointer indirection, and robust modular design."
            )

        if rem_focus:
            rationale += f" Remediation objective: {rem_focus}."

        summary = {
            "mastery_tier": mastery_tier,
            "topic_mastery": f"{topic_mastery:.2f}",
            "subtopic_mastery": f"{subtopic_mastery:.2f}",
            "learning_cycle": f"Cycle {cycle_num} of {max_cycles}",
            "learning_pace": normalized_pace,
            "pattern": pattern_name,
            "instructional_strategy": strategy.teaching_approach,
            "explanation_depth": strategy.explanation_depth,
            "scaffolding": strategy.scaffolding_level,
            "code_complexity": strategy.code_complexity,
            "practice_complexity": strategy.practice_complexity,
            "diagram": diagram_type,
            "concept_focus": concept_focus,
            "rationale": rationale,
            "remediation_focus": rem_focus,
        }

        return PersonalizationContext(
            student_id=student_profile.student_id or "Not enough data available",
            target_topic=topic,
            topic_mastery=round(topic_mastery, 3),
            overall_mastery=round(overall_mastery, 3),
            mastery_tier=mastery_tier,
            learning_pace=normalized_pace,
            preferred_learning_style=learning_style,
            recommended_difficulty=recommended_difficulty,
            predicted_mastery_level=predicted_mastery_level,
            subtopic=target_subtopic,
            subtopic_id=subtopic_id,
            subtopic_mastery=round(subtopic_mastery, 3),
            learning_cycle=cycle_num,
            max_cycles=max_cycles,
            remediation_focus=rem_focus,
            previous_errors=err_cats,
            common_misconceptions=misconceptions,
            accuracy=accuracy_val,
            attempt_count=attempts_val,
            average_time_seconds=time_val,
            pattern_name=pattern_name,
            strategy=strategy,
            personalization_summary=summary,
        )

    @staticmethod
    def _compute_strategy(
        mastery_tier: str,
        topic_mastery: float,
        overall_mastery: float,
        learning_pace: str,
        diagram_type: str,
        diagram_directive: str,
        learning_cycle: int = 1,
        remediation_focus: str = "",
    ) -> tuple[InstructionalStrategy, str]:
        """Compute the 15 pedagogical dimensions deterministically."""

        # Pattern E: Strong overall performance (>= 0.60) but topic-specific weakness (< 0.40)
        if overall_mastery >= 0.60 and topic_mastery < MASTERY_THRESHOLD_BEGINNER_MAX:
            pattern_name = f"Strong overall foundation with topic-specific gap (Cycle {learning_cycle})"
            strategy = InstructionalStrategy(
                explanation_depth="targeted foundational (bridge from familiar C programming concepts)",
                teaching_approach="analogical bridge connecting known C concepts to this new topic",
                cognitive_difficulty="introductory to this specific topic, respecting existing programming maturity",
                code_complexity="clean minimal syntax highlighting the new mechanism without trivializing",
                example_selection="focused PPS examples isolating the specific difficult mechanism",
                step_granularity="granular steps for the new topic mechanism while assuming standard syntax familiarity",
                scaffolding_level="guided scaffolding focused strictly on the gap concept",
                practice_complexity="scaffolded diagnostic practice transitioning quickly to standard application",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="supportive, recognizing prior programming capability while clarifying this topic",
                misconception_strategy="explicit comparison showing how this topic differs from already-mastered concepts",
                roadmap_sequencing="targeted prerequisite bridge followed by rapid integration with advanced curriculum",
                response_structure="structured: Bridge from Known Concepts -> Mechanics -> Code -> Edge Cases",
                amount_of_explanation="moderate and focused, avoiding redundant basic programming lectures",
                revision_strategy="targeted verification checks on the newly introduced concept",
            )
            return strategy, pattern_name

        # Beginner Fast Pace (Pattern B)
        if mastery_tier == "Beginner" and learning_pace == "fast" and learning_cycle == 1:
            pattern_name = "Low mastery / fast pace (Efficient gap resolution)"
            strategy = InstructionalStrategy(
                explanation_depth="foundational but concise, zeroing in directly on the core conceptual mechanics",
                teaching_approach="direct mechanism explanation with concise remedial examples to address gaps fast",
                cognitive_difficulty="introductory to core concepts without slow pacing or verbose narrative",
                code_complexity="concise C examples demonstrating correct syntax and immediate execution flow",
                example_selection="direct, practical PPS code examples targeting the specific difficulty",
                step_granularity="moderate-sized logical steps highlighting cause and effect directly",
                scaffolding_level="focused scaffolding, providing quick diagnostic checks rather than long hand-holding",
                practice_complexity="quick-fire conceptual checks and targeted code-reading problems",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="direct, actionable, explaining exactly why an error occurred and how to fix it",
                misconception_strategy="rapid contrast tables showing correct vs incorrect code patterns",
                roadmap_sequencing="compressed remedial path focusing on core hurdles to accelerate progression",
                response_structure="compact: Core Rule -> Direct Code Demonstration -> Pitfall Contrast -> Rapid Check",
                amount_of_explanation="concise, high signal-to-noise ratio, avoiding repetitive storytelling",
                revision_strategy="rapid conceptual checkpoints verifying root understanding before moving ahead",
            )
            return strategy, pattern_name

        # Adaptive Cycle specific strategies for Weak Learners (< 0.40)
        if mastery_tier == "Beginner":
            if learning_cycle == 1:
                pattern_name = f"Low mastery / {learning_pace} pace (Deep foundational support)"
                strategy = InstructionalStrategy(
                    explanation_depth="foundational first-principles: explain what variables are, RAM cells, and byte memory addresses using concrete analogies before introducing syntax",
                    teaching_approach="step-by-step concrete breakdown, introducing one concept at a time",
                    cognitive_difficulty="introductory, low cognitive load, zero ambiguous jargon, avoiding multiple difficult concepts simultaneously",
                    code_complexity="simple, short C snippets (<15 lines) with comprehensive line-by-line comments",
                    example_selection="everyday intuitive analogies followed by simple C code demonstration",
                    step_granularity="small, highly granular sequential steps with intermediate trace values and expected output explanation",
                    scaffolding_level="high scaffolding, explicit walkthroughs, and guided hints before full solutions",
                    practice_complexity="introductory single-concept exercises with starting templates and hint ladders",
                    diagram_type=diagram_type,
                    diagram_recommendation=diagram_directive,
                    feedback_style="supportive, encouraging, breaking down errors into gentle corrective hints",
                    misconception_strategy="proactive clarification of common beginner pitfalls before student encounters them",
                    roadmap_sequencing="sequential foundational milestones with ample reinforcement checkpoints",
                    response_structure="delineated: Concept Analogy -> Syntax Breakdown -> Annotated Code -> Walkthrough -> Guided Practice",
                    amount_of_explanation="thorough and detailed, leaving no implicit assumptions unexplained",
                    revision_strategy="frequent conceptual check-ins and repetitive reinforcement of core primitives",
                )
                return strategy, pattern_name
            elif learning_cycle == 2:
                pattern_name = f"Weak Learner Cycle 2: Concept Reinforcement & Memory Layout ({learning_pace} pace)"
                strategy = InstructionalStrategy(
                    explanation_depth="reinforced foundational: simpler alternative explanation with heavy visual memory layout and address-value contrast",
                    teaching_approach="visual reinforcement and line-by-line execution walkthrough",
                    cognitive_difficulty="foundational with active recall checks, zero advanced edge cases",
                    code_complexity="minimal C snippets (<12 lines) isolating the single core operator or statement",
                    example_selection="visual memory representation paired with concrete C variable tracing",
                    step_granularity="fine-grained tracing showing memory state at every line",
                    scaffolding_level="maximum scaffolding with guided templates and annotated answers",
                    practice_complexity="beginner fill-in-the-blank and guided trace exercises",
                    diagram_type=diagram_type,
                    diagram_recommendation=diagram_directive,
                    feedback_style="gentle, empathetic coaching explaining why output matches memory state",
                    misconception_strategy="direct comparison table of address vs value",
                    roadmap_sequencing="reinforce prerequisite foundation before allowing new concepts",
                    response_structure="reinforced: Memory Visual -> Line-by-Line Code Trace -> Guided Check",
                    amount_of_explanation="clear and visual, emphasizing mental models of RAM",
                    revision_strategy="immediate check on address vs dereference understanding",
                )
                return strategy, pattern_name
            elif learning_cycle == 3:
                pattern_name = f"Weak Learner Cycle 3: Targeted Misconception Remediation ({learning_pace} pace)"
                target_focus = remediation_focus or "observed student error patterns"
                strategy = InstructionalStrategy(
                    explanation_depth=f"targeted remediation focusing specifically on {target_focus}",
                    teaching_approach="error-contrast method: showing the student's exact error pattern alongside the corrected solution",
                    cognitive_difficulty="remedial to intermediate bridge, isolating the confusion point",
                    code_complexity="compact C code specifically highlighting the corrected mistake",
                    example_selection=f"targeted remediation examples addressing {target_focus}",
                    step_granularity="high-precision step tracing around the error trigger line",
                    scaffolding_level="targeted scaffolding focused on the specific misconception",
                    practice_complexity="focused practice problems isolating the misunderstood mechanism",
                    diagram_type=diagram_type,
                    diagram_recommendation=diagram_directive,
                    feedback_style="constructive diagnostic feedback showing why the previous attempt failed",
                    misconception_strategy=f"focused remediation targeting {target_focus}",
                    roadmap_sequencing="misconception resolution milestone before proceeding",
                    response_structure="targeted: Misconception Clarification -> Corrected Pattern -> Practice Challenge",
                    amount_of_explanation="high signal focused strictly on resolving the misconception",
                    revision_strategy="re-testing the specific weak concept",
                )
                return strategy, pattern_name
            elif learning_cycle == 4:
                pattern_name = f"Weak Learner Cycle 4: Guided Code Exercises & Alternative Pathways ({learning_pace} pace)"
                strategy = InstructionalStrategy(
                    explanation_depth="alternative pedagogical perspective using different metaphors and guided practice steps",
                    teaching_approach="scaffolded guided coding with step-by-step hint ladders",
                    cognitive_difficulty="foundational to developing, building confidence through guided exercises",
                    code_complexity="clean standard C code with progressive fill-in tasks",
                    example_selection="practical beginner laboratory exercises with clear starter templates",
                    step_granularity="semi-granular with student deduction prompts",
                    scaffolding_level="fading scaffolding: starting with full hints and progressing to partial hints",
                    practice_complexity="paired guided coding exercises with progressive hint ladders",
                    diagram_type=diagram_type,
                    diagram_recommendation=diagram_directive,
                    feedback_style="encouraging, highlighting progress while correcting remaining inaccuracies",
                    misconception_strategy="proactive sanity checks before code compilation",
                    roadmap_sequencing="stabilize competency before final subtopic mastery check",
                    response_structure="guided: Alternative Explanation -> Scaffolded Code -> Hint Ladder Practice",
                    amount_of_explanation="balanced, emphasizing learning by guided doing",
                    revision_strategy="synthesis check across the subtopic",
                )
                return strategy, pattern_name
            else:  # Cycle 5
                pattern_name = f"Weak Learner Cycle 5: Final Mastery Validation & Honest Diagnosis ({learning_pace} pace)"
                strategy = InstructionalStrategy(
                    explanation_depth="comprehensive subtopic summary highlighting must-know invariants and syntax rules",
                    teaching_approach="diagnostic mastery evaluation: assess whether student is ready to progress or requires external revision",
                    cognitive_difficulty="standard subtopic threshold level to validate genuine mastery",
                    code_complexity="standard representative PPS code snippet",
                    example_selection="capstone subtopic problem testing complete conceptual loop",
                    step_granularity="standard logical explanation steps",
                    scaffolding_level="unassisted assessment with fallback remediation summary",
                    practice_complexity="evaluative multiple-choice and code output prediction checks",
                    diagram_type=diagram_type,
                    diagram_recommendation=diagram_directive,
                    feedback_style="honest, transparent progress assessment without false mastery claims",
                    misconception_strategy="final summary of remaining concepts requiring revision",
                    roadmap_sequencing="either advance to next subtopic if score >= 0.70 or mark incomplete with recommendations",
                    response_structure="evaluative: Concept Summary -> Final Check -> Honest Roadmap Recommendation",
                    amount_of_explanation="concise summary and actionable next-steps guidance",
                    revision_strategy="final mastery validation gate",
                )
                return strategy, pattern_name

        # Intermediate Learners (0.40 - 0.70)
        if mastery_tier == "Intermediate":
            pattern_name = f"Intermediate Learner Cycle {learning_cycle}: Concept Expansion & Practical Applications"
            strategy = InstructionalStrategy(
                explanation_depth="mechanistic: recap prerequisites concisely, then explore practical multi-statement C programs, memory layout, and execution tracing",
                teaching_approach="guided code walkthroughs connecting related PPS concepts, output tracing, and debugging exercises",
                cognitive_difficulty="moderate, combining multiple syntax elements into coherent programming patterns",
                code_complexity="moderately complex C programs (15-30 lines) with structured functions and logic",
                example_selection="standard PPS laboratory and textbook problems showing realistic usage and common mistakes",
                step_granularity="moderate steps highlighting control flow transitions and state transformations",
                scaffolding_level="partially guided, gradually fading scaffolding as explanation progresses",
                practice_complexity="moderate application problems, code-tracing exercises, and bug-hunting tasks",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="analytical and constructive, guiding the student to identify their own logic gaps",
                misconception_strategy="highlighting subtle edge cases and explaining common runtime misunderstandings",
                roadmap_sequencing="balanced progression connecting core fundamentals to intermediate PPS topics",
                response_structure="structured: Internal Mechanics -> PPS Code Example -> Execution Trace -> Practice Challenge",
                amount_of_explanation="balanced, combining clear conceptual rationale with technical code trace",
                revision_strategy="progressive challenge problems testing both syntax and execution reasoning",
            )
            return strategy, pattern_name

        # Advanced / Strong Learners (>= 0.70)
        pattern_name = f"Advanced Learner Cycle {learning_cycle}: Challenge-Driven & In-Depth Semantics"
        strategy = InstructionalStrategy(
            explanation_depth="deep technical depth: memory architecture, execution reasoning, complex pointer operations, edge cases, and compiler behavior without elementary definition filler",
            teaching_approach="analytical, first-principles exploration of C semantics, complex code reasoning, and debugging",
            cognitive_difficulty="advanced, including boundary conditions, memory addresses, efficiency, and edge cases",
            code_complexity="idiomatic, robust C code demonstrating pointer indirection, edge cases, modularity, and clean design",
            example_selection="challenging PPS application problems, multi-function implementations, and tricky valid C constructs",
            step_granularity="high-level concise architectural steps, omitting elementary syntax explanations",
            scaffolding_level="minimal scaffolding, promoting autonomous problem solving and rigorous reasoning",
            practice_complexity="challenging application scenarios, edge-case debugging, and algorithmic reasoning",
            diagram_type=diagram_type,
            diagram_recommendation=diagram_directive,
            feedback_style="concise, rigorous, and technical, focusing on optimization, safety, and edge-case coverage",
            misconception_strategy="in-depth analysis of undefined behavior, memory corruption, and subtle semantic pitfalls",
            roadmap_sequencing="accelerated roadmap emphasizing advanced PPS applications and system-level concepts",
            response_structure="technical: Concept Architecture -> Memory / System Behavior -> Idiomatic C Implementation -> Advanced Challenge",
            amount_of_explanation="dense and technical, avoiding elementary introductions or redundant analogies",
            revision_strategy="complex multi-step challenge problems requiring independent synthesis",
        )
        return strategy, pattern_name
        """Compute the 15 pedagogical dimensions deterministically."""

        # Pattern E: Strong overall performance (>= 0.70) but topic-specific weakness (< 0.40)
        if overall_mastery >= MASTERY_THRESHOLD_INTERMEDIATE_MAX and topic_mastery < MASTERY_THRESHOLD_BEGINNER_MAX:
            pattern_name = "Strong overall foundation with topic-specific gap"
            strategy = InstructionalStrategy(
                explanation_depth="targeted foundational (bridge from familiar C programming concepts)",
                teaching_approach="analogical bridge connecting known C concepts to this new topic",
                cognitive_difficulty="introductory to this specific topic, respecting existing programming maturity",
                code_complexity="clean minimal syntax highlighting the new mechanism without trivializing",
                example_selection="focused PPS examples isolating the specific difficult mechanism",
                step_granularity="granular steps for the new topic mechanism while assuming standard syntax familiarity",
                scaffolding_level="guided scaffolding focused strictly on the gap concept",
                practice_complexity="scaffolded diagnostic practice transitioning quickly to standard application",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="supportive, recognizing prior programming capability while clarifying this topic",
                misconception_strategy="explicit comparison showing how this topic differs from already-mastered concepts",
                roadmap_sequencing="targeted prerequisite bridge followed by rapid integration with advanced curriculum",
                response_structure="structured: Bridge from Known Concepts -> Mechanics -> Code -> Edge Cases",
                amount_of_explanation="moderate and focused, avoiding redundant basic programming lectures",
                revision_strategy="targeted verification checks on the newly introduced concept",
            )
            return strategy, pattern_name

        # Pattern A: Low mastery (< 0.40) / Slow pace
        if mastery_tier == "Beginner" and learning_pace == "slow":
            pattern_name = "Low mastery / slow pace (Deep foundational support)"
            strategy = InstructionalStrategy(
                explanation_depth="foundational, terminology defined before use with intuitive real-world analogies",
                teaching_approach="step-by-step concrete breakdown, introducing one concept at a time",
                cognitive_difficulty="introductory, low cognitive load, zero ambiguous jargon",
                code_complexity="simple, short C snippets (<15 lines) with comprehensive line-by-line comments",
                example_selection="everyday intuitive analogies followed by simple C code demonstration",
                step_granularity="small, highly granular sequential steps with intermediate trace values",
                scaffolding_level="high scaffolding, explicit walkthroughs, and guided hints before full solutions",
                practice_complexity="introductory single-concept exercises with starting templates and hint ladders",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="supportive, encouraging, breaking down errors into gentle corrective hints",
                misconception_strategy="proactive clarification of common beginner pitfalls before student encounters them",
                roadmap_sequencing="sequential foundational milestones with ample reinforcement checkpoints",
                response_structure="delineated: Concept Analogy -> Syntax Breakdown -> Annotated Code -> Walkthrough -> Guided Practice",
                amount_of_explanation="thorough and detailed, leaving no implicit assumptions unexplained",
                revision_strategy="frequent conceptual check-ins and repetitive reinforcement of core primitives",
            )
            return strategy, pattern_name

        # Pattern B: Low mastery (< 0.40) / Fast pace
        if mastery_tier == "Beginner" and learning_pace == "fast":
            pattern_name = "Low mastery / fast pace (Efficient gap resolution)"
            strategy = InstructionalStrategy(
                explanation_depth="foundational but concise, zeroing in directly on the core conceptual mechanics",
                teaching_approach="direct mechanism explanation with concise remedial examples to address gaps fast",
                cognitive_difficulty="introductory to core concepts without slow pacing or verbose narrative",
                code_complexity="concise C examples demonstrating correct syntax and immediate execution flow",
                example_selection="direct, practical PPS code examples targeting the specific difficulty",
                step_granularity="moderate-sized logical steps highlighting cause and effect directly",
                scaffolding_level="focused scaffolding, providing quick diagnostic checks rather than long hand-holding",
                practice_complexity="quick-fire conceptual checks and targeted code-reading problems",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="direct, actionable, explaining exactly why an error occurred and how to fix it",
                misconception_strategy="rapid contrast tables showing correct vs incorrect code patterns",
                roadmap_sequencing="compressed remedial path focusing on core hurdles to accelerate progression",
                response_structure="compact: Core Rule -> Direct Code Demonstration -> Pitfall Contrast -> Rapid Check",
                amount_of_explanation="concise, high signal-to-noise ratio, avoiding repetitive storytelling",
                revision_strategy="rapid conceptual checkpoints verifying root understanding before moving ahead",
            )
            return strategy, pattern_name

        # Pattern C: Intermediate mastery (0.40 - 0.70) / Moderate pace
        if mastery_tier == "Intermediate":
            pattern_name = "Intermediate mastery / moderate pace (Core reinforcement & progressive challenge)"
            strategy = InstructionalStrategy(
                explanation_depth="mechanistic, explaining how the C constructs work internally and in memory",
                teaching_approach="guided code walkthroughs connecting related PPS concepts (e.g. arrays & pointers)",
                cognitive_difficulty="moderate, combining multiple syntax elements into coherent programming patterns",
                code_complexity="moderately complex C programs (15-30 lines) with structured functions and logic",
                example_selection="standard PPS laboratory and textbook problems showing realistic usage",
                step_granularity="moderate steps highlighting control flow transitions and state transformations",
                scaffolding_level="partially guided, gradually fading scaffolding as explanation progresses",
                practice_complexity="moderate application problems, code-tracing exercises, and bug-hunting tasks",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="analytical and constructive, guiding the student to identify their own logic gaps",
                misconception_strategy="highlighting subtle edge cases and explaining common runtime misunderstandings",
                roadmap_sequencing="balanced progression connecting core fundamentals to intermediate PPS topics",
                response_structure="structured: Internal Mechanics -> PPS Code Example -> Execution Trace -> Practice Challenge",
                amount_of_explanation="balanced, combining clear conceptual rationale with technical code trace",
                revision_strategy="progressive challenge problems testing both syntax and execution reasoning",
            )
            return strategy, pattern_name

        # Pattern D: High mastery (>= 0.70) / Fast pace
        if mastery_tier == "Advanced" and learning_pace == "fast":
            pattern_name = "High mastery / fast pace (Advanced depth & independent problem-solving)"
            strategy = InstructionalStrategy(
                explanation_depth="deep technical depth, memory architecture, execution reasoning, and edge cases",
                teaching_approach="analytical, first-principles exploration of C semantics and compiler behavior",
                cognitive_difficulty="advanced, including boundary conditions, memory addresses, and efficiency considerations",
                code_complexity="idiomatic, robust C code demonstrating pointer arithmetic, modularity, and clean design",
                example_selection="challenging PPS application problems, multi-function implementations, and edge cases",
                step_granularity="high-level concise architectural steps, omitting elementary syntax explanations",
                scaffolding_level="minimal scaffolding, promoting autonomous problem solving and rigorous reasoning",
                practice_complexity="challenging application scenarios, edge-case debugging, and algorithmic problems",
                diagram_type=diagram_type,
                diagram_recommendation=diagram_directive,
                feedback_style="concise, rigorous, and technical, focusing on optimization, safety, and edge-case coverage",
                misconception_strategy="in-depth analysis of undefined behavior, memory leaks, and pointer aliasing",
                roadmap_sequencing="accelerated roadmap emphasizing advanced PPS applications and system-level concepts",
                response_structure="technical: Concept Architecture -> Memory / System Behavior -> Idiomatic C Implementation -> Advanced Challenge",
                amount_of_explanation="dense and technical, avoiding elementary introductions or redundant analogies",
                revision_strategy="complex multi-step challenge problems requiring independent synthesis",
            )
            return strategy, pattern_name

        # Advanced tier with moderate/slow pace
        pattern_name = "Advanced mastery (Conceptual depth & edge case mastery)"
        strategy = InstructionalStrategy(
            explanation_depth="thorough technical depth with rigorous explanation of memory and execution layout",
            teaching_approach="analytical, structured walk-through of advanced C language semantics",
            cognitive_difficulty="advanced, focusing on nuances, boundary limits, and robust design",
            code_complexity="idiomatic C code with clear modular design and safety guards",
            example_selection="in-depth PPS scenarios and real-world system programming patterns",
            step_granularity="focused steps through complex mechanics like pointer indirection and stack frames",
            scaffolding_level="low scaffolding, encouraging student derivation of solutions",
            practice_complexity="advanced PPS problems requiring precise memory and pointer understanding",
            diagram_type=diagram_type,
            diagram_recommendation=diagram_directive,
            feedback_style="rigorous and pedagogical, evaluating code robustness and correctness",
            misconception_strategy="detailed examination of subtle semantic traps and undefined behavior",
            roadmap_sequencing="advanced topic mastery with depth in PPS curriculum applications",
            response_structure="structured: Deep Mechanics -> Memory Model -> Robust C Code -> Edge Case Analysis",
            amount_of_explanation="comprehensive technical explanation without elementary filler",
            revision_strategy="synthesis problems testing comprehensive understanding",
        )
        return strategy, pattern_name
