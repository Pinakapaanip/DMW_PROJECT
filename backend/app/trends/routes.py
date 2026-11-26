from collections import Counter
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import User
from app.ingestion.storage import load_papers
from app.trends.anomaly import (
    analyze_citation_activity,
    analyze_publication_volume,
    detect_emerging_topics,
)
from app.trends.trending import (
    get_popular_topics,
    get_publication_timeline,
    get_topic_summary,
    get_trending_papers,
    get_trending_topics,
)


router = APIRouter(prefix="/api/v1/trends", tags=["F7 Trends and anomalies"])


def _topics_for_years(papers, current_year: int):
    historical = Counter()
    current = Counter()
    for paper in papers:
        try:
            year = int(paper.get("publication_year"))
        except (TypeError, ValueError):
            continue
        topics = paper.get("topics") or []
        if not isinstance(topics, list):
            continue
        if year > current_year:
            continue
        target = current if year == current_year else historical
        for topic in set(str(item).strip().lower() for item in topics if item):
            if topic:
                target[topic] += 1
    return historical, current


@router.get("/topics")
def popular_topics(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_popular_topics(load_papers(db), limit=limit)


@router.get("/topics/growth")
def topic_growth(
    year: int | None = None,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    papers = load_papers(db)
    historical, current = _topics_for_years(papers, year or date.today().year)
    return {
        "growth": get_trending_topics(
            dict(historical),
            dict(current),
            limit=limit,
        ),
        "emerging": detect_emerging_topics(
            dict(historical),
            dict(current),
        ),
        "summary": get_topic_summary(papers),
    }


@router.get("/papers")
def trending_papers(
    limit: int = Query(default=10, ge=1, le=100),
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_trending_papers(load_papers(db), limit=limit, year=year)


@router.get("/timeline")
def publication_timeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_publication_timeline(load_papers(db))


@router.get("/anomalies")
def research_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    papers = load_papers(db)
    return {
        "publication_volume": analyze_publication_volume(papers),
        "citation_activity": analyze_citation_activity(papers),
    }
