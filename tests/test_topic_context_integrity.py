"""Comprehensive Test Suite for EduAdapt Canonical Topic Context Integrity,
Topic Switching, Subtopic Isolation, Starter Code Scaffolding, and Sandbox Execution.

Verifies:
1. CanonicalTopicContext initialization, validation, and curriculum mapping.
2. Cross-topic subtopic sanitization in PersonalizationEngine.derive_context.
3. Subtopic roadmap exclusivity: subtopics returned belong strictly to the requested topic.
4. Sequential topic transitions (Pointers -> Functions -> Arrays -> Strings -> Structures -> Pointers).
5. Starter code scaffolding integrity (empty function bodies with '// Write your implementation here').
6. Reference solution privacy (server-side only, omitted from student payload).
7. Execution sandbox timeout default >= 30s.
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from eduadapt.api import app
from eduadapt.curriculum.pps_curriculum import PPS_CURRICULUM_TREE, get_subtopics_for_topic
from eduadapt.models.topic_context import CanonicalTopicContext, get_curriculum_unit_for_topic
from eduadapt.teaching.canonical_question_registry import CANONICAL_QUESTIONS
from eduadapt.teaching.personalization import PersonalizationEngine
from eduadapt.interfaces.student_model import StudentProfile

client = TestClient(app)


class TestCanonicalTopicContext:
    def test_context_creation_and_unit_mapping(self):
        ctx = CanonicalTopicContext(
            student_id="S001",
            topic_id="pointers",
            topic_name="Pointers",
            subtopic_id="ptr_intro",
            subtopic_name="Introduction to Memory Addresses and Pointer Concept",
        )
        assert "Unit 4" in ctx.curriculum_unit_id
        assert ctx.is_valid_topic is True
        assert ctx.subtopic_matches_topic is True
        assert ctx.learning_session_id is not None

    def test_functions_unit_mapping(self):
        ctx = CanonicalTopicContext(
            student_id="S002",
            topic_id="functions",
            topic_name="Functions",
            subtopic_id="func_basics",
            subtopic_name="Function Declaration, Definition, and Prototypes",
        )
        assert "Unit 4" in ctx.curriculum_unit_id
        assert ctx.is_valid_topic is True
        assert ctx.subtopic_matches_topic is True

    def test_cross_topic_mismatch_detection(self):
        # A subtopic from Pointers paired with topic Functions
        ctx = CanonicalTopicContext(
            student_id="S001",
            topic_id="functions",
            topic_name="Functions",
            subtopic_id="ptr_arithmetic",
            subtopic_name="Pointer Arithmetic and Address Manipulation",
        )
        assert ctx.subtopic_matches_topic is False
        assert any("does not belong to topic Functions" in n for n in ctx.validation_notes)


class TestPersonalizationSanitization:
    def test_derive_context_sanitizes_foreign_subtopic(self):
        profile = StudentProfile(
            student_id="S001",
            current_topic="Functions",
            mastery_levels={"Functions": 0.55, "Pointers": 0.20},
        )
        # Attempt to pass a Pointer subtopic while topic is Functions
        p_context = PersonalizationEngine.derive_context(
            student_profile=profile,
            topic="Functions",
            subtopic="Introduction to Memory Addresses and Pointer Concept",
        )
        assert p_context.target_topic == "Functions"
        # Should be sanitized to a valid Functions subtopic
        functions_subtopics = [s.title for s in get_subtopics_for_topic("Functions")]
        assert p_context.subtopic in functions_subtopics
        assert "Pointer" not in p_context.subtopic


class TestTopicTransitionsAndApiIntegrity:
    @pytest.mark.parametrize("topic_name,expected_unit_snippet", [
        ("Pointers", "Unit 4"),
        ("Functions", "Unit 4"),
        ("Arrays", "Unit 3"),
        ("Strings", "Unit 3"),
        ("Structures", "Unit 5"),
        ("Pointers", "Unit 4"),
    ])
    @patch("eduadapt.teaching.generator.PersonalizedContentGenerator.generate_practice_problems")
    def test_sequential_topic_switching(self, mock_gen, topic_name, expected_unit_snippet):
        mock_gen.return_value = MagicMock(content="", model_name="Mistral 7B")
        student_id = "S001"
        # 1. Fetch Subtopic Roadmap
        res = client.get(f"/api/subtopics/roadmap/{student_id}/{topic_name}")
        assert res.status_code == 200
        data = res.json()
        assert data["topic"] == topic_name
        assert expected_unit_snippet in data.get("unit", "") or expected_unit_snippet in data.get("curriculum_unit", "")
        subtopics = data["subtopics"]
        assert len(subtopics) > 0

        valid_nodes = get_subtopics_for_topic(topic_name)
        valid_curriculum_titles = {s.title.strip().lower() for s in valid_nodes}
        valid_curriculum_ids = {s.id.strip().lower() for s in valid_nodes}

        for s in subtopics:
            assert s["title"].strip().lower() in valid_curriculum_titles or s["id"].strip().lower() in valid_curriculum_ids

        # 2. Fetch Practice MCQs
        mcq_res = client.get(f"/api/practice/{student_id}/{topic_name}/mcqs")
        assert mcq_res.status_code == 200
        mcq_data = mcq_res.json()
        assert mcq_data["topic"] == topic_name
        assert len(mcq_data["questions"]) == 5

        # 3. Generate Practice Coding Challenge
        p_res = client.post("/api/practice/generate", json={
            "student_id": student_id,
            "topic": topic_name,
        })
        assert p_res.status_code == 200
        p_data = p_res.json()
        assert p_data["topic"] == topic_name
        challenge = p_data["challenge"]

        # Starter code must NOT contain reference solution
        assert "reference_solution" not in challenge
        starter_code = challenge["starter_code"]
        assert any(kw in starter_code for kw in ("// Write your", "// Implement", "Write your", "// TODO"))


class TestStarterCodeScaffolding:
    def test_all_canonical_starter_codes_have_empty_bodies(self):
        for topic, q in CANONICAL_QUESTIONS.items():
            starter = q.starter_code
            ref = q.reference_solution
            assert starter != ref, f"Starter code for {topic} must not match reference solution"
            assert any(kw in starter for kw in ("// Write your", "// Implement", "Write your", "// TODO")), (
                f"Starter code for {topic} must contain implementation placeholder"
            )


class TestCExecutorTimeoutConfiguration:
    def test_default_timeout_is_at_least_30_seconds(self):
        from eduadapt.evaluation.c_executor import CExecutor
        executor = CExecutor()
        assert executor.default_timeout_seconds >= 30.0
