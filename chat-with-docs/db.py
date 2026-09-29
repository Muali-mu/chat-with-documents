from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from pgvector.psycopg2 import register_vector
from psycopg2.pool import SimpleConnectionPool

import config

_pool: SimpleConnectionPool | None = None


def init_pool(minconn: int = 1, maxconn: int = 5) -> None:
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(minconn, maxconn, dsn=config.DATABASE_URL)


@contextmanager
def get_conn():
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def insert_document(filename: str, filetype: str, source_path: str) -> int:
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO documents (filename, filetype, source_path) VALUES (%s, %s, %s) RETURNING id",
            (filename, filetype, source_path),
        )
        return cur.fetchone()[0]


def insert_chunks(document_id: int, rows: list[dict]) -> None:
    """rows: list of {chunk_index, content, section_label, embedding}"""
    with get_conn() as conn, conn.cursor() as cur:
        psycopg2.extras.execute_batch(
            cur,
            """
            INSERT INTO chunks (document_id, chunk_index, content, section_label, embedding)
            VALUES (%(document_id)s, %(chunk_index)s, %(content)s, %(section_label)s, %(embedding)s)
            """,
            [{**r, "document_id": document_id} for r in rows],
        )


def vector_search(query_embedding: list[float], top_k: int) -> list[dict]:
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT c.id, c.content, c.section_label, d.filename,
                   1 - (c.embedding <=> %(q)s) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY c.embedding <=> %(q)s
            LIMIT %(k)s
            """,
            {"q": query_embedding, "k": top_k},
        )
        return cur.fetchall()


def keyword_search(query: str, top_k: int) -> list[dict]:
    with get_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            SELECT c.id, c.content, c.section_label, d.filename,
                   ts_rank(c.tsv, plainto_tsquery('english', %(q)s)) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.tsv @@ plainto_tsquery('english', %(q)s)
            ORDER BY score DESC
            LIMIT %(k)s
            """,
            {"q": query, "k": top_k},
        )
        return cur.fetchall()
