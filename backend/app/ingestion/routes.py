import json
from collections import defaultdict
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.connection import get_db
from app.database.models import ResearchPaper, User
from app.ingestion.clean import normalize_papers
from app.ingestion.pdfs import PDF_STORAGE_DIR, scan_local_pdfs
from app.ingestion.pipeline import run_ingestion
from app.ingestion.storage import load_papers, upsert_papers
from app.search.deduplication import deduplicate_papers, normalize_title


router = APIRouter(tags=["F4 Research paper ingestion"])


class IngestionRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    source: Literal["arxiv", "openalex", "all"] = "all"
    limit: int = Field(default=100, ge=1, le=500)
    page_size: int = Field(default=100, ge=1, le=200)
    mailto: str | None = None


def _associate_local_files(records, papers):
    files_by_paper: dict[str, list[dict[str, str]]] = defaultdict(list)
    normalized_records = []
    for raw in records:
        normalized_records.append({
            key: value
            for key, value in raw.items()
            if not key.startswith("_local_pdf_")
        })

    normalized = normalize_papers(normalized_records)
    raw_files = [
        {
            "filename": record["_local_pdf_filename"],
            "sha256": record["_local_pdf_sha256"],
            "source_id": record["source_id"],
        }
        for record in records
    ]
    for paper in papers:
        title = normalize_title(paper.get("title"))
        for normalized_paper in normalized:
            same_identity = (
                paper.get("doi")
                and paper.get("doi") == normalized_paper.get("doi")
            )
            same_title = title == normalize_title(
                normalized_paper.get("title")
            )
            if same_identity or same_title:
                for file_record in raw_files:
                    if file_record["source_id"] == normalized_paper.get("source_id"):
                        files_by_paper[paper["paper_id"]].append({
                            "filename": file_record["filename"],
                            "sha256": file_record["sha256"],
                        })
    return files_by_paper


@router.post("/api/v1/ingestion/run")
def ingest_remote_papers(
    data: IngestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        summary = run_ingestion(
            query=data.query,
            source=data.source,
            limit=data.limit,
            page_size=data.page_size,
            mailto=data.mailto,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    normalized_path = Path(summary["normalized_file"])
    with normalized_path.open(encoding="utf-8") as file:
        normalized = [json.loads(line) for line in file if line.strip()]
    unique_papers = deduplicate_papers(normalized)
    persisted = upsert_papers(db, unique_papers)
    return {
        "success": True,
        "run_id": summary["run_id"],
        "query": summary["query"],
        "source": summary["source"],
        "records_fetched": summary["records_fetched"],
        "total_unique": len(unique_papers),
        **persisted,
    }


@router.post("/api/v1/ingestion/local-pdfs")
def ingest_local_pdfs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = scan_local_pdfs(PDF_STORAGE_DIR)
    normalized = normalize_papers([
        {
            key: value
            for key, value in record.items()
            if not key.startswith("_local_pdf_")
        }
        for record in scan["records"]
    ])
    unique_papers = deduplicate_papers(normalized)
    local_files = _associate_local_files(
        scan["records"],
        unique_papers,
    )
    persisted = upsert_papers(db, unique_papers, local_files)
    return {
        "success": True,
        "directory_scanned": True,
        "files_found": len(scan["records"]) + len(scan["failures"]),
        "files_ingested": len(scan["records"]),
        "papers_normalized": len(unique_papers),
        "failures": scan["failures"],
        **persisted,
    }


@router.get("/api/v1/papers")
def list_papers(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    papers = load_papers(db)
    return {
        "items": papers[offset:offset + limit],
        "total": len(papers),
        "limit": limit,
        "offset": offset,
    }


@router.get("/api/v1/papers/{paper_id}/pdf")
def get_local_pdf(
    paper_id: str,
    file_index: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    paper = db.get(ResearchPaper, paper_id)
    if paper is None or file_index >= len(paper.local_pdf_files or []):
        raise HTTPException(status_code=404, detail="Local paper PDF not found.")
    root = PDF_STORAGE_DIR.resolve()
    path = (root / paper.local_pdf_files[file_index]).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(status_code=404, detail="Local paper PDF not found.")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
    )
