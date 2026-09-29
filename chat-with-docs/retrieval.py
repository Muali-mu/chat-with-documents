import config
import db
import embeddings


def retrieve(query: str) -> list[dict]:
    query_embedding = embeddings.embed_query(query)

    vector_hits = db.vector_search(query_embedding, config.VECTOR_TOP_K)
    keyword_hits = db.keyword_search(query, config.KEYWORD_TOP_K)

    # merge, de-duplicating by chunk id (vector hit wins if both found it)
    merged: dict[int, dict] = {}
    for hit in keyword_hits + vector_hits:
        merged[hit["id"]] = hit
    candidates = list(merged.values())

    if not candidates:
        return []

    # rerank the merged candidate pool for final precision
    texts = [c["content"] for c in candidates]
    top_indices = embeddings.rerank(query, texts, top_k=config.RERANK_TOP_K)
    return [candidates[i] for i in top_indices]
