
"""
Research Analytics Warehouse
-----------------------------
Local analytics storage using DuckDB and Parquet.

Responsibilities:
    - Load normalized research paper records.
    - Maintain a local analytical database.
    - Execute research analytics queries.
    - Provide JSON-serializable results.

Default database:
    data/analytics/research_warehouse.duckdb
"""

import json
import os
from pathlib import Path
from typing import Any, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "analytics"

DEFAULT_DATABASE = DEFAULT_DATA_DIR / "research_warehouse.duckdb"


def _get_duckdb():
    """Import DuckDB lazily so other backend modules can load without it."""
    try:
        import duckdb
        return duckdb
    except ImportError as exc:
        raise RuntimeError(
            "DuckDB is not installed. Install it using: "
            "pip install duckdb"
        ) from exc


def _safe_string(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return default


def _normalize_paper(paper: dict) -> dict:
    """Convert a normalized research paper into warehouse format."""

    authors = paper.get("authors", [])
    topics = paper.get("topics", [])

    if not isinstance(authors, list):
        authors = []

    if not isinstance(topics, list):
        topics = []

    normalized_authors = []

    for author in authors:
        if isinstance(author, dict):
            name = (
                author.get("name")
                or author.get("display_name")
                or ""
            )
            normalized_authors.append(str(name).strip())
        elif author:
            normalized_authors.append(str(author).strip())

    normalized_topics = []

    for topic in topics:
        if isinstance(topic, dict):
            name = (
                topic.get("name")
                or topic.get("display_name")
                or ""
            )
            if name:
                normalized_topics.append(str(name).strip())
        elif topic:
            normalized_topics.append(str(topic).strip())

    year = paper.get("publication_year")

    if year is None:
        year = paper.get("year")

    try:
        year = int(year) if year else None
    except (ValueError, TypeError):
        year = None

    return {
        "paper_id": _safe_string(paper.get("paper_id")),
        "title": _safe_string(paper.get("title")),
        "abstract": _safe_string(paper.get("abstract")),
        "publication_year": year,
        "publication_date": _safe_string(
            paper.get("publication_date")
        ),
        "source": _safe_string(paper.get("source")),
        "doi": _safe_string(paper.get("doi")),
        "journal": _safe_string(paper.get("journal")),
        "paper_type": _safe_string(paper.get("paper_type")),
        "language": _safe_string(paper.get("language")),
        "citation_count": _safe_int(
            paper.get("citation_count")
        ),
        "is_open_access": bool(
            paper.get("is_open_access", False)
        ),
        "authors_json": json.dumps(
            normalized_authors,
            ensure_ascii=False
        ),
        "topics_json": json.dumps(
            normalized_topics,
            ensure_ascii=False
        ),
        "landing_page_url": _safe_string(
            paper.get("landing_page_url")
        ),
    }


def _connect(database_path: Optional[str] = None):
    """Open the local DuckDB database and initialize its schema."""

    duckdb = _get_duckdb()

    path = Path(database_path) if database_path else DEFAULT_DATABASE

    path.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(path))

    connection.execute("""
        CREATE TABLE IF NOT EXISTS research_papers (
            paper_id VARCHAR PRIMARY KEY,
            title VARCHAR,
            abstract VARCHAR,
            publication_year INTEGER,
            publication_date VARCHAR,
            source VARCHAR,
            doi VARCHAR,
            journal VARCHAR,
            paper_type VARCHAR,
            language VARCHAR,
            citation_count BIGINT DEFAULT 0,
            is_open_access BOOLEAN DEFAULT FALSE,
            authors_json VARCHAR,
            topics_json VARCHAR,
            landing_page_url VARCHAR,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_papers_year
        ON research_papers(publication_year)
    """)

    connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_papers_source
        ON research_papers(source)
    """)

    return connection


def initialize_warehouse(
    database_path: Optional[str] = None,
) -> dict:
    """Initialize the research analytics warehouse."""

    try:
        connection = _connect(database_path)
        connection.close()

        return {
            "success": True,
            "message": "Analytics warehouse initialized.",
            "database": str(
                Path(database_path)
                if database_path
                else DEFAULT_DATABASE
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "database": None,
        }


def load_papers(
    papers: list[dict],
    database_path: Optional[str] = None,
) -> dict:
    """
    Insert or update research papers in the warehouse.

    Existing paper IDs are updated instead of duplicated.
    """

    if not isinstance(papers, list):
        return {
            "success": False,
            "message": "papers must be a list.",
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
        }

    inserted = 0
    updated = 0
    skipped = 0

    connection = None

    try:
        connection = _connect(database_path)

        for paper in papers:
            if not isinstance(paper, dict):
                skipped += 1
                continue

            record = _normalize_paper(paper)

            if not record["paper_id"]:
                skipped += 1
                continue

            exists = connection.execute(
                """
                SELECT COUNT(*)
                FROM research_papers
                WHERE paper_id = ?
                """,
                [record["paper_id"]],
            ).fetchone()[0]

            connection.execute(
                """
                INSERT INTO research_papers (
                    paper_id,
                    title,
                    abstract,
                    publication_year,
                    publication_date,
                    source,
                    doi,
                    journal,
                    paper_type,
                    language,
                    citation_count,
                    is_open_access,
                    authors_json,
                    topics_json,
                    landing_page_url,
                    updated_at
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
                )
                ON CONFLICT (paper_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    abstract = EXCLUDED.abstract,
                    publication_year = EXCLUDED.publication_year,
                    publication_date = EXCLUDED.publication_date,
                    source = EXCLUDED.source,
                    doi = EXCLUDED.doi,
                    journal = EXCLUDED.journal,
                    paper_type = EXCLUDED.paper_type,
                    language = EXCLUDED.language,
                    citation_count = EXCLUDED.citation_count,
                    is_open_access = EXCLUDED.is_open_access,
                    authors_json = EXCLUDED.authors_json,
                    topics_json = EXCLUDED.topics_json,
                    landing_page_url = EXCLUDED.landing_page_url,
                    updated_at = CURRENT_TIMESTAMP
                """,
                [
                    record["paper_id"],
                    record["title"],
                    record["abstract"],
                    record["publication_year"],
                    record["publication_date"],
                    record["source"],
                    record["doi"],
                    record["journal"],
                    record["paper_type"],
                    record["language"],
                    record["citation_count"],
                    record["is_open_access"],
                    record["authors_json"],
                    record["topics_json"],
                    record["landing_page_url"],
                ],
            )

            if exists:
                updated += 1
            else:
                inserted += 1

        return {
            "success": True,
            "message": "Research papers loaded into warehouse.",
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
            "total_processed": len(papers),
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "inserted": inserted,
            "updated": updated,
            "skipped": skipped,
        }

    finally:
        if connection is not None:
            connection.close()


def load_parquet(
    parquet_path: str,
    database_path: Optional[str] = None,
) -> dict:
    """Load normalized paper data from a Parquet file."""

    path = Path(parquet_path)

    if not path.exists() or not path.is_file():
        return {
            "success": False,
            "message": "Parquet file does not exist.",
            "inserted": 0,
            "updated": 0,
        }

    connection = None

    try:
        connection = _connect(database_path)

        # Read the Parquet file using DuckDB.
        # The file path is escaped to avoid SQL string issues.
        safe_path = str(path.resolve()).replace("'", "''")

        rows = connection.execute(
            f"SELECT * FROM read_parquet('{safe_path}')"
        ).fetchdf()

        papers = rows.to_dict(orient="records")

        # Convert JSON-serialized nested columns if available.
        for paper in papers:
            for field in ("authors", "topics"):
                value = paper.get(field)

                if isinstance(value, str):
                    try:
                        paper[field] = json.loads(value)
                    except json.JSONDecodeError:
                        paper[field] = []

                if paper.get(field) is None:
                    paper[field] = []

        return load_papers(
            papers=papers,
            database_path=database_path,
        )

    except Exception as exc:
        return {
            "success": False,
            "message": "Parquet loading failed: " + str(exc),
            "inserted": 0,
            "updated": 0,
        }

    finally:
        if connection is not None:
            connection.close()


def get_warehouse_summary(
    database_path: Optional[str] = None,
) -> dict:
    """Get high-level research warehouse statistics."""

    connection = None

    try:
        connection = _connect(database_path)

        total_papers = connection.execute(
            "SELECT COUNT(*) FROM research_papers"
        ).fetchone()[0]

        total_citations = connection.execute(
            """
            SELECT COALESCE(SUM(citation_count), 0)
            FROM research_papers
            """
        ).fetchone()[0]

        total_open_access = connection.execute(
            """
            SELECT COUNT(*)
            FROM research_papers
            WHERE is_open_access = TRUE
            """
        ).fetchone()[0]

        total_sources = connection.execute(
            """
            SELECT COUNT(DISTINCT source)
            FROM research_papers
            WHERE source != ''
            """
        ).fetchone()[0]

        year_range = connection.execute(
            """
            SELECT
                MIN(publication_year),
                MAX(publication_year)
            FROM research_papers
            """
        ).fetchone()

        return {
            "success": True,
            "total_papers": total_papers,
            "total_citations": total_citations,
            "open_access_papers": total_open_access,
            "source_count": total_sources,
            "first_publication_year": year_range[0],
            "latest_publication_year": year_range[1],
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
        }

    finally:
        if connection is not None:
            connection.close()


def get_publication_statistics(
    database_path: Optional[str] = None,
) -> dict:
    """Get the number of papers published each year."""

    connection = None

    try:
        connection = _connect(database_path)

        rows = connection.execute(
            """
            SELECT
                publication_year,
                COUNT(*) AS publication_count
            FROM research_papers
            WHERE publication_year IS NOT NULL
            GROUP BY publication_year
            ORDER BY publication_year
            """
        ).fetchall()

        return {
            "success": True,
            "data": [
                {
                    "year": row[0],
                    "publication_count": row[1],
                }
                for row in rows
            ],
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "data": [],
        }

    finally:
        if connection is not None:
            connection.close()


def get_top_cited_papers(
    limit: int = 10,
    database_path: Optional[str] = None,
) -> dict:
    """Return the most cited research papers."""

    connection = None

    try:
        if limit < 1 or limit > 100:
            raise ValueError("limit must be between 1 and 100.")

        connection = _connect(database_path)

        rows = connection.execute(
            """
            SELECT
                paper_id,
                title,
                citation_count,
                publication_year,
                doi,
                landing_page_url
            FROM research_papers
            ORDER BY citation_count DESC, title ASC
            LIMIT ?
            """,
            [limit],
        ).fetchall()

        return {
            "success": True,
            "results": [
                {
                    "paper_id": row[0],
                    "title": row[1],
                    "citation_count": row[2],
                    "publication_year": row[3],
                    "doi": row[4],
                    "landing_page_url": row[5],
                }
                for row in rows
            ],
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "results": [],
        }

    finally:
        if connection is not None:
            connection.close()


def get_source_statistics(
    database_path: Optional[str] = None,
) -> dict:
    """Compare the number of papers from each research source."""

    connection = None

    try:
        connection = _connect(database_path)

        rows = connection.execute(
            """
            SELECT
                source,
                COUNT(*) AS paper_count
            FROM research_papers
            GROUP BY source
            ORDER BY paper_count DESC
            """
        ).fetchall()

        return {
            "success": True,
            "data": [
                {
                    "source": row[0],
                    "paper_count": row[1],
                }
                for row in rows
            ],
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "data": [],
        }

    finally:
        if connection is not None:
            connection.close()


def get_topic_statistics(
    database_path: Optional[str] = None,
) -> dict:
    """Aggregate research paper counts by topic."""

    connection = None

    try:
        connection = _connect(database_path)

        rows = connection.execute(
            """
            SELECT topics_json
            FROM research_papers
            WHERE topics_json IS NOT NULL
            """
        ).fetchall()

        topic_counts = {}

        for (topics_json,) in rows:
            try:
                topics = json.loads(topics_json or "[]")
            except (json.JSONDecodeError, TypeError):
                continue

            for topic in topics:
                name = _safe_string(topic)

                if name:
                    topic_counts[name] = (
                        topic_counts.get(name, 0) + 1
                    )

        results = [
            {
                "topic": topic,
                "paper_count": count,
            }
            for topic, count in topic_counts.items()
        ]

        results.sort(
            key=lambda item: item["paper_count"],
            reverse=True,
        )

        return {
            "success": True,
            "data": results,
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "data": [],
        }

    finally:
        if connection is not None:
            connection.close()


def export_warehouse_json(
    output_path: Optional[str] = None,
    database_path: Optional[str] = None,
) -> dict:
    """Export the warehouse records to a JSON file."""

    connection = None

    try:
        connection = _connect(database_path)

        rows = connection.execute(
            """
            SELECT *
            FROM research_papers
            ORDER BY publication_year DESC NULLS LAST
            """
        ).fetchdf()

        records = rows.to_dict(orient="records")

        for record in records:
            for field in ("authors_json", "topics_json"):
                value = record.get(field)

                try:
                    record[field.replace("_json", "")] = (
                        json.loads(value) if value else []
                    )
                except (json.JSONDecodeError, TypeError):
                    record[field.replace("_json", "")] = []

                record.pop(field, None)

            # Convert timestamps into JSON-compatible strings.
            if record.get("updated_at") is not None:
                record["updated_at"] = str(
                    record["updated_at"]
                )

        destination = (
            Path(output_path)
            if output_path
            else DEFAULT_DATA_DIR / "warehouse_export.json"
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temporary_path = destination.with_suffix(
            destination.suffix + ".tmp"
        )

        with temporary_path.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                records,
                file,
                ensure_ascii=False,
                indent=2,
                default=str,
            )

        os.replace(temporary_path, destination)

        return {
            "success": True,
            "message": "Warehouse exported successfully.",
            "file_path": str(destination),
            "records_exported": len(records),
        }

    except Exception as exc:
        return {
            "success": False,
            "message": str(exc),
            "file_path": None,
            "records_exported": 0,
        }

    finally:
        if connection is not None:
            connection.close()
