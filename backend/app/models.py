from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON, Boolean, Float, Integer, String, DateTime
from datetime import datetime

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True) 


class ArtifactCache(Base):
    __tablename__ = "artifacts_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, index=True)
    presentation: Mapped[str] = mapped_column(String(8), index=True)
    window: Mapped[str] = mapped_column(String(4), index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    threshold_applied: Mapped[float] = mapped_column(Float)
    flagged: Mapped[bool] = mapped_column(Boolean, index=True)
    top_positive_factors: Mapped[dict] = mapped_column(JSON)
    top_negative_factors: Mapped[dict] = mapped_column(JSON)
    other_factors_sum: Mapped[float] = mapped_column(Float)
    base_value: Mapped[float] = mapped_column(Float)

class SCSResponse(Base):
    __tablename__ = "scs_responses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)  # Quem avaliou
    responses: Mapped[list] = mapped_column(JSON)              # Lista com as 10 respostas
    total_score: Mapped[float] = mapped_column(Float)          # Score calculado (0.0 a 1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)   