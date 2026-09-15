import pytest

pytestmark = pytest.mark.skip(reason="waiting on Q&A/AI integration module (track 4)")


def test_prompt_includes_retrieved_context(client):
    ...


def test_response_includes_source_attribution(client):
    ...