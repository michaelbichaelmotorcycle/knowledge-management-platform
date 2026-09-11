from fastembed import TextEmbedding


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model = TextEmbedding(MODEL_NAME)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    return [embedding.tolist() for embedding in _model.embed(texts)]
