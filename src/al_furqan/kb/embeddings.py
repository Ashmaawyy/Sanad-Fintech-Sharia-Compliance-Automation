"""Deterministic embedding abstraction with optional transformer backends.

The hashing fallback keeps local tests and offline ingestion usable when the
optional sentence-transformers dependency or model weights are unavailable.
Production deployments can select a transformer model through the registry.
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterable


class EmbeddingModel:
    """Embed text into normalized 384-dimensional vectors."""

    AVAILABLE_MODELS = {
        "minilm": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "camelbert": "CAMeL-Lab/bert-base-arabic-camelbert-ca",
    }

    def __init__(self, model_name: str = "minilm") -> None:
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(f"Unknown embedding model: {model_name}")
        self.model_name = model_name
        self.model_path = self.AVAILABLE_MODELS[model_name]
        self.dimension = 384
        self._model = self._load_optional_transformer()
        self._token_slots: dict[str, int] = {}
        self._occupied_slots: set[int] = set()

    def _load_optional_transformer(self):
        """Load a local transformer only when the optional dependency is ready."""
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            return SentenceTransformer(self.model_path)
        except Exception:
            return None

    def embed_query(self, text: str) -> list[float]:
        """Embed one text and return a unit-normalized vector."""
        return self.embed([text])[0]

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        """Embed a batch, preserving order and returning an empty batch unchanged."""
        values = list(texts)
        if not values:
            return []
        if self._model is not None:
            vectors = self._model.encode(values, normalize_embeddings=True)
            return [[float(value) for value in vector] for vector in vectors]
        return [self._hash_embedding(value) for value in values]

    def similarity(self, first: str, second: str) -> float:
        """Return cosine similarity for two texts."""
        left = self.embed_query(first)
        right = self.embed_query(second)
        cosine = float(sum(a * b for a, b in zip(left, right)))
        first_tokens = set(self._tokens(first))
        second_tokens = set(self._tokens(second))
        overlap = len(first_tokens & second_tokens) / max(len(first_tokens), 1)
        return cosine + (0.2 * overlap)

    def _hash_embedding(self, text: str) -> list[float]:
        """Create a stable lexical/character embedding for offline operation."""
        vector = [0.0] * self.dimension
        tokens = self._tokens(text)
        for feature in tokens:
            index = self._slot_for(feature)
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            vector[0] = 1.0
            norm = 1.0
        return [value / norm for value in vector]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        """Return normalized whitespace-delimited Arabic/Unicode tokens."""
        tokens = [
            re.sub(r"[^\w\u0600-\u06ff]", "", token)
            for token in text.casefold().split()
        ]
        return [token for token in tokens if token]

    def _slot_for(self, token: str) -> int:
        """Assign each observed token a stable collision-free local slot."""
        if token in self._token_slots:
            return self._token_slots[token]
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % self.dimension
        while index in self._occupied_slots:
            index = (index + 1) % self.dimension
        self._token_slots[token] = index
        self._occupied_slots.add(index)
        return index
