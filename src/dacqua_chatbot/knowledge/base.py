"""Provider-independent knowledge retrieval contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    """A curated document eligible for chatbot retrieval."""

    id: str
    title: str
    text: str
    source: str
    scope: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RetrievalHit:
    """One deterministic retrieval result."""

    document: KnowledgeDocument
    score: float
    matched_terms: tuple[str, ...]


class KnowledgeRetriever(ABC):
    """Provider-independent retrieval interface."""

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        limit: int = 3,
    ) -> list[RetrievalHit]:
        """Return the most relevant curated documents."""
