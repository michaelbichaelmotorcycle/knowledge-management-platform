from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User
from app.services.auth import get_current_user, get_db


def test_upload_txt_file_successfully():
    mock_db = MagicMock()
    mock_user = User(
        id=1,
        username="testuser",
        hashed_password="test-hash",
        role="user",
        disabled=False,
    )

    with (
        patch("app.api.documents.generate_embeddings") as mock_embeddings,
        TestClient(app) as client,
    ):
        mock_embeddings.return_value = [[0.1] * 384, [0.2] * 384]

        def override_get_db():
            yield mock_db

        def override_get_current_user():
            return mock_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = client.post(
                "/documents/upload",
                files={
                    "file": (
                        "test.txt",
                        b"A" * 600,
                        "text/plain",
                    )
                },
            )

            assert response.status_code == 200

            data = response.json()
            assert data["title"] == "test.txt"
            assert data["chunks_created"] == 2
            assert data["message"] == "Document uploaded successfully"

            assert mock_db.add.call_count == 3
            assert mock_db.commit.call_count == 2

        finally:
            app.dependency_overrides.clear()


def test_upload_rejects_unsupported_file_type():
    mock_db = MagicMock()
    mock_user = User(
        id=1,
        username="testuser",
        hashed_password="test-hash",
        role="user",
        disabled=False,
    )

    with TestClient(app) as client:

        def override_get_db():
            yield mock_db

        def override_get_current_user():
            return mock_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = client.post(
                "/documents/upload",
                files={
                    "file": (
                        "test.docx",
                        b"not a supported file",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
            )

            assert response.status_code == 400
            assert response.json()["detail"] == (
                "Only .txt and .pdf files are supported"
            )

        finally:
            app.dependency_overrides.clear()


def test_upload_rejects_invalid_utf8():
    mock_db = MagicMock()
    mock_user = User(
        id=1,
        username="testuser",
        hashed_password="test-hash",
        role="user",
        disabled=False,
    )

    with TestClient(app) as client:

        def override_get_db():
            yield mock_db

        def override_get_current_user():
            return mock_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user

        try:
            response = client.post(
                "/documents/upload",
                files={
                    "file": (
                        "test.txt",
                        b"\xff\xfe\xfd",
                        "text/plain",
                    )
                },
            )

            assert response.status_code == 400
            assert response.json()["detail"] == (
                "Only UTF-8 text files are supported"
            )

        finally:
            app.dependency_overrides.clear()
