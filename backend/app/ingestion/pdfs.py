from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError


BACKEND_DIR = Path(__file__).resolve().parents[2]
PDF_STORAGE_DIR = BACKEND_DIR / "data" / "research_papers"
MAX_PDF_BYTES = 100 * 1024 * 1024
DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.IGNORECASE)


def _date_from_pdf_metadata(value: Any) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    match = re.search(r"D:(\d{4})(\d{2})?(\d{2})?", text)
    if not match:
        return None
    year, month, day = match.groups()
    try:
        return datetime(
            int(year),
            int(month or "1"),
            int(day or "1"),
        ).date().isoformat()
    except ValueError:
        return None


def _extract_pdf(path: Path, root: Path) -> dict[str, Any]:
    if path.stat().st_size > MAX_PDF_BYTES:
        raise ValueError("PDF exceeds the 100 MiB processing limit.")

    reader = PdfReader(str(path), strict=True)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDFs are not supported.")

    metadata = reader.metadata
    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    ).strip()
    if not text:
        raise ValueError("No extractable text was found in the PDF.")

    title = str(getattr(metadata, "title", "") or "").strip()
    if not title or title.casefold() in {"untitled", "microsoft word"}:
        title = path.stem.replace("_", " ").replace("-", " ").strip()
    if not title:
        raise ValueError("The PDF has no usable title or filename.")

    author_text = str(getattr(metadata, "author", "") or "").strip()
    authors = [
        {"name": name.strip()}
        for name in re.split(r"\s*;\s*|\s*\|\s*", author_text)
        if name.strip()
    ]
    doi_match = DOI_PATTERN.search(text[:10000])
    doi = doi_match.group(0).rstrip(".,;:") if doi_match else None
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "source": "local_pdf",
        "source_id": file_hash,
        "doi": doi,
        "title": title,
        "abstract": text,
        "authors": authors,
        "publication_date": _date_from_pdf_metadata(
            getattr(metadata, "creation_date", None)
        ),
        "topics": [],
        "journal": None,
        "type": "research_paper",
        "language": None,
        "cited_by_count": 0,
        "is_open_access": None,
        "landing_page_url": None,
        "pdf_url": None,
        "_local_pdf_filename": path.relative_to(root).as_posix(),
        "_local_pdf_sha256": file_hash,
    }


def scan_local_pdfs(
    folder: str | Path = PDF_STORAGE_DIR,
) -> dict[str, Any]:
    """Extract paper records from PDFs without moving or copying originals."""
    root = Path(folder).resolve()
    root.mkdir(parents=True, exist_ok=True)
    records = []
    failures = []

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.casefold() != ".pdf":
            continue
        try:
            records.append(_extract_pdf(path, root))
        except (OSError, PdfReadError, ValueError) as exc:
            failures.append({
                "file": path.name,
                "error": str(exc).replace(str(path), path.name),
            })

    return {
        "directory": root,
        "records": records,
        "failures": failures,
    }
