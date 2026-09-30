from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from math import fsum, sqrt
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class CacheEntry:
    embedding: tuple[float, ...]
    response: dict[str, object]
    created_at: float


class SemanticResponseCache:
    def __init__(
        self,
        similarity_threshold: float = 0.98,
        ttl_seconds: int = 3600,
        max_entries: int = 256,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._entries: list[CacheEntry] = []
        self._lock = Lock()

    def lookup(self, embedding: list[float]) -> dict[str, object] | None:
        query_vector = tuple(embedding)
        now = monotonic()
        with self._lock:
            self._remove_expired(now)
            best_entry: CacheEntry | None = None
            best_similarity = self.similarity_threshold
            for entry in self._entries:
                similarity = self._cosine_similarity(query_vector, entry.embedding)
                if similarity >= best_similarity:
                    best_entry = entry
                    best_similarity = similarity
            return deepcopy(best_entry.response) if best_entry is not None else None

    def store(self, embedding: list[float], response: dict[str, object]) -> None:
        now = monotonic()
        query_vector = tuple(embedding)
        with self._lock:
            self._remove_expired(now)
            self._entries.append(CacheEntry(query_vector, deepcopy(response), now))
            if len(self._entries) > self.max_entries:
                del self._entries[:len(self._entries) - self.max_entries]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def _remove_expired(self, now: float) -> None:
        self._entries = [
            entry for entry in self._entries
            if now - entry.created_at < self.ttl_seconds
        ]

    @staticmethod
    def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        if len(left) != len(right) or not left:
            return 0.0
        left_norm = sqrt(fsum(value * value for value in left))
        right_norm = sqrt(fsum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        dot_product = fsum(a * b for a, b in zip(left, right))
        return dot_product / (left_norm * right_norm)


semantic_cache = SemanticResponseCache()
