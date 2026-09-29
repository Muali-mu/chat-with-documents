"""
Chunks text on paragraph boundaries, packing paragraphs up to a target token
size (approximated as words / 0.75) and carrying a small overlap between
consecutive chunks so context isn't lost at the boundary.
"""
import config


def _approx_tokens(text: str) -> int:
    return int(len(text.split()) / 0.75)


def chunk_text(text: str, section_label: str) -> list[dict]:
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    chunks = []
    current: list[str] = []
    current_tokens = 0

    def flush():
        if current:
            chunks.append({"section_label": section_label, "content": "\n".join(current)})

    for para in paragraphs:
        para_tokens = _approx_tokens(para)

        if current_tokens + para_tokens > config.CHUNK_TARGET_TOKENS and current:
            flush()
            # carry overlap: keep trailing paragraphs worth ~CHUNK_OVERLAP_TOKENS
            overlap: list[str] = []
            overlap_tokens = 0
            for p in reversed(current):
                t = _approx_tokens(p)
                if overlap_tokens + t > config.CHUNK_OVERLAP_TOKENS:
                    break
                overlap.insert(0, p)
                overlap_tokens += t
            current = overlap
            current_tokens = overlap_tokens

        current.append(para)
        current_tokens += para_tokens

    flush()
    return chunks


def chunk_sections(sections: list[tuple[str, str]]) -> list[dict]:
    """sections: list of (section_label, text) from a parser. Returns flat chunk list."""
    all_chunks = []
    for label, text in sections:
        all_chunks.extend(chunk_text(text, label))
    for i, c in enumerate(all_chunks):
        c["chunk_index"] = i
    return all_chunks
