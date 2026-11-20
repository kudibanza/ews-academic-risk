"""
Seed the database with the two demo users and a stratified subset of
W8 SHAP artifacts (500 students: 50% flagged, 50% not flagged).
Run from backend/: python -m app.seed
"""
import json
import random
from pathlib import Path

import asyncio
from sqlalchemy import delete, select

from app.auth import hash_password
from app.database import AsyncSessionLocal, Base, engine
from app.models import ArtifactCache, User

ARTIFACTS_PATH = Path("../results/shap_artifacts/") 
WINDOWS = ["W2", "W4", "W6", "W8"]
PRESENTATIONS = ["2013B", "2013J", "2014B", "2014J"]
N_PER_WINDOW = 500
SEED = 42

async def seed_users(session):
    for username, password, role in [
        ("admin", "admin123", "admin"),
        ("advisor", "advisor123", "advisor"),
        ("manager", "manager123", "admin"),
    ]:
        existing = await session.execute(
            select(User).where(User.username == username)
        )
        if existing.scalar_one_or_none() is None:
            session.add(User(
                username=username,
                hashed_password=hash_password(password),
                role=role,
                active=True,
            ))
    await session.commit()
    print("Users seeded: admin / advisor / manager")


def load_window_records(window: str) -> list[dict]:
    """Load all JSONL records for a given window across all presentations."""
    records = []
    for pres in PRESENTATIONS:
        path = ARTIFACTS_PATH / window / f"{pres}.jsonl"
        if not path.exists():
            print(f"[skip] missing {path}")
            continue
        with path.open(encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
    return records


async def seed_artifacts(session):
    await session.execute(delete(ArtifactCache))
    total_inserted = 0

    for window in WINDOWS:
        records = load_window_records(window)
        if not records:
            print(f"[skip] no records for {window}")
            continue

        flagged = [r for r in records if r["flagged"]]
        not_flagged = [r for r in records if not r["flagged"]]

        random.seed(SEED)
        half = N_PER_WINDOW // 2
        sample = (
            random.sample(flagged, min(half, len(flagged)))
            + random.sample(not_flagged, min(half, len(not_flagged)))
        )

        for rec in sample:
            session.add(ArtifactCache(
                student_id=rec["student_id"],
                presentation=rec["presentation"],
                window=rec["window"],
                risk_score=rec["risk_score"],
                threshold_applied=rec["threshold_applied"],
                flagged=rec["flagged"],
                top_positive_factors=rec["top_positive_factors"],
                top_negative_factors=rec["top_negative_factors"],
                other_factors_sum=rec["other_factors_sum"],
                base_value=rec["base_value"],
            ))
        await session.commit()
        total_inserted += len(sample)
        print(f"{window}: {len(sample)} rows seeded "
              f"({len(sample) - min(half, len(not_flagged))} flagged, "
              f"{min(half, len(not_flagged))} not flagged)")

    print(f"Total artifacts seeded: {total_inserted}")


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        await seed_users(session)
        await seed_artifacts(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())