from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.assistant.answer import generate_answer
from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import User
from app.ingestion.storage import load_papers


router = APIRouter(prefix="/api/v1/assistant", tags=["F8 RAG assistant"])


class AssistantQuestion(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    retrieval_mode: Literal["keyword", "semantic", "hybrid"] = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    model: str | None = None


@router.post("/ask")
def ask_research_question(
    data: AssistantQuestion,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    response = generate_answer(
        papers=load_papers(db),
        question=data.question,
        retrieval_mode=data.retrieval_mode,
        top_k=data.top_k,
        model=data.model,
    )
    if not response.get("success"):
        raise HTTPException(
            status_code=503,
            detail=response.get("message", "The research assistant could not answer."),
        )
    return response
