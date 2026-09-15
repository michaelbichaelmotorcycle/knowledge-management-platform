import pytest

pytestmark = pytest.mark.skip(reason="waiting on document ingestion module (track 3)")


def test_extracts_text_from_pdf(client):
    ...


def test_handles_scanned_pdf_gracefully(client):
    ...


def test_extracts_text_from_plain_text_file(client):
    ...