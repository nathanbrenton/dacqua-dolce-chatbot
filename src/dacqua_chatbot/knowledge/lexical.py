"""Small deterministic lexical retriever.

This is intentionally dependency-free. It establishes a measurable retrieval
baseline before embeddings or vector infrastructure are introduced.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from .base import (
    KnowledgeDocument,
    KnowledgeRetriever,
    RetrievalHit,
)


_TOKEN_RE = re.compile(
    r"[a-z0-9]+"
)

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "can",
    "do",
    "does",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "the",
    "this",
    "to",
    "what",
    "which",
    "with",
    "you",
    "your",
}

_ALIASES = {
    "ro": "reverseosmosis",
    "reverseosmosis": "reverseosmosis",
    "uv": "ultraviolet",
    "hardness": "hardwater",
    "hard": "hardwater",
    "softening": "softener",
    "conditioner": "conditioning",
}


def _normalize_token(
    token: str,
) -> str:
    return _ALIASES.get(
        token,
        token,
    )


def _tokens(
    text: str,
) -> list[str]:
    lowered = (
        text.casefold()
        .replace(
            "reverse osmosis",
            "reverseosmosis",
        )
        .replace(
            "hard water",
            "hardwater",
        )
    )

    result: list[str] = []

    for token in _TOKEN_RE.findall(
        lowered
    ):
        if token in _STOP_WORDS:
            continue

        result.append(
            _normalize_token(
                token
            )
        )

    return result


class LexicalKnowledgeRetriever(
    KnowledgeRetriever
):
    """Deterministic BM25-style local retriever."""

    def __init__(
        self,
        documents: list[
            KnowledgeDocument
        ],
    ) -> None:
        self._documents = list(
            documents
        )

        self._tokens_by_id = {
            document.id: _tokens(
                " ".join(
                    (
                        document.title,
                        document.text,
                        *document.tags,
                    )
                )
            )
            for document
            in self._documents
        }

        self._document_frequency: (
            Counter[str]
        ) = Counter()

        for tokens in (
            self._tokens_by_id.values()
        ):
            self._document_frequency.update(
                set(tokens)
            )

        lengths = [
            len(tokens)
            for tokens in (
                self._tokens_by_id.values()
            )
        ]

        self._average_length = (
            sum(lengths)
            / len(lengths)
            if lengths
            else 1.0
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 3,
    ) -> list[RetrievalHit]:
        if limit < 1:
            raise ValueError(
                "Retrieval limit must "
                "be at least 1."
            )

        query_tokens = _tokens(
            query
        )

        if (
            not query_tokens
            or not self._documents
        ):
            return []

        hits: list[
            RetrievalHit
        ] = []

        document_count = len(
            self._documents
        )

        k1 = 1.5
        b = 0.75

        for document in (
            self._documents
        ):
            document_tokens = (
                self._tokens_by_id[
                    document.id
                ]
            )

            frequencies = Counter(
                document_tokens
            )

            score = 0.0
            matched: set[str] = set()

            document_length = len(
                document_tokens
            )

            for term in set(
                query_tokens
            ):
                frequency = frequencies.get(
                    term,
                    0,
                )

                if frequency <= 0:
                    continue

                matched.add(term)

                df = (
                    self._document_frequency[
                        term
                    ]
                )

                idf = math.log(
                    1
                    + (
                        document_count
                        - df
                        + 0.5
                    )
                    / (
                        df
                        + 0.5
                    )
                )

                denominator = (
                    frequency
                    + k1
                    * (
                        1
                        - b
                        + b
                        * document_length
                        / self._average_length
                    )
                )

                score += (
                    idf
                    * frequency
                    * (
                        k1
                        + 1
                    )
                    / denominator
                )

            if score <= 0:
                continue

            title_tokens = set(
                _tokens(
                    document.title
                )
            )

            title_matches = (
                set(query_tokens)
                & title_tokens
            )

            score += (
                0.35
                * len(
                    title_matches
                )
            )

            hits.append(
                RetrievalHit(
                    document=document,
                    score=round(
                        score,
                        6,
                    ),
                    matched_terms=tuple(
                        sorted(matched)
                    ),
                )
            )

        hits.sort(
            key=lambda hit: (
                -hit.score,
                hit.document.id,
            )
        )

        return hits[:limit]
