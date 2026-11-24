
"""
papers.py
---------
Content-based research paper recommendation engine.

Recommendations use:
- User research interests
- Previously saved and liked papers
- Read and viewed paper history
- Followed authors
- Paper topics and metadata
- Citation counts as a secondary popularity signal

No paid APIs, GPU or external services required.
"""

from __future__ import annotations

import re

from collections import Counter
from datetime import date
from typing import Any


POSITIVE_ACTIONS = {
    "save": 3.0,
    "saved": 3.0,
    "bookmark": 3.0,
    "like": 2.5,
    "liked": 2.5,
    "read": 1.5,
    "view": 0.5,
    "viewed": 0.5,
    "download": 2.0,
    "downloaded": 2.0,
}

NEGATIVE_ACTIONS = {
    "dislike": -2.0,
    "dismiss": -1.0,
    "hide": -2.0,
}


def _normalize(value: Any) -> str:
    """Normalize text for reliable matching."""

    if value is None:
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip().lower(),
    )


def _to_list(value: Any) -> list:
    """Convert optional values into a list."""

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, (tuple, set)):
        return list(value)

    return [value]


def _extract_author_names(
    authors: Any,
) -> list[str]:
    """Extract author names from normalized author records."""

    names = []

    for author in _to_list(authors):

        if isinstance(author, str):
            name = author

        elif isinstance(author, dict):
            name = author.get("name", "")

        else:
            continue

        name = str(name).strip()

        if name:
            names.append(name)

    return names


def _paper_topics(
    paper: dict[str, Any],
) -> list[str]:
    """Extract normalized paper topics."""

    topics = []

    for topic in _to_list(paper.get("topics")):

        if isinstance(topic, dict):
            topic = (
                topic.get("name")
                or topic.get("display_name")
                or ""
            )

        topic = _normalize(topic)

        if topic:
            topics.append(topic)

    return topics


def _get_paper_identity(
    paper: dict[str, Any],
) -> str:
    """Generate a stable paper identity."""

    return str(
        paper.get("paper_id")
        or paper.get("doi")
        or paper.get("source_id")
        or paper.get("title")
        or ""
    ).strip()


