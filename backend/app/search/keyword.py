
"""
keyword.py
----------
Keyword-based research paper search.

Designed for integration with FastAPI REST endpoints
and frontend applications.

Database-independent. Accepts normalized paper records
and returns JSON-serializable search results.
"""

from __future__ import annotations

import re

from typing import Any


def _normalize(value: Any) -> str:
    """Normalize text for case-insensitive searching."""

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).casefold(),
    ).strip()


def _get_author_names(
    authors: Any,
) -> list[str]:
    """Extract author names from normalized paper records."""

    if not isinstance(authors, list):
        return []

    names = []

    for author in authors:

        if isinstance(author, str):
            name = author

        elif isinstance(author, dict):
            name = author.get("name", "")

        else:
            continue

        if name:
            names.append(str(name))

    return names


def _calculate_relevance(
    paper: dict[str, Any],
    query_terms: list[str],
) -> tuple[float, list[str]]:
    """
    Calculate a weighted keyword relevance score.

    Title matches receive the highest weight.
    Abstract, author and topic matches contribute
    additional relevance.
    """

    title = _normalize(paper.get("title"))
    abstract = _normalize(paper.get("abstract"))

    authors = " ".join(
        _normalize(name)
        for name in _get_author_names(
            paper.get("authors")
        )
    )

    topics = " ".join(
        _normalize(topic)
        for topic in paper.get("topics", [])
    )

    score = 0.0
    matched_terms = []

    for term in query_terms:

        term_score = 0.0

        if term in title:
            term_score += 10.0

        if term in abstract:
            term_score += 3.0

        if term in authors:
            term_score += 2.0

        if term in topics:
            term_score += 5.0

        if term_score > 0:
            matched_terms.append(term)
            score += term_score

    return score, matched_terms


def _public_paper(
    paper: dict[str, Any],
    score: float,
    matched_terms: list[str],
) -> dict[str, Any]:
    """Create a frontend-friendly paper response."""

    authors = _get_author_names(
        paper.get("authors")
    )

    return {
        "paper_id": paper.get("paper_id"),
        "title": paper.get("title"),
        "abstract": paper.get("abstract"),
        "authors": authors,
        "publication_date": paper.get("publication_date"),
        "publication_year": paper.get("publication_year"),
        "doi": paper.get("doi"),
        "topics": paper.get("topics", []),
        "journal": paper.get("journal"),
        "citation_count": paper.get("citation_count", 0),
        "is_open_access": paper.get("is_open_access"),
        "landing_page_url": paper.get("landing_page_url"),
        "pdf_url": paper.get("pdf_url"),
        "relevance_score": round(score, 3),
        "matched_terms": matched_terms,
    }


def keyword_search(
    papers: list[dict[str, Any]],
    query: str,
    limit: int = 20,
    offset: int = 0,
    year_from: int | None = None,
    year_to: int | None = None,
    source: str | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    """
    Search research papers using keywords.

    Args:
        papers: List of normalized research papers.
        query: Search text supplied by the frontend.
        limit: Maximum number of results.
        offset: Number of results to skip.
        year_from: Optional earliest publication year.
        year_to: Optional latest publication year.
        source: Optional source filter (arxiv/openalex).
        topic: Optional topic filter.

    Returns:
        JSON-serializable response containing search results.
    """

    if not isinstance(query, str) or not query.strip():
        return {
            "success": False,
            "message": "Search query cannot be empty.",
            "query": query,
            "total": 0,
            "results": [],
        }

    if not 1 <= limit <= 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    if offset < 0:
        raise ValueError(
            "offset cannot be negative."
        )

    if year_from is not None and year_to is not None:
        if year_from > year_to:
            raise ValueError(
                "year_from cannot be greater than year_to."
            )

    query_terms = list(dict.fromkeys(
        _normalize(term)
        for term in query.split()
        if _normalize(term)
    ))

    scored_results = []

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        if year_from is not None or year_to is not None:

            year = paper.get("publication_year")

            if year is None:
                continue

            try:
                year = int(year)
            except (TypeError, ValueError):
                continue

            if year_from is not None and year < year_from:
                continue

            if year_to is not None and year > year_to:
                continue

        if source:
            if _normalize(paper.get("source")) != _normalize(source):
                continue

        if topic:
            paper_topics = [
                _normalize(item)
                for item in paper.get("topics", [])
            ]

            if not any(
                _normalize(topic) in item
                for item in paper_topics
            ):
                continue

        score, matched_terms = _calculate_relevance(
            paper,
            query_terms,
        )

        if score <= 0:
            continue

        scored_results.append({
            "paper": paper,
            "score": score,
            "matched_terms": matched_terms,
        })

    scored_results.sort(
        key=lambda item: (
            item["score"],
            item["paper"].get("citation_count") or 0,
        ),
        reverse=True,
    )

    total = len(scored_results)

    paginated = scored_results[
        offset:offset + limit
    ]

    results = [
        _public_paper(
            item["paper"],
            item["score"],
            item["matched_terms"],
        )
        for item in paginated
    ]

    return {
        "success": True,
        "message": "Search completed successfully.",
        "query": query,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(results) < total,
        "results": results,
    }
