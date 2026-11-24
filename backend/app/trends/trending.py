
"""
trending.py
-----------
Research trend analysis and discovery.

Provides:
- Popular research topics
- Fast-growing research topics
- Trending research papers
- Publication activity by year
- Topic activity summaries

Uses Python standard library only.
"""

from __future__ import annotations

import math
import re

from collections import Counter, defaultdict
from typing import Any


def _normalize(value: Any) -> str:
    """Normalize text values."""

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower(),
    )


def _to_list(value: Any) -> list:
    """Convert optional values to a list."""

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    return [value]


def _extract_topics(
    paper: dict[str, Any],
) -> list[str]:
    """Extract normalized research topics."""

    topics = []

    for topic in _to_list(paper.get("topics")):

        if isinstance(topic, dict):

            topic = (
                topic.get("name")
                or topic.get("display_name")
                or ""
            )

        normalized = _normalize(topic)

        if normalized and normalized not in topics:
            topics.append(normalized)

    return topics


def _safe_int(value: Any, default: int = 0) -> int:
    """Safely convert values to integers."""

    try:
        return max(0, int(value or 0))
    except (ValueError, TypeError):
        return default


def get_popular_topics(
    papers: list[dict[str, Any]],
    limit: int = 10,
) -> dict[str, Any]:
    """
    Rank research topics by publication frequency.

    Each paper contributes at most one count per topic.
    """

    if not 1 <= limit <= 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    topic_counts = Counter()
    topic_citations = Counter()

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        topics = _extract_topics(paper)

        citations = _safe_int(
            paper.get("citation_count")
        )

        for topic in topics:

            topic_counts[topic] += 1
            topic_citations[topic] += citations

    results = []

    for topic, count in topic_counts.most_common(limit):

        results.append({
            "topic": topic,
            "publication_count": count,
            "total_citations": topic_citations[topic],
            "average_citations": round(
                topic_citations[topic] / count,
                2,
            ),
        })

    return {
        "success": True,
        "metric": "popular_topics",
        "total_topics": len(topic_counts),
        "limit": limit,
        "results": results,
    }


def get_trending_topics(
    historical_topic_counts: dict[str, int],
    current_topic_counts: dict[str, int],
    limit: int = 10,
    minimum_publications: int = 2,
) -> dict[str, Any]:
    """
    Rank topics by growth between two periods.

    A new topic with no historical publications is
    reported separately rather than assigned an
    infinite growth percentage.
    """

    if not 1 <= limit <= 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    if minimum_publications < 1:
        raise ValueError(
            "minimum_publications must be at least 1."
        )

    previous = {
        _normalize(topic): _safe_int(count)
        for topic, count in historical_topic_counts.items()
        if _normalize(topic)
    }

    current = {
        _normalize(topic): _safe_int(count)
        for topic, count in current_topic_counts.items()
        if _normalize(topic)
    }

    results = []

    for topic, current_count in current.items():

        if current_count < minimum_publications:
            continue

        previous_count = previous.get(topic, 0)

        if previous_count == 0:

            growth_rate = None
            status = "new"

        else:

            growth_rate = (
                current_count - previous_count
            ) / previous_count

            status = (
                "growing"
                if growth_rate > 0
                else "declining"
                if growth_rate < 0
                else "stable"
            )

        results.append({
            "topic": topic,
            "previous_publications": previous_count,
            "current_publications": current_count,
            "growth_rate": (
                round(growth_rate * 100, 2)
                if growth_rate is not None
                else None
            ),
            "status": status,
        })

    results.sort(
        key=lambda item: (
            item["status"] == "new",
            item["growth_rate"] or 0,
            item["current_publications"],
        ),
        reverse=True,
    )

    return {
        "success": True,
        "metric": "trending_topics",
        "total": len(results),
        "limit": limit,
        "results": results[:limit],
    }


