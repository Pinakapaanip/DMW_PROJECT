
"""
arxiv.py
--------
Fetches research paper metadata from the official arXiv API.

This module is independent of the project's database.
It returns raw records for the F4 ingestion pipeline.
"""

from __future__ import annotations

import time
import xml.etree.ElementTree as ET

from typing import Any
from urllib.parse import urlparse

import httpx


ARXIV_API_URL = "https://export.arxiv.org/api/query"

USER_AGENT = (
    "ChanakyaResearchCommons/1.0 "
    "(academic research paper ingestion)"
)

ATOM_NAMESPACE = "{http://www.w3.org/2005/Atom}"
ARXIV_NAMESPACE = "{http://arxiv.org/schemas/atom}"


def _get_text(element: ET.Element, tag: str) -> str | None:
    """Extract and clean text from an XML child element."""

    child = element.find(tag)

    if child is None or child.text is None:
        return None

    value = child.text.strip()
    return value or None


def _extract_arxiv_id(entry_id: str | None) -> str | None:
    """Extract the arXiv identifier from an entry URL."""

    if not entry_id:
        return None

    path = urlparse(entry_id).path.strip("/")

    if not path:
        return None

    return path.split("/")[-1]


def _parse_entry(entry: ET.Element) -> dict[str, Any]:
    """Convert one arXiv Atom entry into a raw Python dictionary."""

    authors = []

    for author in entry.findall(f"{ATOM_NAMESPACE}author"):
        name = _get_text(author, f"{ATOM_NAMESPACE}name")

        if name:
            authors.append(name)

    categories = [
        category.attrib.get("term")
        for category in entry.findall(f"{ATOM_NAMESPACE}category")
        if category.attrib.get("term")
    ]

    links = [
        {
            "href": link.attrib.get("href"),
            "rel": link.attrib.get("rel"),
            "type": link.attrib.get("type"),
        }
        for link in entry.findall(f"{ATOM_NAMESPACE}link")
        if link.attrib.get("href")
    ]

    entry_id = _get_text(entry, f"{ATOM_NAMESPACE}id")

    return {
        "source": "arxiv",
        "source_id": _extract_arxiv_id(entry_id),
        "entry_url": entry_id,
        "title": _get_text(entry, f"{ATOM_NAMESPACE}title"),
        "abstract": _get_text(entry, f"{ATOM_NAMESPACE}summary"),
        "authors": authors,
        "categories": categories,
        "published": _get_text(entry, f"{ATOM_NAMESPACE}published"),
        "updated": _get_text(entry, f"{ATOM_NAMESPACE}updated"),
        "doi": _get_text(entry, f"{ARXIV_NAMESPACE}doi"),
        "journal_reference": _get_text(
            entry, f"{ARXIV_NAMESPACE}journal_ref"
        ),
        "comments": _get_text(entry, f"{ARXIV_NAMESPACE}comment"),
        "links": links,
        "raw_xml": ET.tostring(entry, encoding="unicode"),
    }


def fetch_arxiv(
    query: str,
    max_results: int = 100,
    start: int = 0,
    page_size: int = 100,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    timeout: float = 30.0,
    retries: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch research papers from arXiv.

    Args:
        query: arXiv search expression.
        max_results: Maximum number of records to fetch.
        start: Starting result offset.
        page_size: Number of records requested per API call.
        sort_by: relevance, lastUpdatedDate or submittedDate.
        sort_order: ascending or descending.
        timeout: HTTP timeout in seconds.
        retries: Number of attempts for transient failures.

    Returns:
        A list of raw paper dictionaries.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if max_results < 1:
        raise ValueError("max_results must be at least 1.")

    if start < 0:
        raise ValueError("start cannot be negative.")

    if page_size < 1:
        raise ValueError("page_size must be at least 1.")

    allowed_sort_fields = {
        "relevance",
        "lastUpdatedDate",
        "submittedDate",
    }

    allowed_sort_orders = {"ascending", "descending"}

    if sort_by not in allowed_sort_fields:
        raise ValueError(f"Unsupported sort_by value: {sort_by}")

    if sort_order not in allowed_sort_orders:
        raise ValueError(f"Unsupported sort_order value: {sort_order}")

    papers: list[dict[str, Any]] = []

    headers = {"User-Agent": USER_AGENT}

    with httpx.Client(
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
    ) as client:

        current_start = start

        while len(papers) < max_results:

            current_page_size = min(
                page_size,
                max_results - len(papers),
            )

            params = {
                "search_query": query.strip(),
                "start": current_start,
                "max_results": current_page_size,
                "sortBy": sort_by,
                "sortOrder": sort_order,
            }

            response = None

            for attempt in range(retries + 1):
                try:
                    response = client.get(
                        ARXIV_API_URL,
                        params=params,
                    )
                    response.raise_for_status()
                    break

                except httpx.HTTPError:
                    if attempt == retries:
                        raise

                    time.sleep(min(2 ** attempt, 8))

            if response is None:
                raise RuntimeError("Could not retrieve arXiv response.")

            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as exc:
                raise ValueError(
                    "arXiv returned invalid XML."
                ) from exc

            entries = root.findall(f"{ATOM_NAMESPACE}entry")

            if not entries:
                break

            for entry in entries:
                paper = _parse_entry(entry)

                if paper["source_id"]:
                    papers.append(paper)

            current_start += len(entries)

            if len(entries) < current_page_size:
                break

            # Avoid sending requests too rapidly when multiple pages
            # are required.
            if len(papers) < max_results:
                time.sleep(3)

    return papers
