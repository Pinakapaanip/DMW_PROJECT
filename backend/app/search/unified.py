
"""
unified.py
----------
Unified research paper search service.

Combines keyword, semantic and hybrid search.
Designed for integration with FastAPI REST endpoints.

Search modes:
- keyword
- semantic
- hybrid
"""

from __future__ import annotations

from typing import Any

from .keyword import keyword_search
from .semantic import semantic_search


SUPPORTED_MODES = {
    "keyword",
    "semantic",
    "hybrid",
}


def _merge_search_results(
    keyword_results: list[dict[str, Any]],
    semantic_results: list[dict[str, Any]],
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> list[dict[str, Any]]:
    """
    Merge keyword and semantic results using weighted ranking.

    Results are identified by paper_id.
    Records without paper_id receive a fallback identity.
    """

    combined: dict[str, dict[str, Any]] = {}

    for result in keyword_results:

        identity = (
            result.get("paper_id")
            or result.get("doi")
            or result.get("title")
        )

        if not identity:
            continue

        combined[str(identity)] = {
            **result,
            "_keyword_score": float(
                result.get("relevance_score", 0)
            ),
            "_semantic_score": 0.0,
        }

    for result in semantic_results:

        identity = (
            result.get("paper_id")
            or result.get("doi")
            or result.get("title")
        )

        if not identity:
            continue

        identity = str(identity)

        if identity in combined:

            combined[identity]["_semantic_score"] = float(
                result.get("similarity_score", 0)
            )

            # Preserve metadata already available.
            for key, value in result.items():

                if combined[identity].get(key) in (
                    None, "", [], {}
                ):
                    combined[identity][key] = value

        else:

            combined[identity] = {
                **result,
                "_keyword_score": 0.0,
                "_semantic_score": float(
                    result.get("similarity_score", 0)
                ),
            }

    maximum_keyword = max(
        (
            item["_keyword_score"]
            for item in combined.values()
        ),
        default=0.0,
    )

    def calculate_score(
        item: dict[str, Any],
    ) -> float:

        keyword_score = item["_keyword_score"]

        if maximum_keyword > 0:
            keyword_score /= maximum_keyword

        semantic_score = (
            item["_semantic_score"] + 1
        ) / 2

        semantic_score = max(
            0.0,
            min(1.0, semantic_score),
        )

        return (
            keyword_weight * keyword_score
            + semantic_weight * semantic_score
        )

    results = []

    for item in combined.values():

        item["hybrid_score"] = round(
            calculate_score(item),
            5,
        )

        item.pop("_keyword_score", None)
        item.pop("_semantic_score", None)

        results.append(item)

    results.sort(
        key=lambda item: item["hybrid_score"],
        reverse=True,
    )

    return results


def unified_search(
    papers: list[dict[str, Any]],
    query: str,
    mode: str = "hybrid",
    limit: int = 20,
    offset: int = 0,
    year_from: int | None = None,
    year_to: int | None = None,
    source: str | None = None,
    topic: str | None = None,
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> dict[str, Any]:
    """
    Unified search entry point for frontend integration.

    Args:
        papers: Normalized research paper records.
        query: Search text.
        mode: keyword, semantic or hybrid.
        limit: Maximum number of returned records.
        offset: Pagination offset.
        year_from: Optional minimum publication year.
        year_to: Optional maximum publication year.
        source: Optional arXiv/OpenAlex source filter.
        topic: Optional topic filter.
        keyword_weight: Hybrid keyword ranking weight.
        semantic_weight: Hybrid semantic ranking weight.

    Returns:
        JSON-serializable search response.
    """

    mode = mode.strip().lower()

    if mode not in SUPPORTED_MODES:
        raise ValueError(
            f"Unsupported search mode: {mode}. "
            f"Choose from {sorted(SUPPORTED_MODES)}."
        )

    if not query or not query.strip():
        return {
            "success": False,
            "message": "Search query cannot be empty.",
            "query": query,
            "mode": mode,
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

    if keyword_weight < 0 or semantic_weight < 0:
        raise ValueError(
            "Search weights cannot be negative."
        )

    total_weight = keyword_weight + semantic_weight

    if mode == "hybrid" and total_weight == 0:
        raise ValueError(
            "At least one hybrid search weight must be positive."
        )

    if mode == "keyword":

        response = keyword_search(
            papers=papers,
            query=query,
            limit=limit,
            offset=offset,
            year_from=year_from,
            year_to=year_to,
            source=source,
            topic=topic,
        )

        response["mode"] = "keyword"

        return response

    # Apply common metadata filters before semantic search.
    filtered_papers = []

    for paper in papers:

        year = paper.get("publication_year")

        if year_from is not None or year_to is not None:

            if year is None:
                continue

            try:
                year = int(year)
            except (ValueError, TypeError):
                continue

            if year_from is not None and year < year_from:
                continue

            if year_to is not None and year > year_to:
                continue

        if source and str(
            paper.get("source", "")
        ).lower() != source.lower():
            continue

        if topic:

            topics = paper.get("topics") or []

            if not any(
                topic.casefold() in str(value).casefold()
                for value in topics
            ):
                continue

        filtered_papers.append(paper)

    if mode == "semantic":

        response = semantic_search(
            papers=filtered_papers,
            query=query,
            limit=limit,
            offset=offset,
        )

        response["mode"] = "semantic"

        return response

    # Hybrid search needs both ranking systems.
    # Retrieve a larger candidate set before merging.
    candidate_limit = min(
        max(limit + offset, 100),
        100,
    )

    keyword_response = keyword_search(
        papers=filtered_papers,
        query=query,
        limit=candidate_limit,
        offset=0,
    )

    semantic_response = semantic_search(
        papers=filtered_papers,
        query=query,
        limit=candidate_limit,
        offset=0,
    )

    results = _merge_search_results(
        keyword_results=keyword_response["results"],
        semantic_results=semantic_response["results"],
        keyword_weight=keyword_weight / total_weight,
        semantic_weight=semantic_weight / total_weight,
    )

    total = len(results)

    paginated_results = results[
        offset:offset + limit
    ]

    return {
        "success": True,
        "message": "Hybrid search completed successfully.",
        "query": query,
        "mode": "hybrid",
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(paginated_results) < total,
        "results": paginated_results,
    }
