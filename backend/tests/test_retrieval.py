import pytest

pytestmark = pytest.mark.skip(reason="waiting on RAG/semantic search module (track 3)")


def test_known_query_returns_known_chunk(client):
    ...


def test_empty_query_handled_gracefully(client):
    ...


def test_similarity_ranking_orders_results_correctly(client):
    ...