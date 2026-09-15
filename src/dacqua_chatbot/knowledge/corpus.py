"""Curated knowledge corpus loading."""

from __future__ import annotations

import json
from pathlib import Path

from .base import KnowledgeDocument


def load_knowledge_corpus(
    path: str | Path,
) -> list[KnowledgeDocument]:
    """Load and validate a JSON knowledge corpus."""

    corpus_path = Path(path)

    payload = json.loads(
        corpus_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(payload, dict):
        raise ValueError(
            "Knowledge corpus must be "
            "a JSON object."
        )

    raw_documents = payload.get(
        "documents"
    )

    if not isinstance(
        raw_documents,
        list,
    ):
        raise ValueError(
            "Knowledge corpus must contain "
            "a documents list."
        )

    documents: list[
        KnowledgeDocument
    ] = []

    seen_ids: set[str] = set()

    for raw in raw_documents:
        if not isinstance(raw, dict):
            raise ValueError(
                "Knowledge document must "
                "be a JSON object."
            )

        required = (
            "id",
            "title",
            "text",
            "source",
            "scope",
        )

        values: dict[str, str] = {}

        for field in required:
            value = raw.get(field)

            if (
                not isinstance(value, str)
                or not value.strip()
            ):
                raise ValueError(
                    "Knowledge document "
                    f"requires non-empty {field}."
                )

            values[field] = (
                value.strip()
            )

        document_id = values["id"]

        if document_id in seen_ids:
            raise ValueError(
                "Duplicate knowledge "
                f"document id: {document_id}"
            )

        raw_tags = raw.get(
            "tags",
            [],
        )

        if not isinstance(
            raw_tags,
            list,
        ):
            raise ValueError(
                "Knowledge document tags "
                "must be a list."
            )

        tags: list[str] = []

        for tag in raw_tags:
            if (
                not isinstance(tag, str)
                or not tag.strip()
            ):
                raise ValueError(
                    "Knowledge tags must "
                    "be non-empty strings."
                )

            tags.append(
                tag.strip()
            )

        documents.append(
            KnowledgeDocument(
                id=document_id,
                title=values["title"],
                text=values["text"],
                source=values["source"],
                scope=values["scope"],
                tags=tuple(tags),
            )
        )

        seen_ids.add(
            document_id
        )

    return documents
