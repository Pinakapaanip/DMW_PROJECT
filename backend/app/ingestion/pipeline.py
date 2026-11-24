
"""
pipeline.py
-----------
Main F4 research paper ingestion pipeline.

Workflow:
1. Fetch papers from arXiv and/or OpenAlex.
2. Preserve original source records.
3. Normalize metadata into a common schema.
4. Deduplicate records.
5. Save raw and normalized JSONL files.
6. Export normalized records to Parquet.
7. Update ingestion run metadata.

Database-independent by design.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .fetch import fetch_papers, flatten_papers
from .clean import normalize_papers


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATA_DIR = (
    PROJECT_ROOT / "data" / "ingestion"
)


def _utc_now() -> str:
    """Return current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def _safe_query_name(query: str) -> str:
    """Create a filesystem-safe query identifier."""

    name = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        query.strip().lower(),
    )

    return name.strip("_")[:60] or "research"


def _write_json_atomic(
    path: Path,
    data: Any,
) -> None:
    """Write JSON safely using an atomic file replacement."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_suffix(
        path.suffix + ".tmp"
    )

    with temporary_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    os.replace(temporary_path, path)


def _write_jsonl(
    path: Path,
    records: list[dict[str, Any]],
) -> None:
    """Write records as JSON Lines."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for record in records:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )


def _deduplicate(
    papers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Deduplicate papers using stable paper IDs.

    When two sources provide the same paper, retain
    the record with more complete metadata and merge
    missing fields from the other record.
    """

    unique: dict[str, dict[str, Any]] = {}

    for paper in papers:

        paper_id = paper.get("paper_id")

        if not paper_id:
            continue

        existing = unique.get(paper_id)

        if existing is None:
            unique[paper_id] = paper.copy()
            continue

        existing_score = sum(
            value not in (None, "", [], {})
            for value in existing.values()
        )

        new_score = sum(
            value not in (None, "", [], {})
            for value in paper.values()
        )

        if new_score > existing_score:
            primary = paper.copy()
            secondary = existing
        else:
            primary = existing.copy()
            secondary = paper

        # Merge source identifiers and metadata without
        # discarding the preferred record.
        for key, value in secondary.items():

            if primary.get(key) in (None, "", [], {}):
                primary[key] = value

        sources = set(
            primary.get("sources", [])
        )

        sources.update(
            secondary.get("sources", [])
        )

        sources.add(primary.get("source"))
        sources.add(secondary.get("source"))

        primary["sources"] = sorted(
            source
            for source in sources
            if source
        )

        unique[paper_id] = primary

    return list(unique.values())


def _export_parquet(
    records: list[dict[str, Any]],
    path: Path,
) -> str | None:
    """
    Export normalized records to Parquet.

    Nested metadata fields are serialized to JSON strings
    to keep the output compatible with common data tools.
    """

    if not records:
        return None

    try:
        import pandas as pd

    except ImportError as exc:
        raise RuntimeError(
            "Parquet export requires pandas and pyarrow. "
            "Install them using: "
            "python -m pip install pandas pyarrow"
        ) from exc

    export_records = []

    for record in records:

        row = record.copy()

        for field in (
            "authors",
            "topics",
            "raw_metadata",
            "sources",
        ):

            if field in row:
                row[field] = json.dumps(
                    row[field],
                    ensure_ascii=False,
                    default=str,
                )

        export_records.append(row)

    dataframe = pd.DataFrame(export_records)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        path.stem + ".tmp" + path.suffix
    )

    try:
        dataframe.to_parquet(
            temporary_path,
            engine="pyarrow",
            index=False,
        )

        os.replace(
            temporary_path,
            path,
        )

    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return str(path)


def run_ingestion(
    query: str,
    source: str = "all",
    limit: int = 100,
    page_size: int = 100,
    mailto: str | None = None,
    data_dir: str | Path | None = None,
    export_parquet: bool = True,
) -> dict[str, Any]:
    """
    Execute the complete research paper ingestion pipeline.

    Args:
        query: Research topic to search.
        source: arxiv, openalex or all.
        limit: Maximum number of papers per source.
        page_size: Number of papers per API request.
        mailto: Optional OpenAlex contact email.
        data_dir: Optional custom data directory.
        export_parquet: Whether to export Parquet.

    Returns:
        Summary containing counts, paths and run details.
    """

    if not query or not query.strip():
        raise ValueError("Research query cannot be empty.")

    if limit < 1:
        raise ValueError("limit must be at least 1.")

    started_at = _utc_now()

    run_id = uuid4().hex

    base_dir = Path(
        data_dir
        if data_dir is not None
        else DEFAULT_DATA_DIR
    ).resolve()

    query_name = _safe_query_name(query)

    run_dir = (
        base_dir
        / "runs"
        / f"{datetime.now(timezone.utc):%Y%m%d}"
        / run_id
    )

    raw_dir = run_dir / "raw"
    normalized_dir = run_dir / "normalized"

    logger.info(
        "Starting ingestion run %s for query: %s",
        run_id,
        query,
    )

    # 1. Collect source records.
    collected = fetch_papers(
        query=query,
        source=source,
        limit=limit,
        page_size=page_size,
        mailto=mailto,
    )

    all_raw_records = flatten_papers(collected)

    # 2. Preserve original source records.
    for source_name, records in collected.items():

        if records:
            _write_jsonl(
                raw_dir / f"{source_name}.jsonl",
                records,
            )

    # 3. Normalize metadata.
    normalized = normalize_papers(
        all_raw_records
    )

    # 4. Deduplicate normalized records.
    unique_papers = _deduplicate(
        normalized
    )

    # 5. Save normalized records.
    normalized_path = (
        normalized_dir / f"{query_name}.jsonl"
    )

    _write_jsonl(
        normalized_path,
        unique_papers,
    )

    # 6. Export Parquet.
    parquet_path = None

    if export_parquet and unique_papers:

        parquet_path = _export_parquet(
            unique_papers,
            base_dir
            / "parquet"
            / f"{query_name}.parquet",
        )

    finished_at = _utc_now()

    # 7. Build run metadata.
    summary = {
        "run_id": run_id,
        "query": query,
        "source": source,
        "status": "completed",
        "started_at": started_at,
        "finished_at": finished_at,
        "records_fetched": {
            source_name: len(records)
            for source_name, records in collected.items()
        },
        "total_fetched": len(all_raw_records),
        "total_normalized": len(normalized),
        "total_unique": len(unique_papers),
        "duplicates_removed": (
            len(normalized) - len(unique_papers)
        ),
        "raw_directory": str(raw_dir),
        "normalized_file": str(normalized_path),
        "parquet_file": parquet_path,
    }

    # 8. Save run summary.
    _write_json_atomic(
        run_dir / "summary.json",
        summary,
    )

    # 9. Update latest-run checkpoint.
    checkpoint = {
        "last_successful_run": finished_at,
        "last_run_id": run_id,
        "last_query": query,
        "last_source": source,
        "last_total_unique": len(unique_papers),
        "last_summary_file": str(
            run_dir / "summary.json"
        ),
    }

    _write_json_atomic(
        base_dir / "checkpoint.json",
        checkpoint,
    )

    logger.info(
        "Ingestion completed. Unique papers: %s",
        len(unique_papers),
    )

    return summary
