
import pytest

pytestmark = pytest.mark.skip(reason="waiting on document ingestion module (track 3)")


def test_upload_accepts_pdf(client):
    ...


def test_upload_rejects_invalid_file_type(client):
    ...


def test_upload_rejects_empty_file(client):
    ...