def get_trending_papers(
    papers: list[dict[str, Any]],
    limit: int = 10,
    year: int | None = None,
) -> dict[str, Any]:
    """
    Rank papers using citation impact and recency.

    Recency is based on publication year.
    This is a discovery ranking, not a measured
    short-term citation-growth metric.
    """

    if not 1 <= limit <= 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    if year is not None:
        year = int(year)

    results = []

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        title = paper.get("title")

        if not title:
            continue

        publication_year = paper.get(
            "publication_year"
        )

        try:
            publication_year = int(publication_year)
        except (ValueError, TypeError):
            publication_year = None

        if year is not None and publication_year != year:
            continue

        citations = _safe_int(
            paper.get("citation_count")
        )

        current_year = year

        if current_year is None:
            from datetime import datetime
            current_year = datetime.now().year

        age = (
            max(0, current_year - publication_year)
            if publication_year is not None
            else 10
        )

        citation_score = math.log1p(citations)

        recency_score = 1 / (1 + age * 0.15)

        final_score = (
            citation_score * 0.75
            + recency_score * 0.25
        )

        authors = []

        for author in _to_list(
            paper.get("authors")
        ):

            if isinstance(author, str):
                authors.append(author)

            elif isinstance(author, dict):

                name = author.get("name")

                if name:
                    authors.append(name)

        results.append({
            "paper_id": paper.get("paper_id"),
            "title": title,
            "abstract": paper.get("abstract"),
            "authors": authors,
            "publication_year": publication_year,
            "citation_count": citations,
            "topics": _extract_topics(paper),
            "landing_page_url": paper.get("landing_page_url"),
            "pdf_url": paper.get("pdf_url"),
            "trending_score": round(
                final_score,
                5,
            ),
        })

    results.sort(
        key=lambda item: item["trending_score"],
        reverse=True,
    )

    return {
        "success": True,
        "metric": "trending_papers",
        "ranking_method": "citation_impact_and_recency",
        "total": len(results),
        "limit": limit,
        "results": results[:limit],
    }


def get_publication_timeline(
    papers: list[dict[str, Any]],
) -> dict[str, Any]:
    """Generate yearly publication statistics."""

    yearly_counts = Counter()
    yearly_citations = Counter()

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        try:
            year = int(
                paper.get("publication_year")
            )
        except (ValueError, TypeError):
            continue

        yearly_counts[year] += 1

        yearly_citations[year] += _safe_int(
            paper.get("citation_count")
        )

    timeline = []

    for year in sorted(yearly_counts):

        count = yearly_counts[year]
        citations = yearly_citations[year]

        timeline.append({
            "year": year,
            "publication_count": count,
            "citation_count": citations,
            "average_citations": round(
                citations / count,
                2,
            ),
        })

    return {
        "success": True,
        "metric": "publication_timeline",
        "total_years": len(timeline),
        "results": timeline,
    }


def get_topic_summary(
    papers: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate a combined research topic summary.

    Useful for research dashboard visualizations.
    """

    topic_counts = Counter()
    topic_citations = Counter()
    topic_years = defaultdict(Counter)

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        topics = _extract_topics(paper)

        citations = _safe_int(
            paper.get("citation_count")
        )

        try:
            year = int(
                paper.get("publication_year")
            )
        except (ValueError, TypeError):
            year = None

        for topic in topics:

            topic_counts[topic] += 1
            topic_citations[topic] += citations

            if year is not None:
                topic_years[topic][year] += 1

    results = []

    for topic, count in topic_counts.most_common():

        results.append({
            "topic": topic,
            "publication_count": count,
            "total_citations": topic_citations[topic],
            "yearly_publications": [
                {
                    "year": year,
                    "count": yearly_count,
                }
                for year, yearly_count
                in sorted(topic_years[topic].items())
            ],
        })

    return {
        "success": True,
        "metric": "topic_summary",
        "total_topics": len(results),
        "results": results,
    }
