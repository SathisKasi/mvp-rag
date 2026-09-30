from __future__ import annotations

from datetime import datetime
from typing import TypedDict

from sqlalchemy import Engine, URL, create_engine, text


class DocumentRecord(TypedDict):
    id: str
    filename: str
    pages: int
    chunks: int
    uploaded_at: str


class DocumentRegistry:
    def __init__(self, database_url: URL) -> None:
        self._engine: Engine = create_engine(database_url, pool_pre_ping=True)
        with self._engine.begin() as connection:
            connection.execute(text(
                """
                CREATE TABLE IF NOT EXISTS rag_documents (
                    content_hash CHAR(64) PRIMARY KEY,
                    filename TEXT NOT NULL,
                    page_count INTEGER NOT NULL CHECK (page_count >= 0),
                    chunk_count INTEGER NOT NULL CHECK (chunk_count >= 0),
                    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            ))

    def get(self, content_hash: str) -> DocumentRecord | None:
        with self._engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT content_hash, filename, page_count, chunk_count, uploaded_at
                    FROM rag_documents
                    WHERE content_hash = :content_hash
                    """
                ),
                {"content_hash": content_hash},
            ).mappings().first()
        return self._to_record(row) if row is not None else None

    def list(self) -> list[DocumentRecord]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                text(
                    """
                    SELECT content_hash, filename, page_count, chunk_count, uploaded_at
                    FROM rag_documents
                    ORDER BY uploaded_at DESC, filename ASC
                    """
                )
            ).mappings().all()
        return [self._to_record(row) for row in rows]

    def register(self, content_hash: str, filename: str, pages: int, chunks: int) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO rag_documents (content_hash, filename, page_count, chunk_count)
                    VALUES (:content_hash, :filename, :pages, :chunks)
                    ON CONFLICT (content_hash) DO UPDATE SET
                        filename = EXCLUDED.filename,
                        page_count = EXCLUDED.page_count,
                        chunk_count = EXCLUDED.chunk_count,
                        uploaded_at = CURRENT_TIMESTAMP
                    """
                ),
                {
                    "content_hash": content_hash,
                    "filename": filename,
                    "pages": pages,
                    "chunks": chunks,
                },
            )

    def delete(self, content_hash: str) -> bool:
        with self._engine.begin() as connection:
            result = connection.execute(
                text("DELETE FROM rag_documents WHERE content_hash = :content_hash"),
                {"content_hash": content_hash},
            )
        return result.rowcount > 0

    @staticmethod
    def _to_record(row: object) -> DocumentRecord:
        record = row  # SQLAlchemy RowMapping
        uploaded_at = record["uploaded_at"]
        if isinstance(uploaded_at, datetime):
            uploaded_at = uploaded_at.isoformat()
        return {
            "id": str(record["content_hash"]).strip(),
            "filename": str(record["filename"]),
            "pages": int(record["page_count"]),
            "chunks": int(record["chunk_count"]),
            "uploaded_at": str(uploaded_at),
        }

