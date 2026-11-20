from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_role
from app.schemas import SCSQuestion, SCSSubmission

from app.models import SCSResponse
from app.dependencies import CurrentUser

router = APIRouter(prefix="/api/scs", tags=["scs"])

SCS_QUESTIONS = [
    {"id": 1, "text": "I found that the data included all relevant known causal factors with sufficient precision and granularity."},
    {"id": 2, "text": "I understood the explanations within the context of my work."},
    {"id": 3, "text": "I could change the level of detail on demand."},
    {"id": 4, "text": "I did not need support to understand the explanations."},
    {"id": 5, "text": "I found the explanations helped me to understand causality."},
    {"id": 6, "text": "I was able to use the explanations with my knowledge base."},
    {"id": 7, "text": "I did not find inconsistencies between explanations."},
    {"id": 8, "text": "I think that most people would learn to understand the explanations very quickly."},
    {"id": 9, "text": "I did not need more references in the explanations."},
    {"id": 10, "text": "I received the explanations in a timely and efficient manner."},
]


@router.get(
    "/questions",
    response_model=list[SCSQuestion],
    dependencies=[Depends(require_role(["advisor", "admin"]))],
)
async def get_questions():
    return SCS_QUESTIONS

@router.post("/responses")
async def submit_responses(
    submission: SCSSubmission, 
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser  # Adiciona o utilizador atual
):
    # Calcula o score (Soma das respostas / 50)
    total_sum = sum(item.score for item in submission.responses)
    score = total_sum / 50.0

    # Guarda na base de dados
    db_response = SCSResponse(
        user_id=current_user.id,
        responses=[item.model_dump() for item in submission.responses],
        total_score=score
    )
    db.add(db_response)
    await db.commit()

    return {"status": "recorded", "score": score}