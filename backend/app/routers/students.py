from email.mime import base
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.models import ArtifactCache
from app.schemas import StudentPage, StudentRiskCard, StudentSummary

router = APIRouter(prefix="/api", tags=["students"])


@router.get("/windows", dependencies=[Depends(require_role(["admin", "advisor"]))])
async def list_windows():
    return ["W2", "W4", "W6", "W8"]


@router.get(
    "/students/{window}",
    response_model=StudentPage,
    dependencies=[Depends(require_role(["admin", "advisor"]))],
)
async def list_students(
    window: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    flagged: bool = Query(True),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    student_id: int | None = Query(None, description="Filter by student_id"),
):
    base = select(ArtifactCache).where(
        ArtifactCache.window == window,
        ArtifactCache.flagged == flagged,
    )
    if student_id is not None:
        base = base.where(ArtifactCache.student_id == student_id)

    # Total count
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Paginated items
    stmt = base.order_by(desc(ArtifactCache.risk_score)).offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return StudentPage(
        items=[
            StudentSummary(
                student_id=r.student_id,
                presentation=r.presentation,
                risk_score=r.risk_score,
                flagged=r.flagged,
            )
            for r in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/students/{student_id}/{window}",
    response_model=StudentRiskCard,
    dependencies=[Depends(require_role(["admin", "advisor"]))],
)
async def get_student_card(
    student_id: int,
    window: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(ArtifactCache).where(
        ArtifactCache.student_id == student_id,
        ArtifactCache.window == window,
    )
    result = await db.execute(stmt)
    row = result.scalars().first()
    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentRiskCard(
        student_id=row.student_id,
        presentation=row.presentation,
        window=row.window,
        risk_score=row.risk_score,
        threshold_applied=row.threshold_applied,
        flagged=row.flagged,
        top_positive_factors=row.top_positive_factors,
        top_negative_factors=row.top_negative_factors,
        other_factors_sum=row.other_factors_sum,
        base_value=row.base_value,
    )