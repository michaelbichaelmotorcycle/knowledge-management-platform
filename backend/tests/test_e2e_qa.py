import pytest

pytestmark = pytest.mark.skip(reason="waiting on full pipeline (all tracks) — un-skip last")

REPRESENTATIVE_QUESTIONS = [
    "What is the PTO policy?",
    "How often do passwords need to be rotated?",
    # TODO: add remaining questions from NFR-12
]


def test_representative_questions_return_cited_answers(client):
    ...