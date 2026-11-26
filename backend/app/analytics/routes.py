from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analytics.dashboard import (
    get_dashboard_data,
    get_dashboard_summary,
)
from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import User
from app.ingestion.storage import load_papers


router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["F9 Analytics"],
)


@router.get("/dashboard")
def research_dashboard(
    year: int | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    top_limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = get_dashboard_data(
        papers=load_papers(db),
        year=year,
        year_from=year_from,
        year_to=year_to,
        top_limit=top_limit,
    )
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result["message"])
    return result


@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_dashboard_summary(load_papers(db))
