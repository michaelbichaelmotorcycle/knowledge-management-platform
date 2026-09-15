import pytest

pytestmark = pytest.mark.skip(reason="waiting on database/infra module (track 5)")


def test_chunk_and_embedding_persisted_together(client):
    ...


def test_document_delete_cascades_to_chunks(client):
    ...