"""
Usage:
    python ingest_cli.py /path/to/your/docs
"""
import sys
from pathlib import Path

from tqdm import tqdm

import db
import embeddings
from ingest.chunker import chunk_sections
from ingest.parser import PARSERS, parse_file


def ingest_folder(folder: str) -> None:
    db.init_pool()
    paths = [
        p for p in Path(folder).rglob("*")
        if p.is_file() and p.suffix.lower() in PARSERS
    ]
    print(f"Found {len(paths)} supported files in {folder}")

    for path in tqdm(paths, desc="Ingesting"):
        try:
            sections = parse_file(path)
            chunks = chunk_sections(sections)
            if not chunks:
                continue

            doc_id = db.insert_document(path.name, path.suffix.lower(), str(path))

            texts = [c["content"] for c in chunks]
            vectors = embeddings.embed_documents(texts)
            for c, v in zip(chunks, vectors):
                c["embedding"] = v

            db.insert_chunks(doc_id, chunks)
        except Exception as e:
            print(f"  Failed on {path.name}: {e}")

    print("Ingestion complete.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ingest_cli.py /path/to/your/docs")
        sys.exit(1)
    ingest_folder(sys.argv[1])
