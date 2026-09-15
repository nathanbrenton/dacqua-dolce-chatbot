"""Curated knowledge retrieval."""

from .base import (
    KnowledgeDocument,
    KnowledgeRetriever,
    RetrievalHit,
)
from .context import (
    build_knowledge_context,
)
from .corpus import (
    load_knowledge_corpus,
)
from .factory import (
    create_knowledge_retriever,
    default_corpus_path,
)
from .lexical import (
    LexicalKnowledgeRetriever,
)

__all__ = [
    "KnowledgeDocument",
    "KnowledgeRetriever",
    "LexicalKnowledgeRetriever",
    "RetrievalHit",
    "build_knowledge_context",
    "create_knowledge_retriever",
    "default_corpus_path",
    "load_knowledge_corpus",
]
