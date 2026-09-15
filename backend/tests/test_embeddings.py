from app.services.embedding import generate_embeddings


def test_generate_embeddings_returns_one_vector_per_input():
    texts = [
        "PostgreSQL is the database system.",
        "The application uses semantic search.",
    ]

    embeddings = generate_embeddings(texts)

    assert len(embeddings) == 2
    assert len(embeddings[0]) == 384
    assert len(embeddings[1]) == 384


def test_generate_embeddings_returns_float_values():
    embeddings = generate_embeddings(["Test document"])

    assert len(embeddings) == 1
    assert all(
        isinstance(value, float)
        for value in embeddings[0]
    )


def test_generate_embeddings_handles_empty_input():
    embeddings = generate_embeddings([])

    assert embeddings == []
