"""FastAPI Router for Initial Diagnostic Assessment."""

import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from eduadapt.db.models.student import Student
from eduadapt.db.session import get_db_session
from eduadapt.services.auth_service import get_current_student
from eduadapt.services.diagnostic_service import (
    get_or_create_diagnostic_attempt,
    save_diagnostic_progress,
    submit_diagnostic_assessment,
)

logger = logging.getLogger("eduadapt.routers.diagnostic")

diagnostic_router = APIRouter(prefix="/api/diagnostic", tags=["Initial Diagnostic Assessment"])


class SaveProgressRequest(BaseModel):
    attempt_id: str = Field(..., description="UUID of active diagnostic attempt")
    answers: Dict[str, Any] = Field(default_factory=dict, description="Question answers map {question_id: selected_option}")
    current_index: int = Field(default=0, description="Current question index (0..24)")
    flagged_ids: Optional[List[str]] = Field(default=None, description="List of flagged question IDs")


class SubmitDiagnosticRequest(BaseModel):
    attempt_id: str = Field(..., description="UUID of active diagnostic attempt")
    answers: Dict[str, Any] = Field(default_factory=dict, description="Complete submitted answers")


@diagnostic_router.get(
    "/start",
    summary="Start or resume initial diagnostic assessment",
    description="Returns an active in-progress assessment attempt or creates a reproducible 25-question session.",
)
async def start_diagnostic_endpoint(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Retrieve or initialize student diagnostic assessment."""
    try:
        return await get_or_create_diagnostic_attempt(session=session, student=student)
    except Exception as e:
        logger.error("Failed to start/resume diagnostic: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to load diagnostic assessment: {str(e)}",
        )


@diagnostic_router.post(
    "/save",
    summary="Save in-progress diagnostic state",
    description="Persists answer selections, question index, and review flags during assessment.",
)
async def save_progress_endpoint(
    payload: SaveProgressRequest,
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Persist partial answers to prevent data loss on refresh."""
    try:
        return await save_diagnostic_progress(
            session=session,
            student=student,
            attempt_id=payload.attempt_id,
            answers=payload.answers,
            current_index=payload.current_index,
            flagged_ids=payload.flagged_ids,
        )
    except ValueError as ve:
        err_msg = str(ve).lower()
        if "unauthorized" in err_msg or "does not belong" in err_msg or "not authorized" in err_msg:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(ve))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Failed to save progress: %s", e, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@diagnostic_router.post(
    "/submit",
    summary="Submit initial diagnostic assessment",
    description="Scores responses, calculates cognitive metrics, and updates student profile.",
)
async def submit_diagnostic_endpoint(
    payload: SubmitDiagnosticRequest,
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Evaluate diagnostic submission and return complete performance results."""
    try:
        results = await submit_diagnostic_assessment(
            session=session,
            student=student,
            attempt_id=payload.attempt_id,
            submitted_answers=payload.answers,
        )
        return results
    except ValueError as ve:
        err_msg = str(ve).lower()
        if "unauthorized" in err_msg or "does not belong" in err_msg or "not authorized" in err_msg:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(ve))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error("Failed to submit diagnostic: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit assessment: {str(e)}",
        )


@diagnostic_router.get(
    "/results",
    summary="Retrieve completed diagnostic results",
    description="Returns the latest verified diagnostic assessment summary for the authenticated student.",
)
async def get_diagnostic_results_endpoint(
    student: Student = Depends(get_current_student),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Fetch student's latest completed diagnostic results."""
    from sqlalchemy import select
    from eduadapt.db.models.assessment import DiagnosticAttempt

    stmt = (
        select(DiagnosticAttempt)
        .where(
            DiagnosticAttempt.student_id == student.id,
            DiagnosticAttempt.status == "completed",
        )
        .order_by(DiagnosticAttempt.completed_at.desc())
    )
    res = await session.execute(stmt)
    latest = res.scalar_one_or_none()

    if not latest or not latest.result_summary:
        return {
            "has_completed": False,
            "message": "No diagnostic assessment completed yet.",
        }

    return {
        "has_completed": True,
        "results": latest.result_summary,
    }
