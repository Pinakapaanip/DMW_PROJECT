
"""
Research Analytics Dashboard
----------------------------
Prepares frontend-ready research analytics.

Responsibilities:
    - Generate dashboard KPI cards.
    - Prepare chart datasets.
    - Show publication trends.
    - Analyze research topics and sources.
    - Display top-cited and recent papers.

All returned data is JSON serializable.
"""

from collections import Counter
from datetime import date
from typing import Any, Optional

from . import warehouse


def _safe_string(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _get_year(paper: dict) -> Optional[int]:
    value = paper.get("publication_year") or paper.get("year")

    try:
        year = int(value)
        if 1000 <= year <= 9999:
            return year
    except (TypeError, ValueError):
        pass

    publication_date = _safe_string(
        paper.get("publication_date")
    )

    if len(publication_date) >= 4:
        try:
            year = int(publication_date[:4])
            if 1000 <= year <= 9999:
                return year
        except ValueError:
            pass

    return None


def _get_authors(paper: dict) -> list[str]:
    authors = paper.get("authors", [])

    if not isinstance(authors, list):
        return []

    result = []

    for author in authors:
        if isinstance(author, dict):
            name = (
                author.get("name")
                or author.get("display_name")
                or ""
            )
        else:
            name = author

        name = _safe_string(name)

        if name:
            result.append(name)

    return result


def _get_topics(paper: dict) -> list[str]:
    topics = paper.get("topics", [])

    if not isinstance(topics, list):
        return []

    result = []

    for topic in topics:
        if isinstance(topic, dict):
            name = (
                topic.get("name")
                or topic.get("display_name")
                or ""
            )
        else:
            name = topic

        name = _safe_string(name)

        if name:
            result.append(name)

    return result


def _filter_papers(
    papers: list[dict],
    year: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
) -> list[dict]:
    """Filter papers using publication-year constraints."""

    filtered = []

    for paper in papers:
        paper_year = _get_year(paper)

        if year is not None and paper_year != year:
            continue

        if year_from is not None:
            if paper_year is None or paper_year < year_from:
                continue

        if year_to is not None:
            if paper_year is None or paper_year > year_to:
                continue

        filtered.append(paper)

    return filtered


def _get_publication_timeline(papers: list[dict]) -> list[dict]:
    """Count publications by year."""

    counts = Counter()

    for paper in papers:
        year = _get_year(paper)

        if year is not None:
            counts[year] += 1

    return [
        {
            "year": year,
            "publication_count": counts[year],
        }
        for year in sorted(counts)
    ]


def _get_topic_distribution(
    papers: list[dict],
    limit: int = 10,
) -> list[dict]:
    """Calculate the most common research topics."""

    counts = Counter()

    for paper in papers:
        # Count a topic only once per paper.
        counts.update(set(_get_topics(paper)))

    return [
        {
            "topic": topic,
            "paper_count": count,
        }
        for topic, count in counts.most_common(limit)
    ]


def _get_source_distribution(
    papers: list[dict],
) -> list[dict]:
    """Calculate the number of papers from each source."""

    counts = Counter(
        _safe_string(paper.get("source")) or "Unknown"
        for paper in papers
    )

    return [
        {
            "source": source,
            "paper_count": count,
        }
        for source, count in counts.most_common()
    ]


def _get_top_authors(
    papers: list[dict],
    limit: int = 10,
) -> list[dict]:
    """Find researchers with the most papers in the dataset."""

    author_counts = Counter()

    for paper in papers:
        author_counts.update(set(_get_authors(paper)))

    return [
        {
            "author": author,
            "paper_count": count,
        }
        for author, count in author_counts.most_common(limit)
    ]


def _get_top_cited_papers(
    papers: list[dict],
    limit: int = 10,
) -> list[dict]:
    """Rank papers by citation count."""

    ranked = sorted(
        papers,
        key=lambda paper: _safe_int(
            paper.get("citation_count")
        ),
        reverse=True,
    )

    results = []

    for paper in ranked[:limit]:
        results.append({
            "paper_id": _safe_string(paper.get("paper_id")),
            "title": _safe_string(paper.get("title")),
            "citation_count": _safe_int(
                paper.get("citation_count")
            ),
            "publication_year": _get_year(paper),
            "doi": _safe_string(paper.get("doi")),
            "landing_page_url": _safe_string(
                paper.get("landing_page_url")
            ),
        })

    return results


def _get_recent_papers(
    papers: list[dict],
    limit: int = 10,
) -> list[dict]:
    """Return the most recently published papers."""

    ranked = sorted(
        papers,
        key=lambda paper: (
            _get_year(paper) or 0,
            _safe_string(paper.get("publication_date")),
        ),
        reverse=True,
    )

    results = []

    for paper in ranked[:limit]:
        results.append({
            "paper_id": _safe_string(paper.get("paper_id")),
            "title": _safe_string(paper.get("title")),
            "authors": _get_authors(paper)[:5],
            "publication_year": _get_year(paper),
            "publication_date": _safe_string(
                paper.get("publication_date")
            ),
            "source": _safe_string(paper.get("source")),
            "landing_page_url": _safe_string(
                paper.get("landing_page_url")
            ),
        })

    return results


def _calculate_kpis(papers: list[dict]) -> dict:
    """Calculate key performance indicators."""

    total_papers = len(papers)

    total_citations = sum(
        _safe_int(paper.get("citation_count"))
        for paper in papers
    )

    open_access_count = sum(
        1
        for paper in papers
        if paper.get("is_open_access") is True
    )

    unique_authors = set()

    for paper in papers:
        unique_authors.update(_get_authors(paper))

    unique_topics = set()

    for paper in papers:
        unique_topics.update(_get_topics(paper))

    publication_years = [
        year
        for year in (_get_year(paper) for paper in papers)
        if year is not None
    ]

    return {
        "total_papers": total_papers,
        "total_citations": total_citations,
        "total_authors": len(unique_authors),
        "total_topics": len(unique_topics),
        "open_access_papers": open_access_count,
        "closed_or_unknown_access_papers": (
            total_papers - open_access_count
        ),
        "average_citations_per_paper": round(
            total_citations / total_papers,
            2,
        ) if total_papers else 0,
        "first_publication_year": (
            min(publication_years)
            if publication_years else None
        ),
        "latest_publication_year": (
            max(publication_years)
            if publication_years else None
        ),
    }


def _get_chart_data(papers: list[dict]) -> dict:
    """Prepare datasets for frontend chart components."""

    timeline = _get_publication_timeline(papers)
    topics = _get_topic_distribution(papers, limit=10)
    sources = _get_source_distribution(papers)

    return {
        "publication_timeline": {
            "chart_type": "line",
            "x_key": "year",
            "series": [
                {
                    "data_key": "publication_count",
                    "label": "Publications",
                }
            ],
            "data": timeline,
        },
        "topic_distribution": {
            "chart_type": "bar",
            "x_key": "topic",
            "series": [
                {
                    "data_key": "paper_count",
                    "label": "Papers",
                }
            ],
            "data": topics,
        },
        "source_distribution": {
            "chart_type": "pie",
            "name_key": "source",
            "value_key": "paper_count",
            "data": sources,
        },
    }


def get_dashboard_data(
    papers: list[dict],
    year: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    top_limit: int = 10,
) -> dict:
    """
    Generate the complete research dashboard.

    Parameters:
        papers:
            Normalized research-paper records.

        year:
            Optional exact publication year filter.

        year_from:
            Optional starting publication year.

        year_to:
            Optional ending publication year.

        top_limit:
            Maximum number of records in ranked lists.

    Returns:
        Complete dashboard response.
    """

    if not isinstance(papers, list):
        return {
            "success": False,
            "message": "papers must be a list.",
            "dashboard": None,
        }

    if top_limit < 1 or top_limit > 100:
        return {
            "success": False,
            "message": "top_limit must be between 1 and 100.",
            "dashboard": None,
        }

    if year is not None and (year_from is not None or year_to is not None):
        return {
            "success": False,
            "message": (
                "Use either an exact year or a year range, not both."
            ),
            "dashboard": None,
        }

    if year_from is not None and year_to is not None:
        if year_from > year_to:
            return {
                "success": False,
                "message": "year_from cannot exceed year_to.",
                "dashboard": None,
            }

    valid_papers = [
        paper
        for paper in papers
        if isinstance(paper, dict)
    ]

    filtered_papers = _filter_papers(
        papers=valid_papers,
        year=year,
        year_from=year_from,
        year_to=year_to,
    )

    dashboard = {
        "generated_on": date.today().isoformat(),
        "filters": {
            "year": year,
            "year_from": year_from,
            "year_to": year_to,
        },
        "kpis": _calculate_kpis(filtered_papers),
        "charts": _get_chart_data(filtered_papers),
        "top_authors": _get_top_authors(
            filtered_papers,
            limit=top_limit,
        ),
        "top_cited_papers": _get_top_cited_papers(
            filtered_papers,
            limit=top_limit,
        ),
        "recent_papers": _get_recent_papers(
            filtered_papers,
            limit=top_limit,
        ),
    }

    return {
        "success": True,
        "message": "Research dashboard generated successfully.",
        "dashboard": dashboard,
    }


def get_dashboard_summary(
    papers: list[dict],
) -> dict:
    """Return only the dashboard KPI summary."""

    if not isinstance(papers, list):
        return {
            "success": False,
            "message": "papers must be a list.",
            "kpis": {},
        }

    valid_papers = [
        paper
        for paper in papers
        if isinstance(paper, dict)
    ]

    return {
        "success": True,
        "message": "Dashboard summary generated.",
        "kpis": _calculate_kpis(valid_papers),
    }


def get_dashboard_from_warehouse(
    database_path: Optional[str] = None,
    year: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    top_limit: int = 10,
) -> dict:
    """
    Generate a dashboard directly from the local DuckDB warehouse.

    This function retrieves warehouse records and converts them
    into the normalized format expected by get_dashboard_data().
    """

    connection = None

    try:
        connection = warehouse._connect(database_path)

        rows = connection.execute(
            """
            SELECT
                paper_id,
                title,
                abstract,
                publication_year,
                publication_date,
                source,
                doi,
                journal,
                citation_count,
                is_open_access,
                authors_json,
                topics_json,
                landing_page_url
            FROM research_papers
            """
        ).fetchall()

        papers = []

        import json

        for row in rows:
            try:
                authors = json.loads(row[10] or "[]")
            except (json.JSONDecodeError, TypeError):
                authors = []

            try:
                topics = json.loads(row[11] or "[]")
            except (json.JSONDecodeError, TypeError):
                topics = []

            papers.append({
                "paper_id": row[0],
                "title": row[1],
                "abstract": row[2],
                "publication_year": row[3],
                "publication_date": row[4],
                "source": row[5],
                "doi": row[6],
                "journal": row[7],
                "citation_count": row[8],
                "is_open_access": row[9],
                "authors": authors,
                "topics": topics,
                "landing_page_url": row[12],
            })

        return get_dashboard_data(
            papers=papers,
            year=year,
            year_from=year_from,
            year_to=year_to,
            top_limit=top_limit,
        )

    except Exception as exc:
        return {
            "success": False,
            "message": "Could not generate warehouse dashboard: " + str(exc),
            "dashboard": None,
        }

    finally:
        if connection is not None:
            connection.close()
