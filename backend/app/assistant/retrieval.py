
"""
Research Evidence Retrieval
---------------------------
Retrieves relevant research papers and extracts useful passages.

Supported modes:
    - keyword
    - semantic
    - hybrid

Used by:
    assistant/answer.py
"""

import re
from typing import Any

from ..search.keyword import keyword_search
from ..search.semantic import semantic_search


def _clean_text(value: Any) -> str:
    """Convert text into a normalized string."""
    if value is None:
        return ""

    if isinstance(value, list):
        return " ".join(_clean_text(item) for item in value)

    return re.sub(r"\s+", " ", str(value)).strip()


def _split_sentences(text: str) -> list[str]:
    """Split an abstract into readable sentences."""
    text = _clean_text(text)

    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)

    return [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) > 20
    ]


def _extract_relevant_passages(
    abstract: str,
    query: str,
    max_passages: int = 3,
) -> list[str]:
    """Extract sentences that are most relevant to the query."""

    sentences = _split_sentences(abstract)

    if not sentences:
        return []

    query_terms = {
        term.lower()
        for term in re.findall(r"\b[a-zA-Z0-9]+\b", query)
        if len(term) > 2
    }

    if not query_terms:
        return sentences[:max_passages]

    scored_sentences = []

    for index, sentence in enumerate(sentences):
        sentence_terms = {
            term.lower()
            for term in re.findall(
                r"\b[a-zA-Z0-9]+\b",
                sentence
            )
        }

        overlap = len(query_terms.intersection(sentence_terms))

        if overlap > 0:
            score = overlap / len(query_terms)

            scored_sentences.append({
                "sentence": sentence,
                "score": score,
                "position": index,
            })

    scored_sentences.sort(
        key=lambda item: (
            item["score"],
            -item["position"]
        ),
        reverse=True,
    )

    selected = scored_sentences[:max_passages]

    # Preserve the original abstract order.
    selected.sort(key=lambda item: item["position"])

    if selected:
        return [
            item["sentence"]
            for item in selected
        ]

    # If no exact keyword overlap exists, return the first sentences.
    return sentences[:max_passages]


def _build_source(paper: dict) -> dict:
    """Build frontend-friendly paper metadata."""

    authors = paper.get("authors", [])

    if not isinstance(authors, list):
        authors = []

    author_names = []

    for author in authors:
        if isinstance(author, dict):
            name = _clean_text(
                author.get("name")
                or author.get("display_name")
            )
        else:
            name = _clean_text(author)

        if name:
            author_names.append(name)

    return {
        "paper_id": _clean_text(paper.get("paper_id")),
        "title": _clean_text(paper.get("title")),
        "authors": author_names,
        "publication_year": (
            paper.get("publication_year")
            or paper.get("year")
        ),
        "doi": _clean_text(paper.get("doi")),
        "journal": _clean_text(paper.get("journal")),
        "landing_page_url": _clean_text(
            paper.get("landing_page_url")
        ),
        "pdf_url": _clean_text(paper.get("pdf_url")),
    }


