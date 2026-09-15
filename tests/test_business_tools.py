"""Tests for authoritative business-data routing."""

import unittest

from dacqua_chatbot.inference import ChatMessage
from dacqua_chatbot.tools import (
    BusinessQueryRouter,
    BusinessToolResult,
    InMemoryBusinessDataProvider,
    UnavailableBusinessDataProvider,
)


class BusinessQueryRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = BusinessQueryRouter()

    def classify(self, text: str):
        return self.router.classify(
            [
                ChatMessage(
                    role="user",
                    content=text,
                )
            ]
        )

    def test_price_query(self) -> None:
        self.assertEqual(
            self.classify(
                "What is the current price of the "
                "D'Acqua Dolce Origin system?"
            ),
            "price",
        )

    def test_availability_query(self) -> None:
        self.assertEqual(
            self.classify(
                "Is the D'Acqua Dolce Origin system in stock?"
            ),
            "availability",
        )

    def test_general_water_question_is_not_business_data(
        self,
    ) -> None:
        self.assertIsNone(
            self.classify(
                "What does reverse osmosis do?"
            )
        )


class BusinessDataProviderTests(unittest.TestCase):
    def test_unavailable_price_is_safe(self) -> None:
        provider = UnavailableBusinessDataProvider()

        result = provider.lookup_price(
            "D'Acqua Dolce Origin"
        )

        self.assertEqual(
            result.status,
            "unavailable",
        )
        self.assertNotIn(
            "$",
            result.text,
        )

    def test_authoritative_result_can_be_injected(
        self,
    ) -> None:
        expected = BusinessToolResult(
            kind="price",
            status="success",
            text="Authoritative test quote.",
            source="test-authoritative-source",
        )

        provider = InMemoryBusinessDataProvider(
            prices={
                "Origin": expected,
            }
        )

        result = provider.lookup_price(
            "Current price of Origin system"
        )

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
