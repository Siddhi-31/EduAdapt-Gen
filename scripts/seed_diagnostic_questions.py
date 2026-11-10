"""Standalone script to seed the database with Curriculum and Diagnostic Questions."""

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
for p in [str(BASE_DIR), str(SRC_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from eduadapt.db.session import get_sync_session_factory
from eduadapt.services.seed_service import seed_database_sync

if __name__ == "__main__":
    print("Starting EduAdapt database seeding...")
    SessionLocal = get_sync_session_factory()
    with SessionLocal() as session:
        result = seed_database_sync(session)
        print("Seeding completed successfully!")
        print(f"Curriculum Topics Seeded:    {result['topics_seeded']}")
        print(f"Curriculum Subtopics Seeded: {result['subtopics_seeded']}")
        print(f"Diagnostic Questions Seeded: {result['questions_seeded']}")
