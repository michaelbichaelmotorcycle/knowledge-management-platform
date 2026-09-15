import pytest

pytestmark = pytest.mark.skip(reason="waiting on embeddings module (track 3/4)")


def test_embedding_has_expected_dimension(client):
    ...


def test_embedding_is_deterministic_for_same_input_when_mocked(client):
    ...