def _merge_search_results(
    keyword_results: list[dict],
    semantic_results: list[dict],
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> list[dict]:
    """Combine keyword and semantic search results."""

    merged = {}

    for item in keyword_results:
        paper_id = _clean_text(item.get("paper_id"))

        if not paper_id:
            continue

        merged[paper_id] = {
            **item,
            "paper_id": paper_id,
            "keyword_score": float(
                item.get("relevance_score", 0.0)
                or 0.0
            ),
            "semantic_score": 0.0,
        }

    for item in semantic_results:
        paper_id = _clean_text(item.get("paper_id"))

        if not paper_id:
            continue

        semantic_score = float(
            item.get("similarity_score", 0.0)
            or 0.0
        )

        if paper_id in merged:
            merged[paper_id].update({
                key: value
                for key, value in item.items()
                if value is not None
            })
            merged[paper_id]["keyword_score"] = float(
                merged[paper_id].get("keyword_score", 0.0)
            )
            merged[paper_id]["semantic_score"] = semantic_score
        else:
            merged[paper_id] = {
                **item,
                "paper_id": paper_id,
                "keyword_score": 0.0,
                "semantic_score": semantic_score,
            }

    results = []

    for item in merged.values():
        keyword_score = item["keyword_score"]
        semantic_score = item["semantic_score"]

        # Normalize keyword score to a 0-1 range.
        normalized_keyword = (
            keyword_score / (1.0 + keyword_score)
            if keyword_score > 0
            else 0.0
        )

        item["retrieval_score"] = (
            keyword_weight * normalized_keyword
            + semantic_weight * semantic_score
        )

        results.append(item)

    results.sort(
        key=lambda item: item["retrieval_score"],
        reverse=True,
    )

    return results


def retrieve_evidence(
    papers: list[dict],
    query: str,
    limit: int = 5,
    mode: str = "hybrid",
    max_passages_per_paper: int = 3,
) -> dict:
    """
    Retrieve research papers and relevant evidence passages.

    Parameters:
        papers:
            Normalized research-paper records.

        query:
            User's research question.

        limit:
            Maximum number of papers to retrieve.

        mode:
            keyword, semantic, or hybrid.

        max_passages_per_paper:
            Maximum passages extracted from each paper.

    Returns:
        JSON-serializable retrieval result.
    """

    query = _clean_text(query)
    mode = _clean_text(mode).lower()

    if not query:
        return {
            "success": False,
            "message": "A search query is required.",
            "query": query,
            "mode": mode,
            "total": 0,
            "evidence_count": 0,
            "sources": [],
            "evidence": [],
        }

    if not isinstance(papers, list) or not papers:
        return {
            "success": True,
            "message": "No research papers are available.",
            "query": query,
            "mode": mode,
            "total": 0,
            "evidence_count": 0,
            "sources": [],
            "evidence": [],
        }

    if mode not in {"keyword", "semantic", "hybrid"}:
        return {
            "success": False,
            "message": "Mode must be keyword, semantic, or hybrid.",
            "query": query,
            "mode": mode,
            "total": 0,
            "evidence_count": 0,
            "sources": [],
            "evidence": [],
        }

    if limit < 1 or limit > 100:
        return {
            "success": False,
            "message": "limit must be between 1 and 100.",
            "query": query,
            "mode": mode,
            "total": 0,
            "evidence_count": 0,
            "sources": [],
            "evidence": [],
        }

    if max_passages_per_paper < 1:
        return {
            "success": False,
            "message": "max_passages_per_paper must be at least 1.",
            "query": query,
            "mode": mode,
            "total": 0,
            "evidence_count": 0,
            "sources": [],
            "evidence": [],
        }

    keyword_results = []
    semantic_results = []

    try:
        if mode in {"keyword", "hybrid"}:
            keyword_response = keyword_search(
                papers=papers,
                query=query,
                limit=limit,
                offset=0,
            )

            keyword_results = keyword_response.get(
                "results",
                []
            )

        if mode in {"semantic", "hybrid"}:
            semantic_response = semantic_search(
                papers=papers,
                query=query,
                limit=limit,
            )

            semantic_results = semantic_response.get(
                "results",
                []
            )

    except Exception as exc:
        return {
            "success": False,
            "message": "Search failed: " + str(exc),
            "query": query,
            "mode": mode,
            "total": 0,
            "evidence_count": 0,
            "sources": [],
            "evidence": [],
        }

    if mode == "keyword":
        selected_results = keyword_results

    elif mode == "semantic":
        selected_results = semantic_results

    else:
        selected_results = _merge_search_results(
            keyword_results=keyword_results,
            semantic_results=semantic_results,
        )

    # Match retrieved records with the original paper records.
    paper_map = {}

    for paper in papers:
        paper_id = _clean_text(paper.get("paper_id"))

        if paper_id:
            paper_map[paper_id] = paper

    selected_results = selected_results[:limit]

    sources = []
    evidence = []
    seen_sources = set()

    for result in selected_results:
        paper_id = _clean_text(result.get("paper_id"))

        paper = paper_map.get(paper_id)

        if not paper:
            paper = result

        abstract = _clean_text(paper.get("abstract"))

        if not abstract:
            continue

        source = _build_source(paper)

        source_key = (
            source["paper_id"]
            or source["title"]
        )

        if source_key and source_key not in seen_sources:
            seen_sources.add(source_key)
            sources.append(source)

        passages = _extract_relevant_passages(
            abstract=abstract,
            query=query,
            max_passages=max_passages_per_paper,
        )

        for passage in passages:
            evidence.append({
                "paper_id": source["paper_id"],
                "title": source["title"],
                "authors": source["authors"],
                "publication_year": source["publication_year"],
                "doi": source["doi"],
                "landing_page_url": source["landing_page_url"],
                "pdf_url": source["pdf_url"],
                "passage": passage,
                "retrieval_score": result.get(
                    "retrieval_score",
                    result.get(
                        "similarity_score",
                        result.get("relevance_score", 0.0)
                    )
                ),
            })

    return {
        "success": True,
        "message": (
            "Research evidence retrieved successfully."
            if evidence
            else "No relevant evidence passages were found."
        ),
        "query": query,
        "mode": mode,
        "total": len(selected_results),
        "evidence_count": len(evidence),
        "sources": sources,
        "evidence": evidence,
    }
