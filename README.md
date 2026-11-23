# Chanakya Research Commons

## Detailed Project Rebuild & Implementation Plan

**Course:** Data Mining and Warehousing, V Semester B.Tech., 2026–27\
**University:** Chanakya University, School of Engineering\
**Repository:** [Pinakapaanip/DMW_PROJECT](https://github.com/Pinakapaanip/DMW_PROJECT)\
**Submission date:** 28 November 2026\
**Team:** Adarsh, Pinaka, Roy, Ashish\
**Document purpose:** A precise, phase-by-phase plan for rebuilding the
project carefully, with clear ownership, inputs, implementation steps,
outputs, verification, and Git rules.

------------------------------------------------------------------------

# 0. How to use this plan

This is the team's implementation contract. Read the whole plan once,
then work through the phases in order. Do not skip a phase's exit
criteria.

Each phase states:

- **Goal:** what problem this phase solves.
- **Owners:** who is responsible.
- **Steps:** what to do, in order.
- **Deliverables:** what must exist at the end.
- **Verification:** how to prove it works.
- **Exit gate:** the condition required before moving on.

A folder or Python file existing is not proof that a feature is
complete. A feature is complete only when it runs, uses the agreed data
contract, has a verification step, and is integrated where required.

## Important scope distinction

The project brief defines nine functional subsystems:

-   F1 Accounts and profiles
-   F2 Posts and discussions
-   F3 Library
-   F4 External content ingestion
-   F5 Unified search
-   F6 Recommendations
-   F7 Trends and monitoring
-   F8 Research assistant
-   F9 Institutional analytics

The brief says F5 is the centrepiece: one topic search should return
external scholarly papers, items in the Chanakya library, university
members, and related posts/discussions in one view.

The brief also gives suggested scale targets: 500+ paper records, 50+
synthetic members across 6+ departments, 2,000+ posts/comments, and
10,000+ save/view/search events over six months. These are targets in
the brief, not proof that the team has already generated this data.
Record the actual volume achieved and disclose any gap.

------------------------------------------------------------------------

# 1. Current state assessment

Inspection of this repository on 23 November 2026 shows this backend
structure:

``` text
backend/
├── app/
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   └── warehouse.py
│   ├── assistant/
│   │   ├── __init__.py
│   │   ├── answer.py
│   │   └── retrieval.py
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   ├── schemas.py
│   │   └── security.py
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── arxiv.py
│   │   ├── clean.py
│   │   ├── fetch.py
│   │   ├── openalex.py
│   │   └── pipeline.py
│   ├── library/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── posts/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── profiles/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── recommendations/
│   │   ├── __init__.py
│   │   ├── papers.py
│   │   └── researchers.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── deduplication.py
│   │   ├── keyword.py
│   │   ├── semantic.py
│   │   └── unified.py
│   └── trends/
│       ├── __init__.py
│       ├── anomaly.py
│       └── trending.py
└── main.py
```

This is a **module skeleton**. Every Python file listed above exists,
and each one is empty. `backend/app/database/` has no `__init__.py` yet,
so it is not an importable package. There is no frontend,
`requirements.txt`, `.env.example`, test suite, or `docs/` folder.

An empty file is not evidence that the database can be initialized,
that routes are registered, that APIs return correct data, or that
tests pass.

Therefore, the plan begins with inspection and verification rather than
blindly generating replacement files.

**Preserve existing repository content.** This repository is
`Pinakapaanip/DMW_PROJECT`. It does not contain a separate Q1, lab, or
coursework tree. Do not delete this plan, and do not delete the backend
skeleton while implementing a phase.

------------------------------------------------------------------------

# 2. Team ownership

## Adarsh --- Backend Core

Owns: - F1 registration, login, roles, user profiles and follows. - F2
posts, tags, comments, replies, upvotes and feed. - F3 paper saving,
personal collections and private notes. - Core database connection and
the agreed shared application schema. - Final coordination of backend
router integration with Pinaka.

## Pinaka --- Backend Data Engineering and Intelligence

Owns: - F4 OpenAlex/arXiv/RSS ingestion where appropriate, raw
preservation, cleaning, incremental refresh and Parquet export. - F5
keyword search, semantic search, deduplication, result merging and
ranking. - F6 paper, researcher and co-save recommendations. - F7
trending topics, spike detection and abnormal activity flags. - F8
retrieval-based research assistant with citations and evidence
passages. - F9 DuckDB/Parquet analytics queries and analytics API
endpoints. - Data pipeline tests and numerical evaluation scripts.

## Roy --- Frontend Core

Owns: - Shared frontend shell and agreed route/layout conventions. -
Registration/login screens. - Profile screens and follow controls. -
Feed, post creation, post detail, comments and upvotes. - Library,
save/remove, collections and private notes. - API integration for
F1--F3.

## Ashish --- Frontend Discovery

Owns: - Unified search screen and four result panels. - External/library
paper result cards and source display. - Researcher and discussion
results. - Paper and researcher recommendations. - Research assistant
chat, citations and retrieved passages. - Trends/alerts screen. - Admin
analytics dashboard and charts. - API integration for F5--F9.

## Shared ownership rules

-   `backend/app/database/models.py` is a shared contract. Adarsh
    coordinates the schema; Pinaka supplies data/analytics requirements.
    Agree before editing.
-   `backend/main.py` is shared integration code. Assign one person to
    integrate routers after each module is ready.
-   Frontend router, global styles, app shell and shared API client must
    have one agreed owner at a time. Roy leads shell/routing; Ashish
    adds discovery pages through the agreed route interface.
-   Never create a second users table or a separate incompatible papers
    table for Pinaka's work.
-   All four contribute to tests, technical report, screenshots, demo
    and viva.

------------------------------------------------------------------------

# 3. Recommended technical architecture

First inspect the technologies already present in the repository. Keep
working choices if they are already configured correctly. Do not change
the database or framework just to match this suggestion.

| Layer | Practical choice |
| --- | --- |
| Frontend | React + Vite |
| Styling | Existing configured styling; Tailwind if not yet selected |
| Routing | React Router |
| API client | Axios or fetch |
| Backend | FastAPI |
| Main database | Existing configured DB; SQLite for a simple local MVP, PostgreSQL if already installed and working |
| ORM / validation | SQLAlchemy + Pydantic |
| External scholarly data | OpenAlex and arXiv APIs |
| Data processing | Pandas |
| Analytical files | Parquet |
| Analytics query engine | DuckDB |
| Keyword baseline | Database search or TF-IDF |
| Semantic search | Sentence Transformers after the keyword baseline works |
| Recommendations | Content-based similarity and co-save collaborative signals |
| Dashboard charts | Recharts |
| Tests | pytest, API tests, browser checks |
| API documentation | FastAPI OpenAPI `/docs` |

Potential later additions from the brief include pgvector, MinIO, Docker
Compose, a scheduler, NetworkX, datasketch, mlxtend, Ollama, Metabase or
Superset. These are optional design choices, not mandatory dependencies.
Add them only when the team can install, run and explain them.

------------------------------------------------------------------------

# 4. Detailed implementation phases

## PHASE 1 --- Repository safety and baseline inspection

**Owners:** All four; Adarsh coordinates backend inspection, Roy
coordinates frontend inspection.

### Goal

Understand the existing repository before modifying it. Avoid
overwriting existing work or building duplicate structures.

### Steps

1.  Open this repository, `Pinakapaanip/DMW_PROJECT`, in Cursor.
2.  Run `git status` and record the current branch.
3.  Run `git log --oneline -5` to inspect recent history.
4.  Inspect the root folder and existing README.
5.  Inspect backend dependency files and frontend `package.json`.
6.  Open the existing `main.py`, database connection and model files.
7.  Open the existing ingestion/search/recommendation modules; do not
    assume they are empty.
8.  Identify whether frontend code already exists. If not, record that
    as a task.
9.  Confirm that the team has write permission or decide whether to use
    a fork.
10. Take a backup or ensure all existing work is committed before
    restructuring.

### Deliverables

-   A short inventory of existing files.
-   A list of working, incomplete, empty and unknown modules.
-   Current run instructions, if any.
-   A list of missing dependencies.

### Verification

Every member can open the same repository and see the same committed
baseline.

### Exit gate

No one begins large feature implementation until the team knows what
already exists and what must be preserved.

------------------------------------------------------------------------

## PHASE 2 --- Git branches, collaboration and commit rules

**Owners:** All four.

### Goal

Allow parallel work without everyone editing `main` or overwriting
teammates' work.

### Branch allocation

| Person | Branch |
| --- | --- |
| Adarsh | `backend-adarsh` |
| Pinaka | `backend-pinaka` |
| Roy | `frontend-roy` |
| Ashish | `frontend-ashish` |

### Steps

1.  Agree on the integration base branch (`main` unless the team
    explicitly selects another).
2.  Each person fetches the latest repository state.
3.  Each person creates or switches to their own branch.
4.  Each person checks `git status` before editing.
5.  Commit small, logical changes with descriptive messages.
6.  Push the branch to GitHub.
7.  Open a Pull Request to the agreed integration branch.
8.  Another teammate reviews the changed files and test results.
9.  Merge only after the integration branch remains runnable.

### Commands for a new branch

``` bash
git switch main
git pull origin main
git switch -c backend-adarsh
```

Use the person's assigned branch name. If the branch already exists,
fetch and switch to it rather than creating it again.

### Commands to save work

``` bash
git status
git diff
git add path/to/your/owned/files
git commit -m "Describe the completed change"
git push -u origin backend-adarsh
```

### Rules

-   Do not push directly to `main`.
-   Do not use `git push --force` on shared branches.
-   Do not blindly stage generated data, `.env`, credentials, virtual
    environments, `node_modules` or model caches.
-   If not a repository collaborator, push to a fork and open a Pull
    Request.

### Exit gate

All four have a working branch and can push a test commit without
affecting `main`.

------------------------------------------------------------------------

## PHASE 3 --- Environment setup and reproducible local run

**Owners:** Adarsh (backend environment), Roy (frontend environment),
Pinaka and Ashish verify their tools.

### Goal

Make sure every teammate can run the project on their own machine.

### Backend steps

1.  Confirm the installed Python version.
2.  Create or reuse the backend virtual environment.
3.  Install packages from a shared requirements file.
4.  Create `.env.example` with required variable names and safe
    placeholder values.
5.  Keep real credentials and local secrets in `.env`, which must be
    ignored by Git.
6.  Confirm the backend starts.
7.  Confirm the health endpoint responds.
8.  Confirm FastAPI docs open.

### Frontend steps

1.  Confirm Node.js and npm versions.
2.  Install dependencies from the existing package manifest.
3.  Start the Vite development server.
4.  Confirm the application opens in a browser.
5.  Confirm the frontend can reach the backend health endpoint.

### Deliverables

-   Backend requirements/dependency file.
-   Frontend package manifest and lock file.
-   `.env.example`.
-   `.gitignore`.
-   Documented start commands.

### Verification

A teammate who did not set up the project can follow the instructions
and start both services.

### Exit gate

Backend and frontend both run locally without relying on undocumented
machine-specific settings.

------------------------------------------------------------------------

## PHASE 4 --- Architecture and API contract design

**Owners:** Adarsh and Pinaka for backend contracts; Roy and Ashish for
frontend contracts.

### Goal

Agree on how modules exchange data before parallel coding begins.

### Steps

1.  Draw the high-level architecture: browser → frontend → FastAPI →
    application DB / ingestion / search / analytics.
2.  Agree on the main database.
3.  Agree on shared entity IDs and naming conventions.
4.  Agree on API route prefixes and HTTP methods.
5.  Agree on response and error formats.
6.  Agree on authentication token handling.
7.  Agree on pagination, filtering and sorting conventions.
8.  Record the decisions in `docs/architecture.md` and
    `docs/api-contracts.md`.

### Unified search response contract

The F5 endpoint must return four categories. Example shape:

``` json
{
  "query": "machine learning healthcare",
  "external_papers": [],
  "library_papers": [],
  "researchers": [],
  "discussions": []
}
```

The real implementation must populate these lists from actual
stored/fetched data. Empty lists are valid when there are no matches;
fabricated records are not.

### Deliverables

-   Architecture diagram.
-   API contract document.
-   Agreed response shapes.
-   Agreed ownership of shared files.

### Exit gate

All four can explain which API they are building or consuming and what
data it accepts/returns.

------------------------------------------------------------------------

## PHASE 5 --- Database schema and data model

**Owner:** Adarsh leads; Pinaka reviews the paper, source, event and
analytics requirements.

### Goal

Create one consistent database that supports F1--F9.

### Suggested entities

#### User and community data

-   `users`
-   `profiles`
-   `follows`
-   `posts`
-   `comments`
-   `votes`
-   `tags` or post-tag association

#### Research paper and library data

-   `papers`
-   `paper_sources`
-   `saved_papers`
-   `collections`
-   `collection_items`

#### Data mining and analytics

-   `activity_events`
-   `paper_embeddings` (only if embeddings are implemented)
-   optional topic/keyword associations

### Steps

1.  Define each entity's purpose.
2.  Define primary keys and foreign keys.
3.  Define required and optional fields.
4.  Define uniqueness rules.
5.  Define timestamps and timezone handling.
6.  Define relationships and deletion behaviour.
7.  Add database initialization/migrations.
8.  Create a small test database.
9.  Add a few test records.
10. Test reads, inserts, updates and foreign-key constraints.

### Critical schema rule

There must be one canonical `papers` table. A paper imported from
OpenAlex and arXiv should resolve to the same canonical paper when it is
the same work. `paper_sources` records where the canonical paper was
found.

### Deliverables

-   ER diagram.
-   Shared SQLAlchemy models.
-   Database initialization/migration.
-   Seed/test script.

### Exit gate

The database can be created from scratch and both backend developers can
use the same models without conflicting definitions.

------------------------------------------------------------------------

## PHASE 6 --- Backend foundation and router integration pattern

**Owners:** Adarsh coordinates `main.py`; Pinaka confirms how his
modules will be registered.

### Goal

Establish a consistent way to build and expose API modules.

### Steps

1.  Confirm the FastAPI app creation in `main.py`.
2.  Establish a router convention for each module.
3.  Establish common error responses.
4.  Establish request/response validation with Pydantic.
5.  Establish database session dependency injection.
6.  Establish authentication dependency conventions.
7.  Register one test router.
8.  Confirm `/docs` displays the route.
9.  Add a health endpoint.
10. Add a basic pytest API test.

### Deliverables

-   Working FastAPI app.
-   Consistent router registration.
-   Database dependency.
-   Health endpoint.
-   Basic test.

### Exit gate

A module can add a router without changing unrelated modules or
duplicating application setup.

------------------------------------------------------------------------

## PHASE 7 --- F1 Part A: Registration, login and roles

**Owner:** Adarsh.

### Goal

Allow users to register and securely access the platform.

### Steps

1.  Define registration fields and validation rules.
2.  Enforce unique email addresses.
3.  Hash passwords with a suitable password-hashing library.
4.  Never store plaintext passwords.
5.  Implement registration endpoint.
6.  Implement login endpoint.
7.  Issue and verify access tokens.
8.  Implement current-user endpoint.
9.  Add role values: student, faculty, researcher, admin.
10. Protect endpoints based on authentication and role.
11. Test invalid credentials, duplicate registration and unauthorized
    requests.

### Example endpoints

-   `POST /auth/register`
-   `POST /auth/login`
-   `GET /auth/me`

### Deliverables

Working registration, login, token validation and role checks.

### Exit gate

A user can register, log in, access a protected endpoint, and is denied
access when unauthenticated or unauthorized.

------------------------------------------------------------------------

## PHASE 8 --- F1 Part B: Profiles, interests and follows

**Owner:** Adarsh; Roy consumes the API.

### Goal

Make each member discoverable by research area.

### Steps

1.  Define profile fields: department, bio, interests, tags,
    publication/personal links.
2.  Implement profile creation/update.
3.  Implement own-profile retrieval.
4.  Implement public member listing and profile retrieval.
5.  Implement follow/unfollow member.
6.  Implement topic follow/unfollow if included in the agreed schema.
7.  Prevent duplicate follows.
8.  Add validation and authorization.
9.  Test profile updates and follow relationships.

### Example endpoints

Implemented in `backend/app/profiles` and mounted under `/users`:

-   `GET /users/me`
-   `PUT /users/me`
-   `GET /users`
-   `GET /users/{user_id}`
-   `POST /users/{user_id}/follow`
-   `DELETE /users/{user_id}/follow`

Topic follow is optional. Add those routes only after the shared schema
includes topic follows. They are not part of the contract in section 6.

### Deliverables

Working profile and follow system.

### Exit gate

A logged-in user can update their research interests and follow another
member.

------------------------------------------------------------------------

## PHASE 9 --- F2: Posts and discussions

**Owner:** Adarsh; Roy consumes the API.

### Goal

Allow university members to share and discuss research.

### Steps

1.  Define post schema: author, body, tags, optional paper reference,
    timestamps.
2.  Implement create/list/retrieve post.
3.  Implement edit/delete with ownership checks.
4.  Implement tags.
5.  Implement comments.
6.  Implement replies using parent-comment relationships.
7.  Implement upvotes with one vote per user per post.
8.  Record relevant activity events.
9.  Implement a simple personal feed using followed members/topics.
10. Test authorization and duplicate-vote behaviour.

### Example endpoints

-   `POST /posts`
-   `GET /posts`
-   `GET /posts/{post_id}`
-   `PUT /posts/{post_id}`
-   `DELETE /posts/{post_id}`
-   `POST /posts/{post_id}/comments`
-   `POST /posts/{post_id}/upvote`
-   `GET /feed`

### Deliverables

Working post and discussion APIs.

### Exit gate

A member can publish a post, another member can comment, and the feed
returns stored posts.

------------------------------------------------------------------------

## PHASE 10 --- F3: Shared research library

**Owner:** Adarsh; Pinaka defines the canonical paper/source contract.

### Goal

Allow users to save and organize papers in a university-wide shared
library.

### Steps

1.  Agree on the canonical paper fields with Pinaka.
2.  Implement save by paper ID.
3.  Support adding a paper from URL, DOI or arXiv ID where source
    resolution is available.
4.  Prevent duplicate saves by the same user.
5.  Implement personal library listing.
6.  Implement removal of a personal save.
7.  Implement personal collections.
8.  Implement collection item management.
9.  Implement private notes with owner-only access.
10. Calculate university-wide save counts from actual user saves.
11. Record save/remove activity events.
12. Test privacy and duplicate-save behaviour.

### Example endpoints

-   `POST /library/save`
-   `GET /library`
-   `DELETE /library/{paper_id}`
-   `POST /library/collections`
-   `GET /library/collections`

### Deliverables

Working personal and university-wide library.

### Exit gate

Two different users can save the same canonical paper; the university
library shows one paper with the correct save count.

------------------------------------------------------------------------

## PHASE 11 --- F4 Part A: External source clients

**Owner:** Pinaka.

### Goal

Fetch real scholarly metadata through permitted open APIs.

### Steps

1.  Read OpenAlex API documentation and identify the Works endpoint and
    pagination format.
2.  Choose a small list of research topics relevant to multiple
    university departments.
3.  Implement `openalex.py` to fetch works metadata.
4.  Implement `arxiv.py` to fetch arXiv metadata.
5.  Implement common HTTP handling in `fetch.py`.
6.  Add request timeout and error handling.
7.  Add pagination and rate-limit awareness.
8.  Add retry behaviour for temporary failures.
9.  Preserve source IDs and source names.
10. Test with a small batch before increasing volume.

### Deliverables

-   OpenAlex fetcher.
-   arXiv fetcher.
-   Common fetch utilities.
-   Sample raw API response files.

### Exit gate

The scripts can fetch real records and handle a temporary API/network
failure without crashing the entire pipeline.

------------------------------------------------------------------------

## PHASE 12 --- F4 Part B: Raw preservation and normalization

**Owner:** Pinaka; Adarsh confirms canonical database fields.

### Goal

Keep original source records and create a consistent representation for
analysis.

### Steps

1.  Store original API responses unchanged in a dated raw-data
    directory.
2.  Do not overwrite raw responses with cleaned records.
3.  Map source-specific field names into the canonical paper schema.
4.  Normalize DOI format.
5.  Normalize title whitespace and casing for comparison while retaining
    display title.
6.  Standardize author representation.
7.  Parse publication year and URLs safely.
8.  Extract abstracts where available.
9.  Record missing or malformed fields.
10. Write normalized data to a separate processed output.
11. Add tests for mapping and malformed records.

### Deliverables

-   Raw response storage.
-   Normalization code in `clean.py`.
-   Processed records.
-   Normalization tests.

### Exit gate

The same source response can be reprocessed reproducibly, and raw data
remains unchanged.

------------------------------------------------------------------------

## PHASE 13 --- F4 Part C: Deduplication, database upsert and analytics export

**Owner:** Pinaka; Adarsh reviews shared database writes.

### Goal

Build a repeatable ingestion pipeline without creating duplicate paper
records.

### Steps

1.  Match exact DOI first when present.
2.  Match stable source record IDs.
3.  Compare normalized titles as a fallback.
4.  Use fuzzy title similarity only as a cautious fallback; do not merge
    uncertain matches automatically.
5.  Create/update the canonical paper record.
6.  Add or update `paper_sources` records.
7.  Track ingestion timestamps and source identifiers.
8.  Make repeated ingestion idempotent.
9.  Export processed records to Parquet.
10. Partition Parquet sensibly by ingestion date or year if useful.
11. Use DuckDB to verify the export can be queried.
12. Test repeated ingestion and duplicate cases.

### Deliverables

-   Integration with `backend/app/search/deduplication.py`.
-   `pipeline.py` orchestration.
-   Canonical paper records in database.
-   Parquet export.
-   Idempotency tests.

### Exit gate

Running the same ingestion batch twice does not create duplicate
canonical paper records.

------------------------------------------------------------------------

## PHASE 14 --- F5 Part A: Keyword search across all four categories

**Owner:** Pinaka; Ashish consumes the API.

### Goal

Implement one query that returns all required categories.

### Steps

1.  Agree the search response contract with Ashish.
2.  Implement paper keyword search over title, abstract, authors and
    topics.
3.  Implement library search over canonical papers and save records.
4.  Implement researcher search over profile interests, department and
    tags.
5.  Implement discussion search over post body and tags.
6.  Normalize query input.
7.  Apply pagination/limits.
8.  Return empty arrays when a category has no match.
9.  Add error handling and tests for each category.
10. Integrate all four searches in `unified.py`.

### Required result categories

-   External papers.
-   Chanakya library papers.
-   Researchers.
-   Posts/discussions.

### Deliverables

One unified search endpoint with four result arrays.

### Exit gate

A single query returns results from all available categories using
actual stored records.

------------------------------------------------------------------------

## PHASE 15 --- F5 Part B: Duplicate merging, ranking and semantic search

**Owner:** Pinaka; Ashish displays source/rank information.

### Goal

Improve search quality and prevent repeated representations of the same
paper.

### Steps

1.  Implement DOI-based duplicate matching.
2.  Add normalized-title matching.
3.  Add fuzzy title matching with a documented threshold and
    manual-review path for uncertain cases.
4.  Preserve all source identifiers when records merge.
5.  Implement a simple documented ranking score.
6.  Establish a keyword-only baseline.
7.  Build a small labelled query/relevance test set.
8.  Measure Precision@5, Recall@5 and MRR.
9.  Add TF-IDF/cosine similarity or Sentence Transformers for semantic
    search.
10. Compare semantic/combined search against the keyword baseline.
11. Record actual metrics and limitations.

### Deliverables

-   Duplicate merge logic.
-   Search ranking.
-   Optional semantic search.
-   Search evaluation script and results.

### Exit gate

Duplicate cases are tested, source information is retained, and search
quality is measured rather than described only qualitatively.

------------------------------------------------------------------------

## PHASE 16 --- F6: Recommendation engine

**Owner:** Pinaka; Ashish owns recommendation screens.

### Goal

Recommend papers and people using actual profile and activity data.

### Part A: Paper recommendations

1.  Read a user's declared research interests.
2.  Read the topics/text of papers they saved.
3.  Represent paper text and user interests using a simple baseline such
    as TF-IDF.
4.  Calculate similarity.
5.  Exclude papers already saved by the user.
6.  Return top-ranked papers with a reason.

### Part B: Researcher recommendations

1.  Compare profile interest tags.
2.  Compare saved-paper topics where available.
3.  Exclude the current user and already-followed users.
4.  Return similar members with a reason such as shared interests.

### Part C: Co-save recommendations

1.  Build user-paper save relationships.
2.  Find users who saved the currently viewed paper.
3.  Count other papers saved by those users.
4.  Exclude the current paper and papers already saved by the current
    user.
5.  Rank by co-save count.

### Part D: Cold start

For new users with no history, use selected interests, popular papers,
or recent papers.

### Deliverables

-   Paper recommendations endpoint.
-   Researcher recommendations endpoint.
-   Co-save endpoint.
-   Recommendation tests.

### Exit gate

Recommendations work for both a user with history and a new user, and
their quality is measured against a baseline where feasible.

------------------------------------------------------------------------

## PHASE 17 --- F7: Trends and anomaly monitoring

**Owner:** Pinaka; Ashish owns trends/alerts UI.

### Goal

Identify rising research topics and unusual activity from stored data.

### Part A: Trending topics

1.  Define which events count: post tags, paper topics, saves, searches,
    or a documented combination.
2.  Choose a recent time window.
3.  Calculate counts per topic.
4.  Calculate a comparison baseline from an earlier window.
5.  Calculate change or rate.
6.  Define a spike threshold.
7.  Return topic, count, baseline and spike reason.
8.  Test against synthetic planted spikes.

### Part B: Abnormal activity

1.  Define suspicious signals: excessive post frequency, repeated
    identical text, unusual save volume.
2.  Calculate user activity features over a defined window.
3.  Begin with transparent threshold-based rules.
4.  Record the reason a user/event is flagged.
5.  Add Isolation Forest only if there is enough data and time to
    validate it.
6.  Measure alert precision/recall against planted ground truth.

### Deliverables

-   Trending topic endpoint.
-   Spike alert endpoint.
-   Admin anomaly endpoint.
-   Evaluation script.

### Exit gate

Trend and anomaly results are computed from stored events and validated
against known test cases.

------------------------------------------------------------------------

## PHASE 18 --- F8: Research assistant with retrieval and citations

**Owner:** Pinaka; Ashish owns chat UI.

### Goal

Answer user questions using stored papers/library material and show the
evidence.

### Steps

1.  Define the evidence scope: abstracts and available metadata first;
    full text only where legally and technically available.
2.  Split long text into retrievable passages if needed.
3.  Create searchable representations of passages.
4.  Receive a plain-language question.
5.  Retrieve the most relevant passages.
6.  Apply a relevance threshold.
7.  If evidence is insufficient, return an explicit
    insufficient-evidence response.
8.  Produce an answer grounded only in retrieved material.
9.  Return paper title, source, URL/DOI and retrieved passage.
10. If using a local LLM, pass retrieved passages as context and
    instruct it not to invent citations.
11. Verify that every citation maps to a retrieved record.
12. Test questions with known relevant and irrelevant evidence.

### Deliverables

-   Retrieval module.
-   Answer module.
-   Question endpoint.
-   Citations and evidence in response.
-   Citation-grounding tests.

### Exit gate

The assistant shows evidence passages and valid citations, and refuses
to overstate what the stored sources support.

------------------------------------------------------------------------

## PHASE 19 --- F9 Part A: Analytical data model and warehouse

**Owner:** Pinaka; Adarsh supplies application activity data.

### Goal

Create analysis-ready data for university-level research activity.

### Steps

1.  Define the activity events the application records.
2.  Ensure events include event type, actor, target, timestamp and
    relevant dimensions.
3.  Export selected application data into Parquet.
4.  Define analytical dimensions such as date, department, user, paper
    and topic.
5.  Define fact data such as saves, posts, comments, searches and views.
6.  Use DuckDB to query Parquet.
7.  Check row counts and data consistency against the application
    database.
8.  Document refresh steps.

### Deliverables

-   Warehouse/analytics scripts.
-   Parquet data.
-   DuckDB queries.
-   Data validation checks.

### Exit gate

Analytics queries can be rerun from documented source data and return
consistent results.

------------------------------------------------------------------------

## PHASE 20 --- F9 Part B: Institutional analytics APIs

**Owner:** Pinaka; Ashish builds charts.

### Goal

Expose institutional research metrics to the admin dashboard.

### Steps

1.  Calculate topics by department over time.
2.  Calculate cross-department interactions/collaboration where
    supported by recorded relationships.
3.  Calculate most-saved papers.
4.  Calculate most-discussed papers.
5.  Calculate engagement trends.
6.  Support university/department/topic/member filters where data
    supports them.
7.  Apply admin authorization.
8.  Return predictable JSON response formats.
9.  Test endpoints with seeded and empty datasets.

### Deliverables

-   Overview endpoint.
-   Department activity endpoint.
-   Topic trend endpoint.
-   Most-saved endpoint.
-   Most-discussed endpoint.
-   Engagement endpoint.

### Exit gate

The dashboard can obtain real analytics from warehouse queries, not
hardcoded sample arrays.

------------------------------------------------------------------------

## PHASE 21 --- Frontend foundation and shared design system

**Owner:** Roy leads; Ashish coordinates page integration.

### Goal

Establish one consistent frontend so both frontend developers can work
in parallel.

### Steps

1.  Inspect current frontend files and package configuration.
2.  Agree the route structure.
3.  Agree the global layout and navigation.
4.  Agree shared typography, spacing, colors and reusable components.
5.  Agree a common API client and base URL configuration.
6.  Agree how authentication state is stored and how protected routes
    work.
7.  Define shared loading, empty, error and success states.
8.  Create a placeholder route for every required page.
9.  Confirm the app builds before feature pages are implemented.

### Deliverables

-   Working React app.
-   Shared layout and navigation.
-   Router.
-   API client.
-   Page skeletons.

### Exit gate

All planned pages can be opened through the application navigation
without broken imports.

------------------------------------------------------------------------

## PHASE 22 --- Frontend F1--F3 implementation

**Owner:** Roy.

### Steps

1.  Registration page.
2.  Login page.
3.  Protected application routes.
4.  Profile view and edit page.
5.  Research interests and follow controls.
6.  Feed page.
7.  Create-post form.
8.  Post detail and comments.
9.  Replies and upvotes.
10. Library page.
11. Save/remove paper actions.
12. Collections and private notes.
13. Connect each page to Adarsh's agreed endpoints.
14. Test loading, error, empty and successful states.

### Deliverables

Working core platform UI connected to real APIs.

### Exit gate

A user can complete the F1--F3 journey through the browser, not only
through Swagger.

------------------------------------------------------------------------

## PHASE 23 --- Frontend F5--F9 implementation

**Owner:** Ashish.

### Steps

1.  Unified search page with one search input.
2.  Four result panels.
3.  External paper cards and source information.
4.  Library paper cards and save controls.
5.  Researcher cards and follow action.
6.  Discussion cards linking to posts.
7.  Recommendations pages/sections.
8.  Research assistant chat.
9.  Citation and retrieved-passage display.
10. Trending topic list and spike alerts.
11. Admin anomaly flags.
12. Institutional analytics dashboard.
13. Charts for department activity, topic trends and engagement.
14. Connect every screen to Pinaka's actual APIs.
15. Test loading, empty, error and successful states.

### Deliverables

Working discovery, AI and analytics UI.

### Exit gate

The F5--F9 screens display actual API results and do not rely on
hardcoded demo content.

------------------------------------------------------------------------

## PHASE 24 --- Synthetic data and ground-truth generation

**Owners:** Pinaka leads paper/activity data generation; Adarsh
validates application-compatible records; all four review.

### Goal

Create enough realistic data to test search, recommendations, trends and
analytics.

### Steps

1.  Import real external paper metadata from permitted sources.
2.  Create synthetic members across several departments.
3.  Generate synthetic posts/comments with interests aligned to
    departments.
4.  Generate follow relationships.
5.  Generate save, view and search events over a simulated six-month
    period.
6.  Vary activity over time rather than making every day identical.
7.  Plant duplicate paper records and author name variants.
8.  Plant topic spikes.
9.  Plant abnormal/spam activity examples.
10. Store ground truth separately from the generated data.
11. Clearly label synthetic members/activity in the report.
12. Ensure the schema can later accept real members without redesign.

### Scale targets from the brief

-   500+ paper records.
-   50+ synthetic members across 6+ departments.
-   2,000+ posts/comments.
-   10,000+ save/view/search events over six months.

### Deliverables

-   Reproducible data generator.
-   Seed datasets.
-   Ground-truth file.
-   Data volume summary.

### Exit gate

The generator can be rerun and produces documented, internally
consistent test data. Actual achieved counts are recorded.

------------------------------------------------------------------------

## PHASE 25 --- Integration testing and bug fixing

**Owners:** All four.

### Goal

Verify that separate modules work as one application.

### End-to-end test journey

1.  Register a new member.
2.  Log in.
3.  Complete a profile and add interests.
4.  Follow another member.
5.  Create a post and comment.
6.  Ingest scholarly paper metadata.
7.  Search a topic.
8.  Verify all four search panels.
9.  Verify duplicate merging and source listing.
10. Save a paper.
11. Verify the library save count.
12. Verify paper and researcher recommendations.
13. Verify trends and anomaly flags.
14. Ask a research assistant question.
15. Check that citations refer to retrieved evidence.
16. Open the admin analytics dashboard.

### Testing types

-   Unit tests for data transformations and algorithms.
-   API tests for request/response and authorization.
-   Integration tests for database and module interactions.
-   Browser tests for the main user journey.
-   Regression tests after fixing bugs.

### Deliverables

-   Test suite.
-   Test run instructions.
-   Bug list and fixes.
-   End-to-end verification record.

### Exit gate

The main user journey works from browser through API to database and
back.

------------------------------------------------------------------------

## PHASE 26 --- Numerical evaluation and baselines

**Owners:** Pinaka leads intelligent-feature evaluation; Adarsh
validates activity/data correctness; all review results.

### Goal

Measure quality, as explicitly required by the project brief.

### Suggested metrics

| Feature | Evaluation |
| --- | --- |
| Search | Precision@5, Recall@5, MRR |
| Duplicate detection | Precision, Recall, F1 |
| Recommendations | Hit Rate@5, Precision@5 |
| Trend alerts | Precision and Recall against planted spikes |
| Anomaly flags | Precision and Recall against planted abnormal accounts/events |
| Research assistant | Citation correctness and evidence support |
| Ingestion | Fetched, accepted, rejected, normalized and deduplicated record counts |

### Steps

1.  Create a small manually labelled query set.
2.  Label relevant papers for each query.
3.  Create known duplicate pairs.
4.  Create expected recommendation cases where possible.
5.  Create planted topic spikes and abnormal activity labels.
6.  Run the baseline.
7.  Run the proposed method.
8.  Calculate metrics using scripts.
9.  Record dataset size and test conditions.
10. Report failures and limitations honestly.

### Deliverables

-   Ground-truth test data.
-   Evaluation scripts.
-   Results table.
-   Short interpretation of results.

### Exit gate

Every reported metric can be reproduced using a documented command and
the included evaluation data.

------------------------------------------------------------------------

## PHASE 27 --- Documentation, report, demo and viva

**Owners:** All four; one member coordinates final report assembly.

### Technical report contents

1.  Problem statement and objectives.
2.  Requirements mapping F1--F9.
3.  Architecture and module diagram.
4.  Database schema and data-flow diagram.
5.  External data sources and access approach.
6.  Ingestion, raw preservation and transformation.
7.  Search and duplicate-resolution methods.
8.  Recommendation methods.
9.  Trend and anomaly methods.
10. Research assistant retrieval/citation method.
11. Warehouse and analytics design.
12. Evaluation methodology and actual results.
13. Limitations and known failures.
14. Security, privacy and deployment considerations.
15. Future improvements.

### README contents

-   Project overview.
-   Prerequisites.
-   Environment setup.
-   `.env.example` instructions.
-   Database initialization.
-   Backend run command.
-   Frontend run command.
-   Data ingestion command.
-   Synthetic data generation command.
-   Test command.
-   Evaluation reproduction command.
-   Demo login instructions using safe local seed accounts only.
-   Architecture diagram.

### Demo sequence

1.  Login.
2.  Show profile and research interests.
3.  Create a post.
4.  Search a topic and show all four panels.
5.  Save a paper.
6.  Show recommendations.
7.  Ask the research assistant a question and inspect citations.
8.  Show trends and alerts.
9.  Show institutional analytics.

### Exit gate

A teammate unfamiliar with the implementation can follow the README and
run the application and evaluation scripts.

------------------------------------------------------------------------

# 5. API ownership summary

These are proposed endpoint contracts. Confirm them in the API contract
phase before coding.

## Adarsh --- F1 to F3

``` text
POST   /auth/register
POST   /auth/login
GET    /auth/me

GET    /users
GET    /users/me
PUT    /users/me
GET    /users/{user_id}
POST   /users/{user_id}/follow
DELETE /users/{user_id}/follow

POST   /posts
GET    /posts
GET    /posts/{post_id}
PUT    /posts/{post_id}
DELETE /posts/{post_id}
POST   /posts/{post_id}/comments
POST   /posts/{post_id}/upvote
GET    /feed

POST   /library/save
GET    /library
DELETE /library/{paper_id}
POST   /library/collections
GET    /library/collections
```

## Pinaka --- F4 to F9

``` text
POST   /ingestion/run
GET    /ingestion/status

GET    /search?q=
GET    /recommendations/papers
GET    /recommendations/researchers
GET    /papers/{paper_id}/also-saved

GET    /trends
GET    /trends/alerts
GET    /admin/anomalies

POST   /assistant/ask

GET    /analytics/overview
GET    /analytics/departments
GET    /analytics/topics
GET    /analytics/most-saved
GET    /analytics/most-discussed
GET    /analytics/engagement
```

Protect admin endpoints with role checks. Do not expose ingestion
triggers or internal operational routes to ordinary users without
authorization.

------------------------------------------------------------------------

# 6. AI coding-agent workflow

Use Cursor Agent or another coding agent as a coding assistant, not as
an unsupervised project owner.

## Common prompt for every teammate

``` text
You are working in the existing Chanakya Research Commons Git repository.

My assigned role is: [Adarsh / Pinaka / Roy / Ashish].
My ownership area is: [specific modules/features].
The task for this session is: [one phase task].

First inspect the existing files, dependencies, tests, database models,
router setup, and README. Do not assume the files are empty.
Do not delete or overwrite working code.

Before editing:
1. Explain what already exists for this task.
2. List the files you intend to modify/create.
3. Identify dependencies and shared-file impact.
4. Confirm the agreed database/API contract.

Then implement only this task.
- Follow existing project conventions.
- Keep secrets out of source control.
- Validate inputs and handle errors.
- Add or update tests.
- Do not create duplicate database models or tables.
- Do not modify another person's owned files without agreement.
- Do not rewrite shared router/config files without coordination.
- Run the relevant tests and report exact output.
- List limitations and manual verification steps.

Do not commit or push unless I explicitly ask.
```

## Task discipline

-   One coding-agent task should implement one small feature or one
    tightly related group of functions.
-   Review the diff after every task.
-   Run tests before accepting changes.
-   If the agent changes files outside its ownership, inspect and revert
    unrelated edits.
-   Never let two agents edit the same shared file at the same time.

------------------------------------------------------------------------

# 7. Recommended schedule

The original submission date is 28 November 2026. A careful project
should use the phases above as the development order, but the calendar
is compressed.

| Date | Milestone |
| --- | --- |
| 23 Nov | Phases 1–6: inspection, Git, environment, contracts, schema, backend foundation |
| 24 Nov | Phases 7–10 and 21: F1–F3 backend, and the frontend foundation |
| 25 Nov | Phases 11–15: ingestion and unified search |
| 26 Nov | Phases 16–20: recommendations, trends, assistant and analytics |
| 27 Nov | Phases 22–27: frontend features, synthetic data, tests, evaluation, report and demo |
| 28 Nov | Final submission and contingency fixes |

If the team has more time, do not compress phases. Complete each exit
gate before advancing.

------------------------------------------------------------------------

# 8. Definition of done for each feature

A feature is not complete just because:

- its folder exists
- its Python file exists
- an AI agent generated code
- the endpoint returns a hardcoded success message
- the frontend has a screenshot or mockup
- a demo appears to work with one manually inserted record

A feature is complete only when:

1. The implementation exists.
2. It uses the shared database and API contract.
3. Inputs are validated.
4. Errors are handled.
5. It has a test or documented verification.
6. It is integrated into the running application.
7. Its limitations are documented.
8. Its changes are committed to the correct branch and pushed.

------------------------------------------------------------------------

# 9. Final project acceptance checklist

## Platform

-   [ ] Backend starts from documented instructions.
-   [ ] Frontend starts from documented instructions.
-   [ ] Database initializes from scratch.
-   [ ] Registration/login works.
-   [ ] Roles and authorization work.
-   [ ] Profiles and follows work.
-   [ ] Posts, comments, replies and upvotes work.
-   [ ] Personal and shared library works.

## Data layer

-   [ ] External scholarly sources are fetched through permitted APIs.
-   [ ] Raw responses are preserved unchanged.
-   [ ] Normalized records are stored.
-   [ ] Incremental ingestion avoids duplicates.
-   [ ] Parquet data is generated.
-   [ ] DuckDB can query the analytical data.

## Intelligence

-   [ ] One search query returns all four categories.
-   [ ] Duplicate papers are merged while retaining sources.
-   [ ] Keyword search works.
-   [ ] Semantic search is implemented if selected and evaluated.
-   [ ] Paper recommendations work.
-   [ ] Researcher recommendations work.
-   [ ] Cold-start recommendations work.
-   [ ] Topic trends and spikes are detected.
-   [ ] Abnormal activity is flagged with a reason.
-   [ ] Research assistant returns evidence and citations.
-   [ ] Analytics dashboard uses actual stored/warehouse data.

## Evaluation and submission

-   [ ] Ground truth exists for the evaluated features.
-   [ ] Search metrics are reproducible.
-   [ ] Duplicate-detection metrics are reproducible.
-   [ ] Recommendation metrics are reproducible.
-   [ ] Trend/anomaly metrics are reproducible.
-   [ ] Actual dataset sizes are documented.
-   [ ] Technical report is complete.
-   [ ] README setup and reproduction instructions work.
-   [ ] Demo and viva are rehearsed.

------------------------------------------------------------------------

# 10. The first three actions to take now

Do not ask the four agents to build everything at once.

1.  **Adarsh and Pinaka:** inspect `backend/app/database/models.py` and
    `backend/app/database/connection.py`, then agree on the canonical
    `users`, `papers`, `paper_sources`, `saved_papers` and
    `activity_events` schema. Add `backend/app/database/__init__.py`
    when that package is first imported.
2.  **Roy and Ashish:** inspect the frontend and agree on routes, global
    layout, shared API client and page ownership.
3.  **All four:** complete Phases 1--4 and record decisions before
    parallel implementation.

Once those are done, begin the feature phases in order. This avoids the
most common failure in a four-person AI-assisted project: lots of
generated files, but no single integrated application.
