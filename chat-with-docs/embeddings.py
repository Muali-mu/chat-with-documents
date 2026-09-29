import voyageai

import config

_client = voyageai.Client(api_key=config.VOYAGE_API_KEY)


def embed_documents(texts: list[str]) -> list[list[float]]:
    result = _client.embed(texts, model=config.VOYAGE_EMBED_MODEL, input_type="document")
    return result.embeddings


def embed_query(text: str) -> list[float]:
    result = _client.embed([text], model=config.VOYAGE_EMBED_MODEL, input_type="query")
    return result.embeddings[0]


def rerank(query: str, documents: list[str], top_k: int) -> list[int]:
    """Returns indices into `documents`, best first."""
    result = _client.rerank(query, documents, model=config.VOYAGE_RERANK_MODEL, top_k=top_k)
    return [r.index for r in result.results]
