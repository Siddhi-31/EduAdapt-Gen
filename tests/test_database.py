"""Comprehensive database verification test suite for EduAdapt.

Verifies:
- Security functions (Argon2 hashing, verification, email normalization)
- Database URL normalization and connection handling
- Schema creation, UUID primary keys, and table presence
- Constraints (unique, check, foreign keys)
- Full data persistence and relationship resolution
- Alembic migration generation
- FastAPI database dependency lifecycle
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine, select, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from eduadapt.db.base import Base
from eduadapt.db.models import (
    User,
    Student,
    CurriculumTopic,
    CurriculumSubtopic,
    Question,
    DiagnosticAttempt,
    DiagnosticResponse,
    StudentSubtopicMastery,
    LearningRecommendation,
    AITutorConversation,
    AITutorMessage,
)
from eduadapt.db.security import hash_password, verify_password, normalize_email
from eduadapt.db.session import (
    normalize_database_url,
    check_database_connection,
    check_database_connection_sync,
    get_db_session,
    get_sync_db_session,
)


@pytest.fixture(scope="module")
def test_db_engine():
    """Create an isolated test engine enforcing foreign key constraints."""
    engine = create_engine("sqlite:///:memory:", echo=False, future=True)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(test_db_engine):
    """Provide a clean session wrapped in a transaction that rolls back after each test."""
    connection = test_db_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, class_=Session, expire_on_commit=False)
    session = SessionLocal()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


# -----------------------------------------------------------------------------
# Security & Normalization Tests
# -----------------------------------------------------------------------------

def test_argon2_password_hashing():
    """Verify Argon2 password hashing and verification."""
    password = "SuperSecretPassword42!"
    hashed = hash_password(password)

    assert hashed.startswith("$argon2id$")
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_email_normalization():
    """Verify email normalization handles whitespace, casing, and invalid formats."""
    assert normalize_email("  Student.One@SRM.EDU  ") == "student.one@srm.edu"
    assert normalize_email("USER@DOMAIN.COM") == "user@domain.com"

    with pytest.raises(ValueError):
        normalize_email("")

    with pytest.raises(ValueError):
        normalize_email("not-an-email")


def test_database_url_normalization():
    """Verify database URL normalization for psycopg 3."""
    url = "postgresql://user:pass@localhost:5432/eduadapt"
    assert normalize_database_url(url, is_async=True) == "postgresql+psycopg://user:pass@localhost:5432/eduadapt"
    assert normalize_database_url(url, is_async=False) == "postgresql+psycopg://user:pass@localhost:5432/eduadapt"

    pg_url = "postgres://user:pass@localhost:5432/eduadapt"
    assert normalize_database_url(pg_url, is_async=True) == "postgresql+psycopg://user:pass@localhost:5432/eduadapt"


def test_connection_unreachable_produces_clear_error():
    """Verify unreachable database configuration produces clear structured error info."""
    invalid_engine = create_engine(
        "postgresql+psycopg://invalid_user:wrong_pass@127.0.0.1:54329/nonexistent",
        connect_args={"connect_timeout": 1},
    )
    res = check_database_connection_sync(invalid_engine)
    assert res["status"] == "unreachable"
    assert "error" in res
    assert res["database"] == "nonexistent"


# -----------------------------------------------------------------------------
# Schema & Model Presence Tests
# -----------------------------------------------------------------------------

def test_all_expected_tables_exist(test_db_engine):
    """Verify all 11 required tables are registered in metadata."""
    expected_tables = {
        "users",
        "students",
        "curriculum_topics",
        "curriculum_subtopics",
        "questions",
        "diagnostic_attempts",
        "diagnostic_responses",
        "student_subtopic_mastery",
        "learning_recommendations",
        "ai_tutor_conversations",
        "ai_tutor_messages",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


# -----------------------------------------------------------------------------
# Full Persistence and Relationships Test
# -----------------------------------------------------------------------------

def test_data_persistence_and_relationships(db_session):
    """Verify creating, inserting, querying, and navigating all 11 models."""
    now = datetime.now(timezone.utc)

    # 1. User
    user = User(
        email=normalize_email("test.alex@example.edu"),
        hashed_password=hash_password("AlexPass123!"),
        role="student",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    assert isinstance(user.id, uuid.UUID)

    # 2. Student
    student = Student(
        user_id=user.id,
        student_code="RA2311003010001",
        full_name="Alex Mercer",
        college="SRM Institute of Science and Technology",
        department="Computer Science and Engineering",
        academic_year=1,
        semester=1,
        has_completed_diagnostic=False,
    )
    db_session.add(student)
    db_session.flush()
    assert student.user.email == "test.alex@example.edu"
    assert user.student_profile.full_name == "Alex Mercer"

    # 3. Curriculum Topic
    topic = CurriculumTopic(
        name="Pointers and Dynamic Memory Allocation",
        slug="pointers-dma",
        description="Core C pointer mechanisms, memory layouts, and heap operations",
        display_order=1,
        is_active=True,
    )
    db_session.add(topic)
    db_session.flush()

    # 4. Curriculum Subtopic
    subtopic = CurriculumSubtopic(
        topic_id=topic.id,
        name="Pointer Arithmetic and Arrays",
        slug="ptr-arithmetic-arrays",
        description="Understanding pointer increments, scaling, and array indexing",
        display_order=1,
        is_active=True,
    )
    db_session.add(subtopic)
    db_session.flush()
    assert len(topic.subtopics) == 1
    assert topic.subtopics[0].slug == "ptr-arithmetic-arrays"

    # 5. Question
    question = Question(
        subtopic_id=subtopic.id,
        question_text="What will `*(arr + 2)` evaluate to for `int arr[] = {10, 20, 30};`?",
        question_type="MCQ",
        difficulty_level="intermediate",
        options={"A": "10", "B": "20", "C": "30", "D": "Address of 30"},
        correct_answer="C",
        explanation="Pointer arithmetic adds 2 * sizeof(int) offsets from arr, dereferencing the 3rd element.",
        marks=Decimal("2.00"),
        is_active=True,
    )
    db_session.add(question)
    db_session.flush()

    # 6. Diagnostic Attempt
    attempt = DiagnosticAttempt(
        student_id=student.id,
        assessment_type="initial_diagnostic",
        started_at=now,
        status="in_progress",
        total_score=Decimal("0.00"),
        maximum_score=Decimal("100.00"),
    )
    db_session.add(attempt)
    db_session.flush()

    # 7. Diagnostic Response
    response = DiagnosticResponse(
        attempt_id=attempt.id,
        question_id=question.id,
        selected_answer="C",
        is_correct=True,
        marks_obtained=Decimal("2.00"),
        time_taken_seconds=18,
    )
    db_session.add(response)
    db_session.flush()
    assert len(attempt.responses) == 1
    assert attempt.responses[0].is_correct is True

    # 8. Student Subtopic Mastery
    mastery = StudentSubtopicMastery(
        student_id=student.id,
        subtopic_id=subtopic.id,
        attempts=5,
        successes=4,
        accuracy=Decimal("0.8000"),
        mastery_score=Decimal("80.00"),
        mastery_status="mastered",
        last_attempted_at=now,
        updated_at=now,
    )
    db_session.add(mastery)
    db_session.flush()

    # 9. Learning Recommendation
    rec = LearningRecommendation(
        student_id=student.id,
        subtopic_id=subtopic.id,
        recommendation_type="practice_challenge",
        recommendation_content={
            "suggested_action": "proceed_to_advanced_pointers",
            "reason": "High diagnostic accuracy on pointer arithmetic.",
        },
        issued_at=now,
        status="pending",
        created_at=now,
    )
    db_session.add(rec)
    db_session.flush()

    # 10. AI Tutor Conversation
    conversation = AITutorConversation(
        student_id=student.id,
        title="Clarifying Pointer Scaling and Types",
    )
    db_session.add(conversation)
    db_session.flush()

    # 11. AI Tutor Message
    message = AITutorMessage(
        conversation_id=conversation.id,
        role="user",
        content="Why does incrementing an `int*` add 4 bytes instead of 1?",
        context={"subtopic": "ptr-arithmetic-arrays"},
        created_at=now,
    )
    db_session.add(message)
    db_session.flush()

    assert len(conversation.messages) == 1
    assert conversation.messages[0].role == "user"

    # Query back and verify relations across objects
    retrieved_user = db_session.scalars(select(User).where(User.email == "test.alex@example.edu")).first()
    assert retrieved_user is not None
    assert retrieved_user.student_profile is not None
    assert len(retrieved_user.student_profile.diagnostic_attempts) == 1
    assert len(retrieved_user.student_profile.subtopic_mastery_records) == 1
    assert len(retrieved_user.student_profile.learning_recommendations) == 1
    assert len(retrieved_user.student_profile.tutor_conversations) == 1


# -----------------------------------------------------------------------------
# Constraints Verification Tests
# -----------------------------------------------------------------------------

def test_user_role_check_constraint(db_session):
    """Verify User check constraint rejects invalid roles."""
    invalid_user = User(
        email="invalid.role@example.edu",
        hashed_password="hash",
        role="hacker",  # Only 'student', 'instructor', 'admin' permitted
    )
    db_session.add(invalid_user)
    with pytest.raises(SQLAlchemyError):
        db_session.flush()


def test_mastery_successes_le_attempts_check_constraint(db_session):
    """Verify StudentSubtopicMastery rejects successes > attempts."""
    user = User(email="mastery.test@example.edu", hashed_password="hash", role="student")
    db_session.add(user)
    db_session.flush()

    student = Student(user_id=user.id, full_name="Mastery Tester")
    topic = CurriculumTopic(name="Topic", slug="topic-m")
    db_session.add_all([student, topic])
    db_session.flush()

    subtopic = CurriculumSubtopic(topic_id=topic.id, name="Sub", slug="sub-m")
    db_session.add(subtopic)
    db_session.flush()

    invalid_mastery = StudentSubtopicMastery(
        student_id=student.id,
        subtopic_id=subtopic.id,
        attempts=2,
        successes=5,  # Invalid: 5 > 2
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(invalid_mastery)
    with pytest.raises(SQLAlchemyError):
        db_session.flush()


def test_unique_user_email_constraint(db_session):
    """Verify unique constraint on User email."""
    u1 = User(email="duplicate@example.edu", hashed_password="h1")
    u2 = User(email="duplicate@example.edu", hashed_password="h2")
    db_session.add_all([u1, u2])
    with pytest.raises(SQLAlchemyError):
        db_session.flush()


def test_unique_student_user_id_constraint(db_session):
    """Verify 1:1 relationship constraint: one user cannot have two student profiles."""
    user = User(email="one.student@example.edu", hashed_password="h")
    db_session.add(user)
    db_session.flush()

    s1 = Student(user_id=user.id, full_name="Student 1")
    s2 = Student(user_id=user.id, full_name="Student 2")
    db_session.add_all([s1, s2])
    with pytest.raises(SQLAlchemyError):
        db_session.flush()


def test_unique_attempt_question_response_constraint(db_session):
    """Verify attempt cannot record duplicate responses for the same question."""
    user = User(email="resp.test@example.edu", hashed_password="h")
    db_session.add(user)
    db_session.flush()

    student = Student(user_id=user.id, full_name="Resp Tester")
    topic = CurriculumTopic(name="T", slug="t-resp")
    db_session.add_all([student, topic])
    db_session.flush()

    subtopic = CurriculumSubtopic(topic_id=topic.id, name="S", slug="s-resp")
    db_session.add(subtopic)
    db_session.flush()

    question = Question(
        subtopic_id=subtopic.id,
        question_text="Q",
        question_type="MCQ",
        difficulty_level="beginner",
    )
    attempt = DiagnosticAttempt(student_id=student.id, assessment_type="diag")
    db_session.add_all([question, attempt])
    db_session.flush()

    r1 = DiagnosticResponse(attempt_id=attempt.id, question_id=question.id, selected_answer="A")
    r2 = DiagnosticResponse(attempt_id=attempt.id, question_id=question.id, selected_answer="B")
    db_session.add_all([r1, r2])
    with pytest.raises(SQLAlchemyError):
        db_session.flush()


def test_foreign_key_violation_rejected(db_session):
    """Verify foreign key constraint rejects non-existent parent IDs."""
    fake_student_id = uuid.uuid4()
    attempt = DiagnosticAttempt(
        student_id=fake_student_id,
        assessment_type="diagnostic",
    )
    db_session.add(attempt)
    with pytest.raises(SQLAlchemyError):
        db_session.flush()


def test_session_reopen_and_persistence(test_db_engine):
    """Verify data persists across completely closed and reopened sessions."""
    SessionLocal = sessionmaker(bind=test_db_engine, class_=Session, expire_on_commit=False)

    # Session 1: Create and commit
    with SessionLocal() as session1:
        u = User(
            email="session.persist@example.edu",
            hashed_password=hash_password("Pass123!"),
            role="student",
        )
        session1.add(u)
        session1.commit()
        created_user_id = u.id

    # Session 2: Read back from new session
    with SessionLocal() as session2:
        retrieved = session2.get(User, created_user_id)
        assert retrieved is not None
        assert retrieved.email == "session.persist@example.edu"
        session2.delete(retrieved)
        session2.commit()

    # Session 3: Confirm clean deletion
    with SessionLocal() as session3:
        assert session3.get(User, created_user_id) is None


@pytest.mark.asyncio
async def test_async_session_dependency_lifecycle():
    """Verify get_db_session yields an active AsyncSession that commits or rollbacks cleanly."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    async_engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async_factory = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)

    generator = get_db_session(session_factory=async_factory)
    session = await anext(generator)
    try:
        assert session.is_active
        res = await session.execute(text("SELECT 1"))
        assert res.scalar() == 1
    finally:
        try:
            await anext(generator)
        except StopAsyncIteration:
            pass
    await async_engine.dispose()


def test_alembic_sql_generation():
    """Verify Alembic migration script compiles successfully without syntax errors."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()
    assert head_rev in ("0001_initial_foundation", "0002_diagnostic_and_preferences")

