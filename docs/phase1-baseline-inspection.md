# Phase 1 — Repository Safety & Baseline Inspection

**Date:** 25 November 2026  
**Repository:** `Pinakapaanip/DMW_PROJECT`  
**Current Branch:** `backend-adarsh` (tracking `origin/backend-adarsh`)  
**Remote:** `https://github.com/Pinakapaanip/DMW_PROJECT.git` (fetch & push configured)

---

## 1. Git Baseline

Recent commits on `backend-adarsh`:
- `dc9a321` Updated project files
- `6feef1f` Update DMW_PROJECT
- `65797fa` okay
- `5a151b8` Merge pull request #1 from Pinakapaanip/frontend-roy
- `2a1f32b` Build Roy's F1-F3 frontend

Untracked local artifacts in root (do not commit):
- `DMW-CourseProject (1).pdf`
- `DMW_PROJECT.7z`
- `backend-code.zip`

---

## 2. File & Module Inventory

### Root
- `README.md` — 27-phase implementation plan
- `.gitignore` — ignores `node_modules/`, `dist/`, `.env`, `.env.*`, `!.env.example`, `__pycache__/`, `*.py[cod]`, `.venv/`, `venv/`
- `backend/` — FastAPI backend
- `frontend/` — React + Vite frontend (`package.json`, `src/api.js`, `src/App.jsx`, `src/main.jsx`, `src/styles.css`)

### Backend Module Status (45 Python files, 0 syntax errors)

| Area | Status | Files & Details |
| --- | --- | --- |
| **App & DB Core** | **Working (Partial Schema)** | `backend/main.py` (FastAPI app, CORS, `/health`, `auth_router`), `app/database/connection.py`, `app/database/models.py` (`User`, `RevokedToken` only; missing domain tables for profiles, follows, posts, library, papers, events) |
| **F1 Auth (`app/auth/`)** | **Working (Verified by pytest)** | `routes.py`, `schemas.py`, `security.py`, `service.py` — `/api/v1/auth/{register,login,me,logout}` passing 3/3 tests in `backend/tests/test_auth.py` (role enforcement still pending) |
| **F1 Profiles (`app/profiles/`)** | **Empty (0 bytes)** | `routes.py`, `schemas.py`, `service.py`, `__init__.py` |
| **F2 Posts (`app/posts/`)** | **Empty (0 bytes)** | `routes.py`, `schemas.py`, `service.py`, `__init__.py` |
| **F3 Library (`app/library/`)** | **Empty (0 bytes)** | `routes.py`, `schemas.py`, `service.py`, `__init__.py` |
| **F4 Ingestion (`app/ingestion/`)** | **Implemented (Unverified / Not Wired)** | `fetch.py` (96L), `arxiv.py` (173L), `openalex.py` (173L), `clean.py` (243L), `pipeline.py` (333L) |
| **F5 Search (`app/search/`)** | **Implemented (Unverified / Not Wired)** | `deduplication.py` (200L), `keyword.py` (221L), `semantic.py` (256L), `unified.py` (262L) |
| **F6 Recommendations (`app/recommendations/`)** | **Implemented (Unverified / Not Wired)** | `papers.py` (398L), `researchers.py` (362L) |
| **F7 Trends (`app/trends/`)** | **Implemented (Unverified / Not Wired)** | `trending.py` (349L), `anomaly.py` (318L) |
| **F8 Assistant (`app/assistant/`)** | **Implemented (Unverified / Not Wired)** | `retrieval.py` (367L), `answer.py` (445L) |
| **F9 Analytics (`app/analytics/`)** | **Implemented (Unverified / Not Wired)** | `warehouse.py` (630L), `dashboard.py` (480L) |

---

## 3. Current Run Instructions

### Backend
```powershell
cd backend
copy .env.example .env
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```
- Health check: `http://localhost:8000/health`
- OpenAPI docs: `http://localhost:8000/docs`
- Tests: `.\.venv\Scripts\python.exe -m pytest -v`

### Frontend
```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

---

## 4. Missing Dependencies

Inspection of `backend/requirements.txt` vs. actual imports across `backend/app/` found:
- `numpy` — imported by Pinaka's intelligence modules, **not listed** in `backend/requirements.txt` and not installed in `backend/.venv`.
- `rapidfuzz` — imported by `app/search/deduplication.py` / Pinaka's modules, **not listed** in `backend/requirements.txt` and not installed in `backend/.venv`.
- `docs/architecture.md` and `docs/api-contracts.md` — not yet created (Phase 4).
