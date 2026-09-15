import pytest

from app.services.chunking import chunk_text


def test_chunk_text_returns_empty_list_for_empty_input():
    assert chunk_text("") == []


def test_chunk_text_splits_text_with_overlap():
    text = "abcdefghij"

    chunks = chunk_text(
        text,
        chunk_size=6,
        overlap=2,
    )

    assert chunks == [
        "abcdef",
        "efghij",
    ]


def test_chunk_text_rejects_overlap_equal_to_chunk_size():
    with pytest.raises(ValueError):
        chunk_text(
            "abcdefghij",
            chunk_size=6,
            overlap=6,
        )

def test_chunk_text_rejects_non_positive_chunk_size():
    with pytest.raises(ValueError, match="chunk_size must be greater than zero"):
        chunk_text(
            "abcdefghij",
            chunk_size=0,
            overlap=0,
        )


def test_chunk_text_rejects_negative_chunk_size():
    with pytest.raises(ValueError, match="chunk_size must be greater than zero"):
        chunk_text(
            "abcdefghij",
            chunk_size=-1,
            overlap=0,
        )


def test_chunk_text_rejects_negative_overlap():
    with pytest.raises(ValueError, match="overlap cannot be negative"):
        chunk_text(
            "abcdefghij",
            chunk_size=6,
            overlap=-1,
        )