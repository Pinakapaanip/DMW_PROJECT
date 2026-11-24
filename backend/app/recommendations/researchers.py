
"""
researchers.py
--------------
Researcher recommendation engine.

Builds researcher profiles from research paper records
and recommends researchers based on topic similarity,
publication activity and citation impact.

No paid APIs, GPU or external services required.
"""

from __future__ import annotations

import math
import re

from collections import Counter, defaultdict
from typing import Any


def _normalize(value: Any) -> str:
    """Normalize text for matching."""

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


def _extract_authors(
    paper: dict[str, Any],
) -> list[dict[str, str]]:
    """Extract researcher names and identifiers."""

    authors = []

    for author in _to_list(paper.get("authors")):

        if isinstance(author, str):

            name = author.strip()

            if name:
                authors.append({
                    "name": name,
                    "author_id": "",
                    "institution": "",
                })

        elif isinstance(author, dict):

            name = (
                author.get("name")
                or author.get("display_name")
                or ""
            )

            if not str(name).strip():
                continue

            authors.append({
                "name": str(name).strip(),
                "author_id": str(
                    author.get("author_id")
                    or author.get("id")
                    or ""
                ).strip(),
                "institution": str(
                    author.get("institution")
                    or author.get("institution_name")
                    or ""
                ).strip(),
            })

    return authors


def _extract_topics(
    paper: dict[str, Any],
) -> list[str]:
    """Extract topics from a paper."""

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


