
"""
semantic.py
-----------
Semantic research paper search using sentence embeddings.

Uses sentence-transformers with a CPU-friendly model.
Supports embedding generation, similarity ranking,
pagination and frontend-friendly JSON responses.

Model:
sentence-transformers/all-MiniLM-L6-v2
"""

from __future__ import annotations

import logging

from typing import Any

import numpy as np


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = None
_model_name = None

# In-memory embedding cache.
# Suitable for development and moderate local datasets.
_embedding_cache: dict[str, np.ndarray] = {}


def get_embedding_model(
    model_name: str = DEFAULT_MODEL,
):
    """Load the embedding model once and reuse it."""

    global _model, _model_name

    if _model is None or _model_name != model_name:

        try:
            from sentence_transformers import SentenceTransformer

        except ImportError as exc:
            raise RuntimeError(
                "Semantic search requires sentence-transformers. "
                "Install it using: "
                "python -m pip install sentence-transformers"
            ) from exc

        logger.info(
            "Loading semantic embedding model: %s",
            model_name,
        )

        _model = SentenceTransformer(
            model_name,
            device="cpu",
        )

        _model_name = model_name
        _embedding_cache.clear()

    return _model


def build_paper_text(
    paper: dict[str, Any],
) -> str:
    """Combine important paper fields into searchable text."""

    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""

    topics = paper.get("topics") or []

    if not isinstance(topics, list):
        topics = []

    authors = paper.get("authors") or []

    author_names = []

    for author in authors:

        if isinstance(author, str):
            author_names.append(author)

        elif isinstance(author, dict):
            name = author.get("name")

            if name:
                author_names.append(name)

    return (
        f"Title: {title}. "
        f"Abstract: {abstract}. "
        f"Topics: {' '.join(topics)}. "
        f"Authors: {' '.join(author_names)}."
    ).strip()


def generate_embeddings(
    texts: list[str],
    model_name: str = DEFAULT_MODEL,
    batch_size: int = 32,
) -> np.ndarray:
    """Generate normalized embeddings for a list of texts."""

    if not texts:
        return np.empty((0, 0), dtype=np.float32)

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")

    model = get_embedding_model(model_name)

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return np.asarray(
        embeddings,
        dtype=np.float32,
    )


def get_paper_embeddings(
    papers: list[dict[str, Any]],
    model_name: str = DEFAULT_MODEL,
) -> np.ndarray:
    """Generate or retrieve cached paper embeddings."""

    texts = []
    missing_indices = []
    paper_keys = []

    for index, paper in enumerate(papers):

        paper_id = str(
            paper.get("paper_id")
            or f"paper-index-{index}"
        )

        text = build_paper_text(paper)

        cache_key = f"{model_name}:{paper_id}"

        paper_keys.append(cache_key)

        if cache_key in _embedding_cache:
            texts.append(None)

        else:
            texts.append(text)
            missing_indices.append(index)

    if missing_indices:

        missing_texts = [
            texts[index]
            for index in missing_indices
        ]

        new_embeddings = generate_embeddings(
            missing_texts,
            model_name=model_name,
        )

        for index, embedding in zip(
            missing_indices,
            new_embeddings,
        ):

            _embedding_cache[
                paper_keys[index]
            ] = embedding

    if not papers:
        return np.empty((0, 0), dtype=np.float32)

    return np.stack([
        _embedding_cache[key]
        for key in paper_keys
    ])


def semantic_search(
    papers: list[dict[str, Any]],
    query: str,
    limit: int = 20,
    offset: int = 0,
    model_name: str = DEFAULT_MODEL,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """
    Search research papers by semantic meaning.

    Args:
        papers: Normalized research paper records.
        query: Natural language search query.
        limit: Maximum results to return.
        offset: Pagination offset.
        model_name: Sentence-transformer model.
        min_score: Minimum cosine similarity threshold.

    Returns:
        JSON-serializable ranked search response.
    """

    if not query or not query.strip():
        return {
            "success": False,
            "message": "Search query cannot be empty.",
            "query": query,
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

    if not -1.0 <= min_score <= 1.0:
        raise ValueError(
            "min_score must be between -1 and 1."
        )

    valid_papers = [
        paper
        for paper in papers
        if isinstance(paper, dict)
        and paper.get("title")
    ]

    if not valid_papers:
        return {
            "success": True,
            "message": "No research papers available.",
            "query": query,
            "total": 0,
            "limit": limit,
            "offset": offset,
            "has_more": False,
            "results": [],
        }

    query_embedding = generate_embeddings(
        [query.strip()],
        model_name=model_name,
    )[0]

    paper_embeddings = get_paper_embeddings(
        valid_papers,
        model_name=model_name,
    )

    # Embeddings are normalized, so dot product equals cosine similarity.
    similarities = np.dot(
        paper_embeddings,
        query_embedding,
    )

    ranked_indices = np.argsort(
        similarities
    )[::-1]

    ranked_results = []

    for index in ranked_indices:

        score = float(similarities[index])

        if score < min_score:
            continue

        paper = valid_papers[index]

        authors = paper.get("authors") or []

        author_names = [
            author
            if isinstance(author, str)
            else author.get("name")
            for author in authors
            if isinstance(author, (str, dict))
        ]

        ranked_results.append({
            "paper_id": paper.get("paper_id"),
            "title": paper.get("title"),
            "abstract": paper.get("abstract"),
            "authors": [
                name for name in author_names if name
            ],
            "publication_date": paper.get("publication_date"),
            "publication_year": paper.get("publication_year"),
            "doi": paper.get("doi"),
            "topics": paper.get("topics", []),
            "citation_count": paper.get("citation_count", 0),
            "landing_page_url": paper.get("landing_page_url"),
            "pdf_url": paper.get("pdf_url"),
            "similarity_score": round(score, 5),
        })

    total = len(ranked_results)

    results = ranked_results[
        offset:offset + limit
    ]

    return {
        "success": True,
        "message": "Semantic search completed successfully.",
        "query": query,
        "model": model_name,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + len(results) < total,
        "results": results,
    }


def clear_embedding_cache() -> None:
    """Clear in-memory paper embeddings."""

    _embedding_cache.clear()
