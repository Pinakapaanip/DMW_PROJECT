
"""
fetch.py
--------
Central collector for research paper sources.

Coordinates OpenAlex and arXiv ingestion and provides
a consistent interface for the F4 pipeline.
"""

from __future__ import annotations

from typing import Any

from .arxiv import fetch_arxiv
from .openalex import fetch_openalex


SUPPORTED_SOURCES = {"arxiv", "openalex", "all"}


def fetch_papers(
    query: str,
    source: str = "all",
    limit: int = 100,
    page_size: int = 100,
    mailto: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    Fetch research papers from selected sources.

    Args:
        query: Research topic or search expression.
        source: arxiv, openalex or all.
        limit: Maximum records per source.
        page_size: Records requested per API page.
        mailto: Optional OpenAlex contact email.

    Returns:
        Dictionary containing records grouped by source.
    """

    if not query or not query.strip():
        raise ValueError("Research query cannot be empty.")

    source = source.strip().lower()

    if source not in SUPPORTED_SOURCES:
        raise ValueError(
            f"Unsupported source '{source}'. "
            f"Choose from {sorted(SUPPORTED_SOURCES)}."
        )

    if limit < 1:
        raise ValueError("limit must be at least 1.")

    if page_size < 1:
        raise ValueError("page_size must be at least 1.")

    collected: dict[str, list[dict[str, Any]]] = {
        "arxiv": [],
        "openalex": [],
    }

    sources = (
        ["arxiv", "openalex"]
        if source == "all"
        else [source]
    )

    errors: dict[str, str] = {}

    for selected_source in sources:

        try:
            if selected_source == "arxiv":
                collected["arxiv"] = fetch_arxiv(
                    query=query,
                    max_results=limit,
                    page_size=page_size,
                )

            elif selected_source == "openalex":
                collected["openalex"] = fetch_openalex(
                    search_query=query,
                    max_results=limit,
                    page_size=min(page_size, 200),
                    mailto=mailto,
                )

        except Exception as exc:
            errors[selected_source] = (
                f"{type(exc).__name__}: {exc}"
            )

    if errors:
        raise RuntimeError(
            f"One or more sources failed: {errors}. "
            f"Successfully collected: "
            f"{ {key: len(value) for key, value in collected.items()} }"
        )

    return collected


def flatten_papers(
    collected: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Combine records from all sources into one list."""

    papers: list[dict[str, Any]] = []

    for source_records in collected.values():
        papers.extend(source_records)

    return papers


def get_collection_summary(
    collected: dict[str, list[dict[str, Any]]],
) -> dict[str, int]:
    """Return the number of records collected per source."""

    summary = {
        source: len(records)
        for source, records in collected.items()
    }

    summary["total"] = sum(summary.values())

    return summary
