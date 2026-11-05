"""Authoritative Canonical Topic Context Model for EduAdapt.

Provides a unified, immutable data contract that encapsulates the active curriculum
topic, subtopic, student state, and personalization tier across the entire lifecycle:
Topic Dropdown -> Selected Topic State -> Subtopic Resolution -> Student Learning State ->
Learning Twin -> Curriculum Retrieval/RAG -> Prompt Construction -> Generation -> Response Parsing ->
Lesson Rendering -> Practice -> Assessment -> Progress Update.
"""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


def get_curriculum_unit_for_topic(topic: str) -> str:
    """Map canonical topic name to its official PPS curriculum unit."""
    t_lower = topic.strip().lower()
    if any(k in t_lower for k in ("variable", "data type", "operator", "expression")):
        return "Unit 1: Fundamentals of C"
    elif any(k in t_lower for k in ("conditional", "loop", "while", "for", "switch")):
        return "Unit 2: Control Structures"
    elif any(k in t_lower for k in ("array", "string")):
        return "Unit 3: Arrays & Strings"
    elif any(k in t_lower for k in ("function", "pointer")):
        return "Unit 4: Functions & Pointers"
    elif any(k in t_lower for k in ("structure", "dynamic memory", "malloc", "free")):
        return "Unit 5: Structures & Dynamic Memory"
    return "Unit 4: Functions & Pointers"


class CanonicalTopicContext(BaseModel):
    """Authoritative canonical topic context used across frontend and backend services."""

    student_id: str = Field(..., description="Stable student identifier (e.g. 'S001')")
    topic_id: str = Field(..., description="Normalized topic key (e.g. 'pointers', 'functions')")
    topic_name: str = Field(..., description="Canonical curriculum topic display name (e.g. 'Pointers')")
    subtopic_id: str = Field(..., description="Unique subtopic identifier (e.g. 'ptr_intro_addresses')")
    subtopic_name: str = Field(..., description="Canonical subtopic display title")
    curriculum_unit_id: Optional[str] = Field(default=None, description="Curriculum unit grouping (e.g. 'Unit 4: Functions & Pointers')")
    learning_session_id: Optional[str] = Field(default=None, description="Unique tracking identifier for this generation session")
    learning_cycle: int = Field(default=1, description="Adaptive learning cycle number (1..5)")
    student_mastery: float = Field(default=0.0, description="Genuine student mastery for this specific topic (0.0..1.0)")
    student_pace: str = Field(default="moderate", description="Student learning pace ('slow', 'moderate', 'fast')")
    personalization_tier: str = Field(default="Beginner", description="Pedagogical depth tier ('Beginner', 'Intermediate', 'Advanced')")
    is_valid_topic: bool = Field(default=True, description="Whether this topic is recognized in the PPS curriculum")
    subtopic_matches_topic: bool = Field(default=True, description="Strict validation that subtopic belongs to topic")
    validation_notes: List[str] = Field(default_factory=list, description="Diagnostic validation logs")

    @model_validator(mode="before")
    @classmethod
    def populate_defaults_and_validate(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        topic_name = data.get("topic_name") or ""
        subtopic_name = data.get("subtopic_name") or ""

        if not data.get("curriculum_unit_id"):
            data["curriculum_unit_id"] = get_curriculum_unit_for_topic(topic_name)

        if not data.get("learning_session_id"):
            data["learning_session_id"] = f"sess_{uuid.uuid4().hex[:12]}"

        # Check subtopic compatibility
        notes = list(data.get("validation_notes") or [])
        from eduadapt.curriculum.pps_curriculum import get_subtopics_for_topic
        valid_subtopics = get_subtopics_for_topic(topic_name)
        valid_titles = [s.title.lower() for s in valid_subtopics]
        valid_ids = [s.id.lower() for s in valid_subtopics]

        sub_lower = subtopic_name.strip().lower()
        sub_id_lower = (data.get("subtopic_id") or "").strip().lower()

        matches = any(sub_lower in vt or vt in sub_lower for vt in valid_titles) or (sub_id_lower in valid_ids)
        if not matches and valid_subtopics:
            data["subtopic_matches_topic"] = False
            notes.append(f"Subtopic '{subtopic_name}' does not belong to topic {topic_name}")
        else:
            data["subtopic_matches_topic"] = True

        data["validation_notes"] = notes
        return data

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
