from typing import Annotated

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.database import get_db
from app.dependencies import require_role
from app.models import ArtifactCache, User
from app.schemas import (
    RiskBin, TopFeature, UserCreate, UserOut, UserUpdate, WindowStats,
)

from pathlib import Path

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(["admin"]))],
)

SHAP_IMPORTANCE_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "results" / "tables" / "shap_importance.csv"
)

@router.get("/users", response_model=list[UserOut])
async def list_users(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")
    if body.role not in ("admin", "advisor"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
        active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        if body.role not in ("admin", "advisor"):
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = body.role
    if body.active is not None:
        user.active = body.active
    if body.password is not None:
        if len(body.password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters",
            )
        user.hashed_password = hash_password(body.password)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=UserOut)
async def deactivate_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.active = False
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/stats/{window}", response_model=WindowStats)
async def window_stats(
    window: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(ArtifactCache).where(ArtifactCache.window == window)
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="No data for this window")

    n = len(rows)
    n_flagged = sum(1 for r in rows if r.flagged)
    risk_scores = np.array([r.risk_score for r in rows])

    bins = np.linspace(0.0, 1.0, 11)
    bins = np.round(bins, 2)  # round to avoid floating point issues
    counts, _ = np.histogram(risk_scores, bins=bins)
    risk_bins = [
        RiskBin(bin_start=float(bins[i]), bin_end=float(bins[i + 1]),
                count=int(counts[i]))
        for i in range(len(counts))
    ]

    top_features = []
    if SHAP_IMPORTANCE_PATH.exists():
        imp = pd.read_csv(SHAP_IMPORTANCE_PATH)
        imp_w = imp[imp["window"] == window].sort_values(
            "mean_abs_shap", ascending=False
        ).head(5)
        top_features = [
            TopFeature(feature=row["feature"],
                       mean_abs_shap=np.round(float(row["mean_abs_shap"]),4))
            for _, row in imp_w.iterrows()
        ]

    return WindowStats(
        window=window,
        n_students=n,
        n_flagged=n_flagged,
        flagged_pct=n_flagged / n if n else 0.0,
        risk_bins=risk_bins,
        top_features=top_features,
    )