
"""
deduplication.py
----------------
Research paper duplicate detection and merging.

Uses:
- DOI matching
- arXiv identifier matching
- OpenAlex identifier matching
- Normalized title matching
- RapidFuzz for fuzzy title similarity

No database dependency.
"""

from __future__ import annotations

import re
import unicodedata

from collections import defaultdict
from typing import Any

from rapidfuzz import fuzz


def normalize_title(title: str | None) -> str:
    """Normalize a paper title for comparison."""

    if not title:
        return ""

    title = unicodedata.normalize("NFKC", title)
    title = title.casefold()

    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title)

    return title.strip()


def normalize_doi(doi: str | None) -> str | None:
    """Normalize DOI identifiers."""

    if not doi:
        return None

    doi = doi.strip().lower()

    doi = re.sub(
        r"^https?://(dx\.)?doi\.org/",
        "",
        doi,
    )

    doi = doi.removeprefix("doi:")

    return doi.strip().rstrip(".,;") or None


def normalize_arxiv_id(
    source_id: str | None,
) -> str | None:
    """Normalize arXiv identifiers and remove version suffixes."""

    if not source_id:
        return None

    value = source_id.strip()

    value = re.sub(
        r"^https?://arxiv\.org/(abs|pdf)/",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(
        r"\.pdf$",
        "",
        value,
        flags=re.IGNORECASE,
    )

    value = re.sub(r"v\d+$", "", value)

    return value.lower() or None


def _identity_keys(
    paper: dict[str, Any],
) -> set[str]:
    """Build reliable identifiers for a paper."""

    keys = set()

    doi = normalize_doi(paper.get("doi"))

    if doi:
        keys.add(f"doi:{doi}")

    source = paper.get("source", "").lower()
    source_id = paper.get("source_id")

    if source == "arxiv":
        arxiv_id = normalize_arxiv_id(source_id)

        if arxiv_id:
            keys.add(f"arxiv:{arxiv_id}")

    elif source_id:
        keys.add(f"{source}:{source_id.strip().lower()}")

    paper_id = paper.get("paper_id")

    if paper_id:
        keys.add(f"paper:{paper_id}")

    return keys


def _merge_records(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Merge duplicate records while preserving available metadata."""

    if not records:
        return {}

    # Prefer the record with the most complete metadata.
    primary = max(
        records,
        key=lambda record: sum(
            value not in (None, "", [], {})
            for value in record.values()
        ),
    ).copy()

    sources = set()
    identifiers = set()

    for record in records:

        if record.get("source"):
            sources.add(record["source"])

        for source in record.get("sources", []):
            sources.add(source)

        for key, value in record.items():

            if primary.get(key) in (None, "", [], {}):
                primary[key] = value

        for key in ("source_id", "doi", "paper_id"):

            if record.get(key):
                identifiers.add(
                    str(record[key])
                )

    primary["sources"] = sorted(sources)

    primary["source_identifiers"] = sorted(
        identifiers
    )

    return primary


def _group_by_identity(
    papers: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """Group papers using exact identifiers."""

    groups = []
    parent = list(range(len(papers)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]

        return index

    def union(first: int, second: int) -> None:
        root_first = find(first)
        root_second = find(second)

        if root_first != root_second:
            parent[root_second] = root_first

    identifier_owner = {}

    for index, paper in enumerate(papers):

        for key in _identity_keys(paper):

            if key in identifier_owner:
                union(index, identifier_owner[key])

            else:
                identifier_owner[key] = index

    grouped = defaultdict(list)

    for index, paper in enumerate(papers):
        grouped[find(index)].append(paper)

    groups.extend(grouped.values())

    return groups


def deduplicate_papers(
    papers: list[dict[str, Any]],
    similarity_threshold: int = 95,
) -> list[dict[str, Any]]:
    """
    Remove duplicate research papers.

    Exact identifiers are matched first.
    Remaining records are compared using title similarity.

    Similarity threshold ranges from 0 to 100.
    A high threshold is recommended to avoid merging
    unrelated research papers.
    """

    if not 0 <= similarity_threshold <= 100:
        raise ValueError(
            "similarity_threshold must be between 0 and 100."
        )

    valid_papers = [
        paper
        for paper in papers
        if isinstance(paper, dict)
        and paper.get("title")
    ]

    if not valid_papers:
        return []

    groups = _group_by_identity(
        valid_papers
    )

    merged = [
        _merge_records(group)
        for group in groups
    ]

    # Conservative fuzzy title matching.
    # Compare only records not already merged by identifiers.
    final_groups = []

    for paper in merged:

        title = normalize_title(
            paper.get("title")
        )

        matched = False

        for index, existing in enumerate(final_groups):

            existing_title = normalize_title(
                existing.get("title")
            )

            if not title or not existing_title:
                continue

            similarity = fuzz.ratio(
                title,
                existing_title,
            )

            if similarity >= similarity_threshold:

                final_groups[index] = _merge_records(
                    [existing, paper]
                )

                matched = True
                break

        if not matched:
            final_groups.append(paper)

    return final_groups
