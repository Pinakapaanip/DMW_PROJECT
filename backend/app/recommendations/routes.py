from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import (
    Follow,
    LibraryItem,
    ResearcherProfile,
    User,
)
from app.ingestion.storage import load_papers
from app.recommendations.papers import recommend_papers
from app.recommendations.researchers import recommend_researchers


router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["F6 Recommendations"],
)


def _user_preferences(db: Session, user: User) -> dict:
    profile = db.get(ResearcherProfile, user.id)
    followed_users = db.scalars(
        select(User.full_name)
        .join(Follow, Follow.followed_id == User.id)
        .where(Follow.follower_id == user.id)
    ).all()
    return {
        "interests": profile.interests if profile else [],
        "followed_authors": [name for name in followed_users if name],
    }


@router.get("/papers")
def paper_recommendations(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved = db.scalars(
        select(LibraryItem)
        .options(selectinload(LibraryItem.paper))
        .where(LibraryItem.user_id == current_user.id)
    ).all()
    interactions = [
        {
            "paper_id": item.paper.paper_id,
            "action": "save",
            "topics": item.paper.topics or [],
            "authors": item.paper.authors or [],
        }
        for item in saved
    ]
    return recommend_papers(
        papers=load_papers(db),
        user_profile=_user_preferences(db, current_user),
        user_interactions=interactions,
        exclude_paper_ids=[item.paper.paper_id for item in saved],
        limit=limit,
    )


@router.get("/researchers")
def researcher_recommendations(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    followed = db.scalars(
        select(User.username)
        .join(Follow, Follow.followed_id == User.id)
        .where(Follow.follower_id == current_user.id)
    ).all()
    return recommend_researchers(
        papers=load_papers(db),
        user_profile=_user_preferences(db, current_user),
        followed_researchers=followed,
        limit=limit,
    )
