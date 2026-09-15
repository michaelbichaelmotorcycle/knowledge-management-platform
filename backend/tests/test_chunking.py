import pytest

pytestmark = pytest.mark.skip(reason="waiting on document ingestion module (track 3)")


def test_chunks_are_roughly_target_size(client):
    ...


def test_short_document_produces_at_least_one_chunk(client):
    ...


def test_long_document_produces_expected_chunk_count(client):
    ...