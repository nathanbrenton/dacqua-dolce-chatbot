"""Classification of requests requiring authoritative business data."""

from __future__ import annotations

from typing import Sequence

from dacqua_chatbot.inference import ChatMessage

from .base import BusinessQueryKind


class BusinessQueryRouter:
    """Identify requests that must use business-data tools."""

    _BRAND_TERMS = (
        "d'acqua",
        "dacqua",
        "our product",
        "our system",
        "origin system",
        "refine system",
        "clarity system",
        "silken system",
        "harmony system",
        "lucent system",
    )

    _PRICE_TERMS = (
        "current price",
        "price of",
        "how much",
        "cost of",
        "quote me",
        "quote for",
        "pricing",
    )

    _AVAILABILITY_TERMS = (
        "in stock",
        "currently available",
        "available for installation",
        "installation this week",
        "installation next week",
        "schedule installation",
        "book installation",
    )

    @staticmethod
    def latest_user_text(
        messages: Sequence[ChatMessage],
    ) -> str:
        for message in reversed(messages):
            if message.role == "user":
                return message.content.strip()

        return ""

    @staticmethod
    def _contains_any(
        text: str,
        terms: tuple[str, ...],
    ) -> bool:
        return any(term in text for term in terms)

    def classify(
        self,
        messages: Sequence[ChatMessage],
    ) -> BusinessQueryKind | None:
        text = self.latest_user_text(messages)

        if not text:
            return None

        normalized = text.casefold()

        if not self._contains_any(
            normalized,
            self._BRAND_TERMS,
        ):
            return None

        if self._contains_any(
            normalized,
            self._AVAILABILITY_TERMS,
        ):
            return "availability"

        if self._contains_any(
            normalized,
            self._PRICE_TERMS,
        ):
            return "price"

        return None
