from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import User
from app.ingestion.storage import load_papers
from app.search.unified import unified_search


router = APIRouter(prefix="/api/v1/search", tags=["F5 Research paper search"])


@router.get("")
def search_papers(
    query: str = Query(min_length=1, max_length=500),
    mode: Literal["keyword", "semantic", "hybrid"] = "keyword",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    year_from: int | None = None,
    year_to: int | None = None,
    source: str | None = None,
    topic: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(
            status_code=422,
            detail="year_from cannot be greater than year_to.",
        )
    try:
        return unified_search(
            papers=load_papers(db),
            query=query,
            mode=mode,
            limit=limit,
            offset=offset,
            year_from=year_from,
            year_to=year_to,
            source=source,
            topic=topic,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