def _build_user_preferences(
    user_profile: dict[str, Any] | None,
    user_interactions: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Build user preference weights from profile and activity."""

    profile = user_profile or {}

    topic_weights: Counter = Counter()
    author_weights: Counter = Counter()
    excluded_ids = set()

    # Explicit user interests.
    for topic in _to_list(
        profile.get("interests")
        or profile.get("research_interests")
        or profile.get("topics")
    ):

        normalized = _normalize(topic)

        if normalized:
            topic_weights[normalized] += 3.0

    # Authors the user follows.
    for author in _to_list(
        profile.get("followed_authors")
        or profile.get("following_authors")
    ):

        normalized = _normalize(author)

        if normalized:
            author_weights[normalized] += 3.0

    # Learn from previous user activity.
    for interaction in user_interactions or []:

        if not isinstance(interaction, dict):
            continue

        paper_id = str(
            interaction.get("paper_id") or ""
        ).strip()

        action = _normalize(
            interaction.get("action")
            or interaction.get("type")
        )

        weight = (
            POSITIVE_ACTIONS.get(action)
            or NEGATIVE_ACTIONS.get(action)
            or 0.0
        )

        if weight == 0:
            continue

        for topic in _to_list(
            interaction.get("topics")
        ):

            normalized = _normalize(topic)

            if normalized:
                topic_weights[normalized] += weight

        for author in _to_list(
            interaction.get("authors")
        ):

            normalized = _normalize(author)

            if normalized:
                author_weights[normalized] += weight

        if action in {"dislike", "dismiss", "hide"} and paper_id:
            excluded_ids.add(paper_id)

    # Keep only positive preferences.
    topic_weights = Counter({
        key: value
        for key, value in topic_weights.items()
        if value > 0
    })

    author_weights = Counter({
        key: value
        for key, value in author_weights.items()
        if value > 0
    })

    return {
        "topic_weights": topic_weights,
        "author_weights": author_weights,
        "excluded_ids": excluded_ids,
    }


def _calculate_popularity_score(
    paper: dict[str, Any],
) -> float:
    """Calculate a small normalized popularity signal."""

    try:
        citations = max(
            0,
            int(paper.get("citation_count") or 0),
        )

    except (ValueError, TypeError):
        citations = 0

    # Logarithmic scaling prevents highly cited papers
    # from dominating every recommendation.
    import math

    return min(
        1.0,
        math.log1p(citations) / math.log1p(1000),
    )


def _calculate_topic_score(
    paper_topics: list[str],
    topic_weights: Counter,
) -> tuple[float, list[str]]:
    """Calculate weighted topic relevance."""

    if not paper_topics or not topic_weights:
        return 0.0, []

    matched_topics = []

    score = 0.0
    maximum_possible = sum(
        topic_weights.values()
    )

    for paper_topic in paper_topics:

        for user_topic, weight in topic_weights.items():

            if (
                paper_topic == user_topic
                or paper_topic in user_topic
                or user_topic in paper_topic
            ):

                score += weight

                if user_topic not in matched_topics:
                    matched_topics.append(user_topic)

    if maximum_possible <= 0:
        return 0.0, matched_topics

    normalized_score = min(
        1.0,
        score / maximum_possible,
    )

    return normalized_score, matched_topics


def _calculate_author_score(
    paper_authors: list[str],
    author_weights: Counter,
) -> float:
    """Calculate relevance based on preferred authors."""

    if not paper_authors or not author_weights:
        return 0.0

    normalized_authors = {
        _normalize(author)
        for author in paper_authors
    }

    matched_weight = sum(
        weight
        for author, weight in author_weights.items()
        if author in normalized_authors
    )

    maximum_weight = sum(
        author_weights.values()
    )

    if maximum_weight <= 0:
        return 0.0

    return min(
        1.0,
        matched_weight / maximum_weight,
    )


def recommend_papers(
    papers: list[dict[str, Any]],
    user_profile: dict[str, Any] | None = None,
    user_interactions: list[dict[str, Any]] | None = None,
    limit: int = 10,
    exclude_paper_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Recommend research papers for a user.

    Args:
        papers:
            Available normalized research paper records.

        user_profile:
            Optional user profile, for example:
            {
                "interests": ["machine learning", "robotics"],
                "followed_authors": ["Author Name"]
            }

        user_interactions:
            Optional reading activity, for example:
            [
                {
                    "paper_id": "paper-123",
                    "action": "save",
                    "topics": ["machine learning"],
                    "authors": ["Author Name"]
                }
            ]

        limit:
            Maximum number of recommendations.

        exclude_paper_ids:
            Paper IDs that must not be recommended.

    Returns:
        JSON-serializable recommendation response.
    """

    if not 1 <= limit <= 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    if not isinstance(papers, list):
        raise TypeError(
            "papers must be a list."
        )

    preferences = _build_user_preferences(
        user_profile=user_profile,
        user_interactions=user_interactions,
    )

    topic_weights = preferences["topic_weights"]
    author_weights = preferences["author_weights"]

    excluded_ids = (
        preferences["excluded_ids"]
        | {
            str(value)
            for value in (exclude_paper_ids or [])
        }
    )

    recommendations = []

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        paper_id = _get_paper_identity(paper)

        if not paper_id or paper_id in excluded_ids:
            continue

        title = paper.get("title")

        if not title:
            continue

        topics = _paper_topics(paper)

        authors = _extract_author_names(
            paper.get("authors")
        )

        topic_score, matched_topics = (
            _calculate_topic_score(
                topics,
                topic_weights,
            )
        )

        author_score = _calculate_author_score(
            authors,
            author_weights,
        )

        popularity_score = _calculate_popularity_score(
            paper
        )

        # Main relevance comes from user interests.
        # Popularity is deliberately given a smaller weight.
        if topic_weights or author_weights:

            final_score = (
                topic_score * 0.70
                + author_score * 0.20
                + popularity_score * 0.10
            )

        else:
            # Cold-start recommendation:
            # use paper popularity when the user has
            # no available preference history.
            final_score = (
                popularity_score * 0.70
                + (0.30 if paper.get("abstract") else 0.0)
            )

        reasons = []

        if matched_topics:
            reasons.append(
                "Matches your research interests: "
                + ", ".join(matched_topics[:3])
            )

        if author_score > 0:
            reasons.append(
                "Written by an author you follow or prefer"
            )

        if popularity_score >= 0.5:
            reasons.append(
                "Has a strong citation record"
            )

        if not reasons:
            reasons.append(
                "Recommended from the available research collection"
            )

        recommendations.append({
            "paper_id": paper_id,
            "title": title,
            "abstract": paper.get("abstract"),
            "authors": authors,
            "publication_date": paper.get("publication_date"),
            "publication_year": paper.get("publication_year"),
            "doi": paper.get("doi"),
            "topics": topics,
            "citation_count": paper.get("citation_count", 0),
            "is_open_access": paper.get("is_open_access", False),
            "landing_page_url": paper.get("landing_page_url"),
            "pdf_url": paper.get("pdf_url"),
            "recommendation_score": round(
                final_score * 100,
                2,
            ),
            "recommendation_reasons": reasons,
        })

    recommendations.sort(
        key=lambda item: (
            item["recommendation_score"],
            item["citation_count"] or 0,
        ),
        reverse=True,
    )

    selected = recommendations[:limit]

    return {
        "success": True,
        "message": "Paper recommendations generated successfully.",
        "recommendation_type": "content_based",
        "total": len(recommendations),
        "limit": limit,
        "has_more": len(recommendations) > limit,
        "personalized": bool(
            topic_weights or author_weights
        ),
        "results": selected,
    }
