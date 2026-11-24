
"""
clean.py
--------
Cleans and standardizes research paper metadata.

Converts arXiv and OpenAlex records into a common schema
for search, recommendations, analytics and RAG.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

from datetime import datetime, timezone
from typing import Any


def clean_text(value: Any) -> str:
    """Normalize text and remove unnecessary whitespace."""

    if value is None:
        return ""

    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_doi(value: Any) -> str | None:
    """Normalize DOI identifiers."""

    if not value:
        return None

    doi = clean_text(value).lower()

    doi = re.sub(
        r"^https?://(dx\.)?doi\.org/",
        "",
        doi,
    )

    doi = doi.removeprefix("doi:")

    doi = doi.strip().rstrip(".,;")

    if not doi.startswith("10."):
        return None

    if "/" not in doi:
        return None

    return doi


def clean_authors(value: Any) -> list[dict[str, Any]]:
    """Convert author names or author objects into a common format."""

    if not isinstance(value, list):
        return []

    authors = []
    seen = set()

    for author in value:

        if isinstance(author, str):
            name = clean_text(author)

            author_data = {
                "name": name,
                "author_id": None,
                "orcid": None,
                "institutions": [],
            }

        elif isinstance(author, dict):
            name = clean_text(
                author.get("name")
                or author.get("display_name")
            )

            author_data = {
                "name": name,
                "author_id": author.get("author_id")
                or author.get("id"),
                "orcid": author.get("orcid"),
                "institutions": [
                    clean_text(institution)
                    for institution in author.get(
                        "institutions", []
                    )
                    if clean_text(institution)
                ],
            }

        else:
            continue

        if not name:
            continue

        normalized_name = name.casefold()

        if normalized_name in seen:
            continue

        seen.add(normalized_name)
        authors.append(author_data)

    return authors


def reconstruct_abstract(
    inverted_index: dict[str, list[int]] | None,
) -> str:
    """Reconstruct an OpenAlex abstract from its inverted index."""

    if not isinstance(inverted_index, dict):
        return ""

    positions: dict[int, str] = {}

    for word, indexes in inverted_index.items():

        if not isinstance(indexes, list):
            continue

        for index in indexes:

            if isinstance(index, int) and index >= 0:
                positions[index] = word

    if not positions:
        return ""

    return " ".join(
        positions[index]
        for index in sorted(positions)
    )


def generate_paper_id(
    doi: str | None,
    source: str,
    source_id: str | None,
    title: str,
) -> str:
    """Generate a deterministic identifier for a research paper."""

    if doi:
        identity = f"doi:{doi}"

    elif source == "arxiv" and source_id:
        arxiv_id = re.sub(r"v\d+$", "", source_id)
        identity = f"arxiv:{arxiv_id}"

    elif source_id:
        identity = f"{source}:{source_id}"

    else:
        normalized_title = clean_text(title).casefold()
        identity = f"title:{normalized_title}"

    digest = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()

    return f"paper_{digest[:24]}"


def normalize_paper(
    paper: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert one source record into the common paper schema.

    Supports both arXiv and OpenAlex records.
    """

    if not isinstance(paper, dict):
        raise TypeError("Paper record must be a dictionary.")

    source = clean_text(
        paper.get("source")
    ).lower()

    if source not in {"arxiv", "openalex"}:
        raise ValueError(
            f"Unsupported paper source: {source}"
        )

    title = clean_text(paper.get("title"))

    if not title:
        raise ValueError("Paper title is missing.")

    abstract = clean_text(
        paper.get("abstract")
    )

    if not abstract:
        abstract = reconstruct_abstract(
            paper.get("abstract_inverted_index")
        )

    doi = clean_doi(paper.get("doi"))

    source_id = clean_text(
        paper.get("source_id")
    ) or None

    authors = clean_authors(
        paper.get("authors")
    )

    if source == "arxiv":
        publication_date = paper.get("published")
        updated_date = paper.get("updated")

        categories = paper.get("categories", [])
        topics = []

    else:
        publication_date = paper.get("publication_date")
        updated_date = None

        categories = []
        topics = paper.get("topics", [])

        if not topics:
            topics = paper.get("concepts", [])

    try:
        parsed_date = (
            datetime.fromisoformat(
                publication_date.replace("Z", "+00:00")
            )
            if publication_date
            else None
        )

        if parsed_date and parsed_date.tzinfo is None:
            parsed_date = parsed_date.replace(
                tzinfo=timezone.utc
            )

    except (ValueError, AttributeError):
        parsed_date = None

    normalized_topics = sorted({
        clean_text(topic)
        for topic in topics + categories
        if clean_text(topic)
    })

    return {
        "paper_id": generate_paper_id(
            doi=doi,
            source=source,
            source_id=source_id,
            title=title,
        ),
        "source": source,
        "source_id": source_id,
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "authors": authors,
        "publication_date": (
            parsed_date.isoformat()
            if parsed_date
            else None
        ),
        "publication_year": (
            parsed_date.year
            if parsed_date
            else paper.get("publication_year")
        ),
        "updated_date": updated_date,
        "topics": normalized_topics,
        "journal": clean_text(
            paper.get("journal")
        ) or None,
        "paper_type": paper.get("type"),
        "language": paper.get("language"),
        "citation_count": max(
            0,
            int(paper.get("cited_by_count") or 0),
        ),
        "is_open_access": paper.get("is_open_access"),
        "landing_page_url": (
            paper.get("landing_page_url")
            or paper.get("entry_url")
        ),
        "pdf_url": paper.get("pdf_url"),
        "authors_count": len(authors),
        "raw_metadata": paper,
    }


def normalize_papers(
    papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize multiple paper records."""

    normalized = []

    for paper in papers:

        try:
            normalized.append(
                normalize_paper(paper)
            )

        except (ValueError, TypeError):
            # Invalid records are skipped rather than stopping
            # the entire ingestion batch.
            continue

    return normalized
