# EduAdapt PostgreSQL Database Foundation & Setup Guide

## 1. Executive Summary & Objective

This document defines the relational database infrastructure for **EduAdapt**, replacing legacy CSV and JSON flat-file storage with a secure, ACID-compliant, and horizontally scalable PostgreSQL foundation.

The database foundation establishes persistent schema definitions, constraints, indexes, connection pooling, and migrations to support:
- User identity and role management (Argon2id password hashing)
- Student academic profiles and metadata
- Hierarchical curriculum structure (Topics and Subtopics)
- Question bank (MCQ, Coding, Short Answer with difficulty tiers and test cases)
- Initial Diagnostic Assessment attempts and student responses
- Topic- and subtopic-level adaptive learning mastery tracking
- Adaptive learning recommendations
- AI Tutor conversation threads and chronological message histories

---

## 2. Technology Stack

- **Database Engine**: PostgreSQL (Target 15+)
- **Object-Relational Mapping (ORM)**: SQLAlchemy 2.0 (using modern `Mapped` and `mapped_column` type annotations)
- **Database Driver**: `psycopg` (Version 3.x with C-binary acceleration via `psycopg[binary]`)
- **Database Migrations**: Alembic 1.13+
- **Security & Cryptography**: `argon2-cffi` (Argon2id password hashing with automatic salt generation)
- **FastAPI Integration**: Asynchronous engine and session factory (`AsyncSession`) with non-blocking lifecycle management
- **Vector Search Separation**: Qdrant Vector DB is preserved strictly for semantic slide embeddings and PPS curriculum RAG retrieval; no user/account data is stored in Qdrant.

---

## 3. Database Architecture & Directory Structure

```
EduAdapt/
│
├── alembic.ini                              # Alembic configuration file
├── migrations/                              # Database migration scripts
│   ├── env.py                               # Alembic runtime environment & metadata hook
│   ├── script.py.mako                       # Migration template
│   └── versions/
│       └── 0001_initial_foundation.py       # Baseline migration creating all 11 tables
│
├── src/eduadapt/
│   ├── config.py                            # Settings including DATABASE_URL & pooling options
│   └── db/
│       ├── __init__.py                      # DB module export interface
│       ├── base.py                          # DeclarativeBase & TimestampMixin
│       ├── security.py                      # Argon2 password hashing & email normalization
│       ├── session.py                       # Connection pooling, engine, & FastAPI dependencies
│       └── models/
│           ├── __init__.py                  # Table registry exporting Base.metadata
│           ├── user.py                      # User model
│           ├── student.py                   # Student profile model
│           ├── curriculum.py                # CurriculumTopic & CurriculumSubtopic models
│           ├── question.py                  # Question model
│           ├── assessment.py                # DiagnosticAttempt & DiagnosticResponse models
│           ├── progress.py                  # StudentSubtopicMastery & LearningRecommendation
│           └── tutor.py                     # AITutorConversation & AITutorMessage models
│
└── tests/
    └── test_database.py                     # Automated verification test suite
```

---

## 4. Schema Overview & Entity Relationships

### Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o| STUDENTS : "has profile"
    STUDENTS ||--o{ DIAGNOSTIC_ATTEMPTS : "takes"
    DIAGNOSTIC_ATTEMPTS ||--o{ DIAGNOSTIC_RESPONSES : "contains"
    CURRICULUM_TOPICS ||--o{ CURRICULUM_SUBTOPICS : "contains"
    CURRICULUM_SUBTOPICS ||--o{ QUESTIONS : "categorizes"
    QUESTIONS ||--o{ DIAGNOSTIC_RESPONSES : "evaluated in"
    STUDENTS ||--o{ STUDENT_SUBTOPIC_MASTERY : "tracks progress"
    CURRICULUM_SUBTOPICS ||--o{ STUDENT_SUBTOPIC_MASTERY : "mastered by"
    STUDENTS ||--o{ LEARNING_RECOMMENDATIONS : "receives"
    CURRICULUM_SUBTOPICS ||--o{ LEARNING_RECOMMENDATIONS : "recommends"
    STUDENTS ||--o{ AI_TUTOR_CONVERSATIONS : "initiates"
    AI_TUTOR_CONVERSATIONS ||--o{ AI_TUTOR_MESSAGES : "contains"

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string role
        boolean is_active
        boolean is_verified
        timestamp created_at
        timestamp updated_at
        timestamp last_login_at
    }

    STUDENTS {
        uuid id PK
        uuid user_id FK,UK
        string student_code UK
        string full_name
        string college
        string department
        int academic_year
        int semester
        string section
        string avatar_url
        boolean has_completed_diagnostic
        string current_skill_level
        timestamp created_at
        timestamp updated_at
    }

    CURRICULUM_TOPICS {
        uuid id PK
        string name
        string slug UK
        text description
        int display_order
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CURRICULUM_SUBTOPICS {
        uuid id PK
        uuid topic_id FK
        string name
        string slug
        text description
        int display_order
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    QUESTIONS {
        uuid id PK
        uuid subtopic_id FK
        text question_text
        string question_type
        string difficulty_level
        jsonb options
        jsonb correct_answer
        text explanation
        jsonb test_cases
        numeric marks
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    DIAGNOSTIC_ATTEMPTS {
        uuid id PK
        uuid student_id FK
        string assessment_type
        timestamp started_at
        timestamp completed_at
        string status
        numeric total_score
        numeric maximum_score
        string assigned_skill_level
        jsonb result_summary
        timestamp created_at
        timestamp updated_at
    }

    DIAGNOSTIC_RESPONSES {
        uuid id PK
        uuid attempt_id FK
        uuid question_id FK
        jsonb selected_answer
        boolean is_correct
        numeric marks_obtained
        int time_taken_seconds
        timestamp created_at
        timestamp updated_at
    }

    STUDENT_SUBTOPIC_MASTERY {
        uuid id PK
        uuid student_id FK
        uuid subtopic_id FK
        int attempts
        int successes
        numeric accuracy
        numeric mastery_score
        string mastery_status
        timestamp last_attempted_at
        timestamp updated_at
    }

    LEARNING_RECOMMENDATIONS {
        uuid id PK
        uuid student_id FK
        uuid subtopic_id FK
        string recommendation_type
        jsonb recommendation_content
        timestamp issued_at
        string status
        timestamp created_at
    }

    AI_TUTOR_CONVERSATIONS {
        uuid id PK
        uuid student_id FK
        string title
        timestamp created_at
        timestamp updated_at
    }

    AI_TUTOR_MESSAGES {
        uuid id PK
        uuid conversation_id FK
        string role
        text content
        jsonb context
        timestamp created_at
    }
```

---

## 5. Table Specifications & Constraints

### 1. `users`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `email` (unique index), `hashed_password` (Argon2id), `role` (`'student' | 'instructor' | 'admin'`), `is_active` (bool, default true), `is_verified` (bool, default false), `created_at`, `updated_at`, `last_login_at`.
- **Constraints**: Check constraint `ck_users_role` enforcing valid role values.

### 2. `students`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `user_id` (foreign key referencing `users.id` with `RESTRICT`), `student_code` (unique index, optional institutional ID), `full_name`, `college`, `department`, `academic_year`, `semester`, `section`, `avatar_url`, `has_completed_diagnostic` (bool, default false), `current_skill_level`, `created_at`, `updated_at`.
- **Constraints**: Unique constraint on `user_id` ensuring a strict 1:1 user-to-student profile relationship.

### 3. `curriculum_topics`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `name`, `slug` (unique index), `description`, `display_order`, `is_active`, `created_at`, `updated_at`.

### 4. `curriculum_subtopics`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `topic_id` (foreign key referencing `curriculum_topics.id` with `CASCADE`), `name`, `slug`, `description`, `display_order`, `is_active`, `created_at`, `updated_at`.
- **Constraints**: Compound unique constraint `uq_curriculum_subtopics_topic_slug` on `(topic_id, slug)`.

### 5. `questions`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `subtopic_id` (foreign key referencing `curriculum_subtopics.id` with `RESTRICT`), `question_text`, `question_type`, `difficulty_level`, `options` (JSONB), `correct_answer` (JSONB), `explanation`, `test_cases` (JSONB), `marks` (numeric 5,2), `is_active`, `created_at`, `updated_at`.
- **Constraints**:
  - `ck_questions_question_type`: `question_type IN ('MCQ', 'coding', 'short_answer')`
  - `ck_questions_difficulty_level`: `difficulty_level IN ('beginner', 'intermediate', 'advanced')`

### 6. `diagnostic_attempts`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `student_id` (foreign key referencing `students.id` with `RESTRICT`), `assessment_type`, `started_at`, `completed_at`, `status` (`'in_progress' | 'completed' | 'abandoned'`), `total_score`, `maximum_score`, `assigned_skill_level`, `result_summary` (JSONB), `created_at`, `updated_at`.
- **Constraints**: `ck_diagnostic_attempts_status` on valid statuses.

### 7. `diagnostic_responses`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `attempt_id` (foreign key referencing `diagnostic_attempts.id` with `CASCADE`), `question_id` (foreign key referencing `questions.id` with `RESTRICT`), `selected_answer` (JSONB), `is_correct` (boolean), `marks_obtained`, `time_taken_seconds`, `created_at`, `updated_at`.
- **Constraints**: Compound unique constraint `uq_attempt_question_response` on `(attempt_id, question_id)`.

### 8. `student_subtopic_mastery`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `student_id` (FK), `subtopic_id` (FK), `attempts` (int >= 0), `successes` (int >= 0), `accuracy` (numeric 5,4), `mastery_score` (numeric 5,2), `mastery_status`, `last_attempted_at`, `updated_at`.
- **Constraints**:
  - Unique constraint on `(student_id, subtopic_id)`
  - `ck_mastery_attempts_non_negative`: `attempts >= 0`
  - `ck_mastery_successes_non_negative`: `successes >= 0`
  - `ck_mastery_successes_le_attempts`: `successes <= attempts`

### 9. `learning_recommendations`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `student_id` (FK), `subtopic_id` (FK, nullable), `recommendation_type`, `recommendation_content` (JSONB), `issued_at`, `status`, `created_at`.
- **Constraints**: `ck_recommendation_status`: `status IN ('pending', 'accepted', 'completed', 'dismissed')`.

### 10. `ai_tutor_conversations`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `student_id` (foreign key referencing `students.id` with `RESTRICT`), `title`, `created_at`, `updated_at`.

### 11. `ai_tutor_messages`
- **Primary Key**: `id` (UUIDv4)
- **Columns**: `conversation_id` (foreign key referencing `ai_tutor_conversations.id` with `CASCADE`), `role` (`'user' | 'assistant' | 'student' | 'system'`), `content` (text), `context` (JSONB), `created_at`.
- **Constraints**: `ck_tutor_messages_role` on role values.

---

## 6. PostgreSQL Setup Instructions

### Option A: Local Docker (Recommended for Local Dev)
Run a PostgreSQL container using Docker:
```powershell
docker run --name eduadapt-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=eduadapt -p 5432:5432 -d postgres:16-alpine
```

### Option B: Local Windows Native Installation
1. Install PostgreSQL 16+ via Winget or installer:
   ```powershell
   winget install PostgreSQL.PostgreSQL.16
   ```
2. During setup, configure superuser `postgres` and password.
3. Launch `psql` or pgAdmin and create the database:
   ```sql
   CREATE DATABASE eduadapt;
   ```

### Option C: Cloud Managed Database (Supabase, Neon, AWS RDS, GCP Cloud SQL)
Obtain your connection string:
```
postgresql+psycopg://username:password@hostname:5432/eduadapt
```

---

## 7. Configuration & Environment Variables

Add the connection parameters to `.env` in the repository root:
```ini
# Database Configuration (PostgreSQL foundation)
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/eduadapt
DATABASE_ECHO=false
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
DATABASE_POOL_TIMEOUT=30.0
```

> [!NOTE]
> The engine automatically handles `postgresql://` and `postgres://` URLs and transforms them into `postgresql+psycopg://` for both synchronous migrations and asynchronous FastAPI operations.

---

## 8. Migration Commands

To manage database schema revisions using Alembic:

### Inspect Static Migration DDL (Offline Mode)
Generates static SQL without requiring a running PostgreSQL server:
```powershell
$env:PYTHONPATH="src"
python -m alembic upgrade head --sql
```

### Apply Migrations (Online Mode)
Applies pending migrations to the database configured in `DATABASE_URL`:
```powershell
$env:PYTHONPATH="src"
python -m alembic upgrade head
```

### Rollback Migration
Reverts the last applied migration:
```powershell
$env:PYTHONPATH="src"
python -m alembic downgrade -1
```

---

## 9. Verification & Testing

Run the automated database test suite:
```powershell
$env:PYTHONPATH="src"
python -m pytest tests/test_database.py -v
```

The test suite validates:
1. Argon2 password hashing and verification.
2. Email normalization and validation.
3. Dynamic database URL normalization.
4. Unreachable database error handling.
5. Presence of all 11 tables in declarative metadata.
6. Entity creation and cross-table relationship traversal.
7. Role check constraints.
8. Mastery attempts/successes check constraints.
9. Email uniqueness constraints.
10. 1:1 Student user ID uniqueness constraints.
11. Attempt question response uniqueness constraints.
12. Foreign key enforcement.
13. Session persistence across session closures.
14. FastAPI async session dependency lifecycle.
15. Alembic migration compilation.

---

## 10. Existing Flat-File Data Migration Strategy (Phase 7)

The project currently stores student data in:
- `data/assessment_data.csv`: Historical aggregate scores and attempts for mock students (S001–S006).
- `data/student_subtopic_progress.json`: Subtopic-level progress, cycle counts, reading status, and mastery.
- `data/question_history.json`: Student practice and quiz attempts.
- `data/tutor_history.json`: Student conversations with the AI tutor.

### Safe Future Migration Plan (To be executed in Auth/Diagnostic phase):
1. **Preserve Raw Flat Files**: Do not modify or delete existing flat files.
2. **User & Student Seeding**:
   - For each student identifier in the files (e.g., `S001`), seed a user record (`s001@eduadapt.local`) and a student profile (`student_code="S001"`).
3. **Curriculum Ingestion**:
   - Parse `PPS_CURRICULUM_TREE` into `curriculum_topics` and `curriculum_subtopics`.
4. **Progress & History Ingestion**:
   - Map entries from `student_subtopic_progress.json` into `student_subtopic_mastery`.
   - Map entries from `question_history.json` into `diagnostic_attempts` and `diagnostic_responses`.
   - Map entries from `tutor_history.json` into `ai_tutor_conversations` and `ai_tutor_messages`.
5. **Feature Flag Transition**:
   - Introduce an application flag (`STORAGE_BACKEND=db`) to allow gradual cutover from JSON/CSV files to PostgreSQL without downtime or regressions.
