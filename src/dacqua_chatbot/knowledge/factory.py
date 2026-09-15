"""Knowledge-retrieval provider configuration."""

from __future__ import annotations

import os
from pathlib import Path

from .base import KnowledgeRetriever
from .corpus import load_knowledge_corpus
from .lexical import LexicalKnowledgeRetriever


KNOWLEDGE_PROVIDER_ENV = (
    "DACQUA_KNOWLEDGE_PROVIDER"
)

KNOWLEDGE_CORPUS_ENV = (
    "DACQUA_KNOWLEDGE_CORPUS"
)


def default_corpus_path() -> Path:
    """Return the repository's default curated corpus."""

    return (
        Path(__file__).resolve().parents[3]
        / "data"
        / "knowledge"
        / "dacqua-foundation.json"
    )


def create_knowledge_retriever(
) -> KnowledgeRetriever | None:
    """Create the configured retrieval provider."""

    provider_name = os.environ.get(
        KNOWLEDGE_PROVIDER_ENV,
        "lexical",
    ).strip().lower()

    if provider_name == "disabled":
        return None

    if provider_name != "lexical":
        raise RuntimeError(
            "Unsupported knowledge provider: "
            f"{provider_name}"
        )

    configured_path = os.environ.get(
        KNOWLEDGE_CORPUS_ENV
    )

    corpus_path = (
        Path(configured_path)
        .expanduser()
        .resolve()
        if configured_path
        else default_corpus_path()
    )

    if not corpus_path.is_file():
        raise FileNotFoundError(
            "Knowledge corpus does not exist: "
            f"{corpus_path}"
        )

    documents = load_knowledge_corpus(
        corpus_path
    )

    return LexicalKnowledgeRetriever(
        documents
    )
