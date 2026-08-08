from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_query_creates_session_and_returns_answer(
    client: TestClient,
    mock_rag_system: MagicMock,
    sample_query: dict[str, str],
) -> None:
    response = client.post("/api/query", json=sample_query)

    assert response.status_code == 200
    assert response.json() == {
        "answer": "The course teaches retrieval-augmented generation.",
        "sources": ["Building AI Agents, lesson 1"],
        "session_id": "test-session-id",
    }
    mock_rag_system.session_manager.create_session.assert_called_once_with()
    mock_rag_system.query.assert_called_once_with(
        sample_query["query"], "test-session-id"
    )


def test_query_reuses_provided_session(
    client: TestClient,
    mock_rag_system: MagicMock,
    sample_query: dict[str, str],
) -> None:
    payload = {**sample_query, "session_id": "existing-session"}

    response = client.post("/api/query", json=payload)

    assert response.status_code == 200
    assert response.json()["session_id"] == "existing-session"
    mock_rag_system.session_manager.create_session.assert_not_called()
    mock_rag_system.query.assert_called_once_with(
        sample_query["query"], "existing-session"
    )


def test_query_rejects_missing_query(client: TestClient) -> None:
    response = client.post("/api/query", json={})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "query"]


def test_query_returns_500_when_rag_system_fails(
    client: TestClient,
    mock_rag_system: MagicMock,
    sample_query: dict[str, str],
) -> None:
    mock_rag_system.query.side_effect = RuntimeError("generation unavailable")

    response = client.post("/api/query", json=sample_query)

    assert response.status_code == 500
    assert response.json() == {"detail": "generation unavailable"}


def test_courses_returns_catalog_analytics(
    client: TestClient,
    mock_rag_system: MagicMock,
    sample_courses: dict[str, object],
) -> None:
    response = client.get("/api/courses")

    assert response.status_code == 200
    assert response.json() == sample_courses
    mock_rag_system.get_course_analytics.assert_called_once_with()


def test_courses_returns_500_when_analytics_fail(
    client: TestClient,
    mock_rag_system: MagicMock,
) -> None:
    mock_rag_system.get_course_analytics.side_effect = RuntimeError(
        "analytics unavailable"
    )

    response = client.get("/api/courses")

    assert response.status_code == 500
    assert response.json() == {"detail": "analytics unavailable"}


def test_root_returns_html(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Course Materials RAG System" in response.text
