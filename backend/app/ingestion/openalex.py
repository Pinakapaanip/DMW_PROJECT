
"""
openalex.py
-----------
Fetches scholarly research metadata from the OpenAlex API.

Returns raw records without depending on the project's database.
Supports pagination, retries, filtering and raw response preservation.
"""

from __future__ import annotations

import time
from typing import Any

import httpx


OPENALEX_API_URL = "https://api.openalex.org/works"

USER_AGENT = (
    "ChanakyaResearchCommons/1.0 "
    "(academic research ingestion)"
)


def _extract_authors(authorships: list[dict]) -> list[dict[str, Any]]:
    """Extract author details from OpenAlex authorships."""

    authors = []

    for authorship in authorships:
        author = authorship.get("author") or {}

        authors.append({
            "author_id": author.get("id"),
            "name": author.get("display_name"),
            "orcid": author.get("orcid"),
            "institutions": [
                institution.get("display_name")
                for institution in authorship.get("institutions", [])
                if institution.get("display_name")
            ],
            "is_corresponding": authorship.get(
                "is_corresponding",
                False,
            ),
        })

    return authors


def _normalize_work(work: dict[str, Any]) -> dict[str, Any]:
    """Extract useful metadata while preserving the original record."""

    primary_location = work.get("primary_location") or {}
    source = primary_location.get("source") or {}
    best_oa_location = work.get("best_oa_location") or {}

    topics = [
        topic.get("display_name")
        for topic in work.get("topics", [])
        if topic.get("display_name")
    ]

    concepts = [
        concept.get("display_name")
        for concept in work.get("concepts", [])
        if concept.get("display_name")
    ]

    return {
        "source": "openalex",
        "source_id": work.get("id"),
        "doi": work.get("doi"),
        "title": work.get("title"),
        "abstract_inverted_index": work.get("abstract_inverted_index"),
        "publication_date": work.get("publication_date"),
        "publication_year": work.get("publication_year"),
        "type": work.get("type"),
        "language": work.get("language"),
        "authors": _extract_authors(
            work.get("authorships") or []
        ),
        "institutions": [
            institution.get("display_name")
            for authorship in work.get("authorships", [])
            for institution in authorship.get("institutions", [])
            if institution.get("display_name")
        ],
        "topics": topics,
        "concepts": concepts,
        "journal": source.get("display_name"),
        "journal_issn": source.get("issn_l"),
        "landing_page_url": primary_location.get("landing_page_url"),
        "pdf_url": best_oa_location.get("pdf_url"),
        "is_open_access": (
            work.get("open_access") or {}
        ).get("is_oa"),
        "cited_by_count": work.get("cited_by_count", 0),
        "referenced_works": work.get("referenced_works", []),
        "related_works": work.get("related_works", []),
        "raw_record": work,
    }


def fetch_openalex(
    search_query: str,
    max_results: int = 100,
    page_size: int = 100,
    sort: str = "relevance_score:desc",
    mailto: str | None = None,
    timeout: float = 30.0,
    retries: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch research works from OpenAlex.

    Args:
        search_query: Search phrase for research papers.
        max_results: Maximum number of records to retrieve.
        page_size: Records per API request (maximum 200).
        sort: OpenAlex sorting expression.
        mailto: Optional contact email for API identification.
        timeout: HTTP timeout in seconds.
        retries: Number of retry attempts.

    Returns:
        List of raw OpenAlex records with extracted metadata.
    """

    if not isinstance(search_query, str) or not search_query.strip():
        raise ValueError("Search query cannot be empty.")

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    if not 1 <= page_size <= 200:
        raise ValueError("page_size must be between 1 and 200.")

    if retries < 0:
        raise ValueError("retries cannot be negative.")

    results: list[dict[str, Any]] = []
    cursor = "*"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    with httpx.Client(
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
    ) as client:

        while len(results) < max_results:

            current_page_size = min(
                page_size,
                max_results - len(results),
            )

            params: dict[str, Any] = {
                "search": search_query.strip(),
                "per-page": current_page_size,
                "cursor": cursor,
                "sort": sort,
            }

            if mailto:
                params["mailto"] = mailto

            response = None

            for attempt in range(retries + 1):
                try:
                    response = client.get(
                        OPENALEX_API_URL,
                        params=params,
                    )
                    response.raise_for_status()
                    break

                except httpx.HTTPError:
                    if attempt == retries:
                        raise

                    time.sleep(min(2 ** attempt, 8))

            if response is None:
                raise RuntimeError(
                    "Could not retrieve OpenAlex response."
                )

            try:
                payload = response.json()
            except ValueError as exc:
                raise ValueError(
                    "OpenAlex returned invalid JSON."
                ) from exc

            works = payload.get("results", [])

            for work in works:
                results.append(_normalize_work(work))

            next_cursor = (
                payload.get("meta") or {}
            ).get("next_cursor")

            if not works or not next_cursor:
                break

            cursor = next_cursor

            if len(results) < max_results:
                time.sleep(0.2)

    return results