def _build_researcher_profiles(
    papers: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Build researcher profiles from paper records."""

    profiles = {}

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        paper_id = str(
            paper.get("paper_id")
            or paper.get("doi")
            or paper.get("title")
            or ""
        )

        topics = _extract_topics(paper)

        authors = _extract_authors(paper)

        try:
            citations = max(
                0,
                int(paper.get("citation_count") or 0),
            )
        except (ValueError, TypeError):
            citations = 0

        publication_year = paper.get(
            "publication_year"
        )

        try:
            publication_year = int(publication_year)
        except (ValueError, TypeError):
            publication_year = None

        for author in authors:

            name = author["name"]
            author_id = author["author_id"]

            identity = (
                f"id:{author_id}"
                if author_id
                else f"name:{_normalize(name)}"
            )

            if identity not in profiles:

                profiles[identity] = {
                    "researcher_id": author_id or None,
                    "name": name,
                    "institutions": set(),
                    "topics": Counter(),
                    "paper_ids": set(),
                    "publication_count": 0,
                    "citation_count": 0,
                    "latest_publication_year": None,
                    "sample_papers": [],
                }

            profile = profiles[identity]

            if author["institution"]:
                profile["institutions"].add(
                    author["institution"]
                )

            profile["topics"].update(topics)

            if paper_id and paper_id not in profile["paper_ids"]:

                profile["paper_ids"].add(paper_id)

                profile["publication_count"] += 1

                profile["citation_count"] += citations

                if len(profile["sample_papers"]) < 5:
                    profile["sample_papers"].append({
                        "paper_id": paper.get("paper_id"),
                        "title": paper.get("title"),
                        "publication_year": publication_year,
                    })

            if publication_year is not None:

                current_latest = profile[
                    "latest_publication_year"
                ]

                if (
                    current_latest is None
                    or publication_year > current_latest
                ):
                    profile[
                        "latest_publication_year"
                    ] = publication_year

    return profiles


def _normalize_profile(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Convert internal researcher profile to JSON-safe output."""

    return {
        "researcher_id": profile["researcher_id"],
        "name": profile["name"],
        "institutions": sorted(
            profile["institutions"]
        ),
        "topics": [
            topic
            for topic, _ in profile["topics"].most_common(15)
        ],
        "publication_count": profile["publication_count"],
        "citation_count": profile["citation_count"],
        "latest_publication_year": profile[
            "latest_publication_year"
        ],
        "sample_papers": profile["sample_papers"],
    }


def _topic_similarity(
    researcher_topics: Counter,
    user_topics: Counter,
) -> float:
    """Calculate weighted topic overlap."""

    if not researcher_topics or not user_topics:
        return 0.0

    researcher_set = set(researcher_topics)
    user_set = set(user_topics)

    common = researcher_set & user_set

    if not common:
        return 0.0

    weighted_overlap = sum(
        user_topics[topic]
        for topic in common
    )

    maximum = sum(
        user_topics.values()
    )

    if maximum <= 0:
        return 0.0

    return min(
        1.0,
        weighted_overlap / maximum,
    )


def recommend_researchers(
    papers: list[dict[str, Any]],
    user_profile: dict[str, Any] | None = None,
    followed_researchers: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Recommend researchers based on research interests.

    Args:
        papers:
            Normalized research paper records.

        user_profile:
            Example:
            {
                "interests": [
                    "machine learning",
                    "computer vision"
                ],
                "followed_authors": [
                    "Researcher Name"
                ]
            }

        followed_researchers:
            Researcher IDs or names already followed.

        limit:
            Maximum recommendations.

    Returns:
        JSON-serializable researcher recommendation response.
    """

    if not isinstance(papers, list):
        raise TypeError(
            "papers must be a list."
        )

    if not 1 <= limit <= 100:
        raise ValueError(
            "limit must be between 1 and 100."
        )

    profile = user_profile or {}

    user_topics = Counter()

    for topic in _to_list(
        profile.get("interests")
        or profile.get("research_interests")
        or profile.get("topics")
    ):

        normalized = _normalize(topic)

        if normalized:
            user_topics[normalized] += 3.0

    for paper in _to_list(
        profile.get("previously_read_topics")
    ):

        normalized = _normalize(paper)

        if normalized:
            user_topics[normalized] += 1.0

    followed = {
        _normalize(value)
        for value in (
            followed_researchers
            or profile.get("followed_authors")
            or []
        )
        if _normalize(value)
    }

    profiles = _build_researcher_profiles(
        papers
    )

    recommendations = []

    for identity, researcher in profiles.items():

        researcher_id = researcher["researcher_id"]

        normalized_name = _normalize(
            researcher["name"]
        )

        if (
            normalized_name in followed
            or _normalize(researcher_id) in followed
        ):
            continue

        topic_score = _topic_similarity(
            researcher["topics"],
            user_topics,
        )

        publication_count = researcher[
            "publication_count"
        ]

        citation_count = researcher[
            "citation_count"
        ]

        activity_score = min(
            1.0,
            math.log1p(publication_count)
            / math.log1p(50),
        )

        impact_score = min(
            1.0,
            math.log1p(citation_count)
            / math.log1p(1000),
        )

        if user_topics:

            final_score = (
                topic_score * 0.70
                + activity_score * 0.20
                + impact_score * 0.10
            )

        else:

            # Cold-start discovery.
            final_score = (
                activity_score * 0.65
                + impact_score * 0.35
            )

        reasons = []

        if topic_score > 0:
            reasons.append(
                "Researches topics related to your interests"
            )

        if publication_count >= 5:
            reasons.append(
                "Has multiple publications in the collection"
            )

        if impact_score >= 0.5:
            reasons.append(
                "Has a strong citation record"
            )

        if not reasons:
            reasons.append(
                "Discovered through the research collection"
            )

        researcher_data = _normalize_profile(
            researcher
        )

        recommendations.append({
            **researcher_data,
            "recommendation_score": round(
                final_score * 100,
                2,
            ),
            "recommendation_reasons": reasons,
        })

    recommendations.sort(
        key=lambda item: (
            item["recommendation_score"],
            item["citation_count"],
        ),
        reverse=True,
    )

    selected = recommendations[:limit]

    return {
        "success": True,
        "message": "Researcher recommendations generated successfully.",
        "recommendation_type": "researcher_discovery",
        "total": len(recommendations),
        "limit": limit,
        "has_more": len(recommendations) > limit,
        "personalized": bool(user_topics),
        "results": selected,
    }
