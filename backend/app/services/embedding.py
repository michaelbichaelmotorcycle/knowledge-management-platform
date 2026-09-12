from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = None


def _get_model():
    """Lazily initialize the embedding model so the module can be imported
    without downloading the model (e.g. in tests that mock embeddings)."""
    global _model
    if _model is None:
        _model = TextEmbedding(MODEL_NAME)
    return _model


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    model = _get_model()
    return [embedding.tolist() for embedding in model.embed(texts)]
