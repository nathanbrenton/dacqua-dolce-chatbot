"""Tests for the deterministic RAG retrieval foundation."""

from pathlib import Path
import unittest

from dacqua_chatbot.knowledge import (
    LexicalKnowledgeRetriever,
    load_knowledge_corpus,
)


CORPUS = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "knowledge"
    / "dacqua-foundation.json"
)


class KnowledgeRetrievalTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(
        cls,
    ) -> None:
        cls.documents = (
            load_knowledge_corpus(
                CORPUS
            )
        )

        cls.retriever = (
            LexicalKnowledgeRetriever(
                cls.documents
            )
        )

    def test_unique_document_ids(
        self,
    ) -> None:
        ids = [
            document.id
            for document
            in self.documents
        ]

        self.assertEqual(
            len(ids),
            len(set(ids)),
        )

    def test_reverse_osmosis_query(
        self,
    ) -> None:
        hits = self.retriever.search(
            "How does reverse osmosis "
            "use a membrane?"
        )

        self.assertEqual(
            hits[0].document.id,
            "water-reverse-osmosis",
        )

    def test_softener_query(
        self,
    ) -> None:
        hits = self.retriever.search(
            "What helps with hard water "
            "calcium and magnesium?"
        )

        self.assertEqual(
            hits[0].document.id,
            "water-softening",
        )

    def test_uv_query(
        self,
    ) -> None:
        hits = self.retriever.search(
            "Does UV ultraviolet treatment "
            "remove dissolved salts?"
        )

        self.assertEqual(
            hits[0].document.id,
            "water-ultraviolet",
        )

    def test_conditioner_is_distinct_from_softener(
        self,
    ) -> None:
        hits = self.retriever.search(
            "Is a water conditioner the "
            "same thing as a softener?"
        )

        ids = [
            hit.document.id
            for hit in hits[:2]
        ]

        self.assertIn(
            "water-conditioning",
            ids,
        )

        self.assertIn(
            "water-softening",
            ids,
        )

    def test_unrelated_dynamic_price_query(
        self,
    ) -> None:
        hits = self.retriever.search(
            "What is today's price for Origin?"
        )

        treatment_ids = {
            "water-reverse-osmosis",
            "water-carbon-filtration",
            "water-softening",
            "water-conditioning",
            "water-ultraviolet",
        }

        self.assertFalse(
            treatment_ids
            & {
                hit.document.id
                for hit in hits
            }
        )

    def test_corpus_contains_no_currency_amounts(
        self,
    ) -> None:
        for document in self.documents:
            self.assertNotIn(
                "$",
                document.text,
            )

    def test_limit(
        self,
    ) -> None:
        hits = self.retriever.search(
            "water treatment system",
            limit=2,
        )

        self.assertLessEqual(
            len(hits),
            2,
        )

    def test_invalid_limit(
        self,
    ) -> None:
        with self.assertRaises(
            ValueError
        ):
            self.retriever.search(
                "water",
                limit=0,
            )


if __name__ == "__main__":
    unittest.main()
