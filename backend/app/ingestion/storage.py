from __future__ import annotations

from collections.abc import Iterable
from typing import Any
from urllib.parse import quote

from rapidfuzz.fuzz import ratio
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import ResearchPaper
from app.search.deduplication import normalize_title


PAPER_FIELDS = (
    "source",
    "source_id",
    "doi",
    "title",
    "abstract",
    "authors",
    "publication_date",
    "publication_year",
    "updated_date",
    "topics",
    "journal",
    "paper_type",
    "language",
    "citation_count",
    "is_open_access",
    "landing_page_url",
    "pdf_url",
    "raw_metadata",
)


def _as_year(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _find_existing(
    db: Session,
    paper: dict[str, Any],
) -> ResearchPaper | None:
    if paper.get("doi"):
        existing = db.scalar(
            select(ResearchPaper).where(
                func.lower(ResearchPaper.doi) == str(paper["doi"]).lower()
            )
        )
        if existing:
            return existing

    title = normalize_title(paper.get("title"))
    if not title:
        return None

    candidates = db.execute(
        select(ResearchPaper.paper_id, ResearchPaper.title)
    ).all()
    for candidate_id, candidate_title in candidates:
        if ratio(title, normalize_title(candidate_title)) >= 95:
            return db.get(ResearchPaper, candidate_id)
    return None


def upsert_papers(
    db: Session,
    papers: Iterable[dict[str, Any]],
    local_files: dict[str, list[dict[str, str]]] | None = None,
) -> dict[str, int]:
    """Persist normalized records to the application's single paper table."""
    local_files = local_files or {}
    inserted = 0
    updated = 0
    duplicates = 0

    for paper in papers:
        paper_id = str(paper.get("paper_id") or "").strip()
        if not paper_id or not paper.get("title"):
            continue

        existing = db.get(ResearchPaper, paper_id) or _find_existing(db, paper)
        if existing is None:
            existing = ResearchPaper(paper_id=paper_id)
            db.add(existing)
            inserted += 1
        else:
            duplicates += int(existing.paper_id != paper_id)
            updated += 1

        for field in PAPER_FIELDS:
            value = paper.get(field)
            if field == "publication_year":
                value = _as_year(value)
            if field == "citation_count":
                try:
                    value = max(0, int(value or 0))
                except (TypeError, ValueError):
                    value = 0
            if field in {"authors", "topics"} and not isinstance(value, list):
                value = []
            if field == "raw_metadata" and not isinstance(value, dict):
                value = {}
            if value is not None:
                setattr(existing, field, value)

        known_hashes = list(existing.file_hashes or [])
        known_filenames = list(existing.local_pdf_files or [])
        for local_file in local_files.get(paper_id, []):
            file_hash = local_file["sha256"]
            filename = local_file["filename"]
            if file_hash not in known_hashes:
                known_hashes.append(file_hash)
                known_filenames.append(filename)
        existing.file_hashes = known_hashes
        existing.local_pdf_files = known_filenames

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "inserted": inserted,
        "updated": updated,
        "duplicates": duplicates,
    }


def paper_to_dict(paper: ResearchPaper) -> dict[str, Any]:
    """Serialize paper metadata without exposing stored filesystem names."""
    local_pdf = bool(paper.local_pdf_files)
    return {
        "paper_id": paper.paper_id,
        "source": paper.source,
        "source_id": paper.source_id,
        "doi": paper.doi,
        "title": paper.title,
        "abstract": paper.abstract,
        "authors": paper.authors or [],
        "publication_date": paper.publication_date,
        "publication_year": paper.publication_year,
        "updated_date": paper.updated_date,
        "topics": paper.topics or [],
        "journal": paper.journal,
        "paper_type": paper.paper_type,
        "language": paper.language,
        "citation_count": paper.citation_count or 0,
        "is_open_access": paper.is_open_access,
        "landing_page_url": paper.landing_page_url,
        "pdf_url": (
            f"/api/v1/papers/{quote(paper.paper_id, safe='')}/pdf"
            if local_pdf
            else paper.pdf_url
        ),
    }


def load_papers(db: Session) -> list[dict[str, Any]]:
    papers = db.scalars(
        select(ResearchPaper).order_by(ResearchPaper.title)
    ).all()
    return [paper_to_dict(paper) for paper in papers]
