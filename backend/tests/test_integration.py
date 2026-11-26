import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.assistant.retrieval import retrieve_evidence
from app.database.connection import Base, get_db
from app.database.models import ResearchPaper
from app.ingestion import routes as ingestion_routes
from app.ingestion.pdfs import scan_local_pdfs
import main

app = main.app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'integration.db'}",
        connect_args={"check_same_thread": False},
    )
    testing_sessions = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=test_engine)
    monkeypatch.setattr(main, "engine", test_engine)

    def override_get_db():
        db = testing_sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.testing_sessions = testing_sessions
        yield test_client
    app.dependency_overrides.clear()
    test_engine.dispose()


def register_user(client, username, email):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "StrongPassword123!",
            "full_name": username.title(),
            "role": "researcher",
        },
    )
    assert response.status_code == 201, response.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_profiles_posts_library_and_research_apis(client):
    headers = register_user(client, "researcher_one", "one@example.org")
    other_headers = register_user(client, "researcher_two", "two@example.org")

    profile = client.put(
        "/api/v1/users/me",
        headers=headers,
        json={
            "full_name": "Researcher One",
            "department": "Computer Science",
            "bio": "Studies data science.",
            "interests": ["data science"],
        },
    )
    assert profile.status_code == 200, profile.text
    assert profile.json()["interests"] == ["data science"]

    directory = client.get("/api/v1/users", headers=headers)
    assert directory.status_code == 200
    assert all("email" not in user for user in directory.json()["users"])

    other_id = next(
        user["id"]
        for user in directory.json()["users"]
        if user["username"] == "researcher_two"
    )
    assert client.post(
        f"/api/v1/users/{other_id}/follow",
        headers=headers,
    ).status_code == 200

    post = client.post(
        "/api/v1/posts",
        headers=headers,
        json={"body": "A research question", "tags": ["data"]},
    )
    assert post.status_code == 201, post.text
    post_id = post.json()["id"]
    assert client.get("/api/v1/feed", headers=headers).json()["posts"][0]["body"] == "A research question"
    assert client.post(
        f"/api/v1/posts/{post_id}/comments",
        headers=other_headers,
        json={"body": "A useful comment"},
    ).status_code == 201
    assert client.post(
        f"/api/v1/posts/{post_id}/upvote",
        headers=other_headers,
    ).json()["upvoted"] is True

    db = client.testing_sessions()
    db.add(ResearchPaper(
        paper_id="paper_test_001",
        source="local_pdf",
        title="Data Science in Research",
        abstract="This paper studies data science methods.",
        authors=[{"name": "Researcher One"}],
        topics=["data science"],
        publication_year=2025,
        citation_count=10,
    ))
    db.commit()
    db.close()

    assert client.get(
        "/api/v1/search",
        params={"query": "data science"},
        headers=headers,
    ).json()["total"] == 1
    assert client.post(
        "/api/v1/library/save",
        headers=headers,
        json={"paper_id": "paper_test_001"},
    ).status_code == 201
    assert len(client.get("/api/v1/library", headers=headers).json()["papers"]) == 1
    assert client.post(
        "/api/v1/library/collections",
        headers=headers,
        json={"name": "Project reading"},
    ).status_code == 201
    assert client.get(
        "/api/v1/recommendations/papers",
        headers=headers,
    ).status_code == 200
    assert client.get("/api/v1/trends/topics", headers=headers).status_code == 200
    assert client.get("/api/v1/trends/timeline", headers=headers).status_code == 200
    assert client.get("/api/v1/analytics/dashboard", headers=headers).status_code == 200


def test_local_pdf_scan_reports_corrupt_documents(tmp_path):
    pdf_folder = tmp_path / "research_papers"
    pdf_folder.mkdir()
    (pdf_folder / "broken.pdf").write_bytes(b"not a PDF")

    result = scan_local_pdfs(pdf_folder)

    assert result["records"] == []
    assert result["failures"]
    assert result["failures"][0]["file"] == "broken.pdf"
    assert str(pdf_folder) not in result["failures"][0]["error"]


def test_frontend_cors_preflight(client):
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_local_pdf_ingestion_search_and_authenticated_download(
    client,
    tmp_path,
    monkeypatch,
):
    from pypdf import PdfWriter
    from pypdf.generic import (
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    pdf_folder = tmp_path / "research_papers"
    pdf_folder.mkdir()
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): font_ref,
        }),
    })
    content = DecodedStreamObject()
    content.set_data(
        b"BT /F1 14 Tf 50 700 Td (Academic Research Sample) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(content)
    writer.add_metadata({
        "/Title": "Academic Research Sample",
        "/Author": "Researcher One",
    })
    with (pdf_folder / "sample.pdf").open("wb") as file:
        writer.write(file)

    monkeypatch.setattr(ingestion_routes, "PDF_STORAGE_DIR", pdf_folder)
    headers = register_user(client, "pdf_researcher", "pdf@example.org")
    response = client.post(
        "/api/v1/ingestion/local-pdfs",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["files_ingested"] == 1

    papers = client.get("/api/v1/papers", headers=headers).json()["items"]
    assert len(papers) == 1
    paper = papers[0]
    assert paper["title"] == "Academic Research Sample"
    assert str(pdf_folder) not in response.text
    assert str(pdf_folder) not in str(paper)

    search = client.get(
        "/api/v1/search",
        params={"query": "academic research sample"},
        headers=headers,
    )
    assert search.status_code == 200
    assert search.json()["total"] == 1
    evidence = retrieve_evidence(
        papers=papers,
        query="academic research",
        mode="keyword",
    )
    assert evidence["evidence_count"] > 0

    download = client.get(paper["pdf_url"], headers=headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
