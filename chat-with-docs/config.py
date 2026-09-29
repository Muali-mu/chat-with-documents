import os
from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/chatdocs")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# "anthropic" (Claude, paid but cheap, best instruction-following) or
# "groq" (free, very fast, open-weight models)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
VOYAGE_EMBED_MODEL = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3-large")
VOYAGE_RERANK_MODEL = os.getenv("VOYAGE_RERANK_MODEL", "rerank-2")

CHUNK_TARGET_TOKENS = _int("CHUNK_TARGET_TOKENS", 400)
CHUNK_OVERLAP_TOKENS = _int("CHUNK_OVERLAP_TOKENS", 50)

VECTOR_TOP_K = _int("VECTOR_TOP_K", 25)
KEYWORD_TOP_K = _int("KEYWORD_TOP_K", 25)
RERANK_TOP_K = _int("RERANK_TOP_K", 8)
