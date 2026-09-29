import anthropic
from groq import Groq

import config

_anthropic_client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY) if config.ANTHROPIC_API_KEY else None
_groq_client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None

SYSTEM_PROMPT = """You are a precise assistant that answers questions using ONLY the \
document excerpts provided below. Rules:

1. Base your answer strictly on the provided excerpts. Do not use outside knowledge.
2. After every factual claim, cite the source in the form (filename, section_label).
3. If the excerpts do not contain enough information to answer, say so plainly \
instead of guessing.
4. Be concise and direct. Do not pad the answer with generic commentary.
"""


def _format_context(chunks: list[dict]) -> str:
    blocks = []
    for c in chunks:
        blocks.append(
            f"[Source: {c['filename']} | {c.get('section_label') or 'N/A'}]\n{c['content']}"
        )
    return "\n\n---\n\n".join(blocks)


def _answer_with_anthropic(user_message: str) -> str:
    if _anthropic_client is None:
        raise RuntimeError("ANTHROPIC_API_KEY is not set but LLM_PROVIDER=anthropic")
    response = _anthropic_client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _answer_with_groq(user_message: str) -> str:
    if _groq_client is None:
        raise RuntimeError("GROQ_API_KEY is not set but LLM_PROVIDER=groq")
    response = _groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    return response.choices[0].message.content


def answer_question(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I couldn't find anything relevant to that question in the ingested documents."

    context = _format_context(chunks)
    user_message = f"Document excerpts:\n\n{context}\n\nQuestion: {question}"

    if config.LLM_PROVIDER == "groq":
        return _answer_with_groq(user_message)
    return _answer_with_anthropic(user_message)
