from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from config import document_registry, embedding, engine

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "chroma_db"
BATCH_SIZE = 500


def _display_filename(source: str) -> str:
    filename = Path(source.replace("\\", "/")).name
    return filename or "legacy-document.pdf"


def _normalise_metadata(metadata: dict[str, Any], filename: str, content_hash: str) -> dict[str, str | int | float | bool]:
    clean = {
        key: value
        for key, value in metadata.items()
        if isinstance(value, (str, int, float, bool))
    }
    clean["source"] = filename
    clean["file_name"] = filename
    clean["file_hash"] = content_hash
    return clean


def migrate() -> dict[str, int]:
    if not CHROMA_DIR.exists():
        return {"migrated_files": 0, "migrated_chunks": 0}

    legacy = Chroma(
        embedding_function=embedding,
        collection_name="MVP_RAG",
        persist_directory=str(CHROMA_DIR),
    )
    grouped: dict[str, list[tuple[str, str, dict[str, Any], list[float] | None]]] = {}
    offset = 0

    while True:
        batch = legacy.get(
            limit=BATCH_SIZE,
            offset=offset,
            include=["documents", "metadatas", "embeddings"],
        )
        batch_ids = batch.get("ids") or []
        if not batch_ids:
            break

        texts = batch.get("documents") or []
        metadatas = batch.get("metadatas") or []
        vectors = batch.get("embeddings")
        for index, legacy_id in enumerate(batch_ids):
            text = texts[index] if index < len(texts) else None
            if not isinstance(text, str) or not text.strip():
                continue
            metadata = metadatas[index] if index < len(metadatas) and metadatas[index] else {}
            source = str(metadata.get("file_name") or metadata.get("source") or legacy_id)
            vector = None
            if vectors is not None and index < len(vectors) and vectors[index] is not None:
                vector = [float(value) for value in vectors[index]]
            grouped.setdefault(source, []).append((str(legacy_id), text, metadata, vector))
        offset += len(batch_ids)

    migrated_files = 0
    migrated_chunks = 0
    for source, items in grouped.items():
        items.sort(key=lambda item: item[0])
        filename = _display_filename(source)
        hasher = hashlib.sha256(source.encode("utf-8"))
        for legacy_id, text, _, _ in items:
            hasher.update(legacy_id.encode("utf-8"))
            hasher.update(text.encode("utf-8"))
        file_hash = hasher.hexdigest()

        if document_registry.get(file_hash) is not None:
            continue

        chunk_ids = [f"{file_hash}-{index}" for index in range(len(items))]
        documents = [
            Document(
                page_content=text,
                metadata=_normalise_metadata(metadata, filename, file_hash),
            )
            for _, text, metadata, _ in items
        ]
        page_numbers = [
            metadata.get("page")
            for _, _, metadata, _ in items
            if isinstance(metadata.get("page"), int)
        ]
        page_count = max(page_numbers) + 1 if page_numbers else 0
        vectors = [vector for _, _, _, vector in items]

        if all(vector is not None for vector in vectors):
            engine.add_embeddings(
                texts=[document.page_content for document in documents],
                embeddings=[vector for vector in vectors if vector is not None],
                metadatas=[document.metadata for document in documents],
                ids=chunk_ids,
            )
        else:
            engine.add_documents(documents, ids=chunk_ids)

        document_registry.register(file_hash, filename, page_count, len(documents))
        migrated_files += 1
        migrated_chunks += len(documents)

    return {"migrated_files": migrated_files, "migrated_chunks": migrated_chunks}


if __name__ == "__main__":
    result = migrate()
    print(f"Migrated {result['migrated_chunks']} chunks across {result['migrated_files']} files from {CHROMA_DIR}.")
