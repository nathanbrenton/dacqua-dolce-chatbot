"""Business-data provider implementations."""

from __future__ import annotations

from collections.abc import Mapping

from .base import (
    BusinessDataProvider,
    BusinessToolResult,
)


class UnavailableBusinessDataProvider(BusinessDataProvider):
    """Safe default until authoritative systems are connected."""

    def lookup_price(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        return BusinessToolResult(
            kind="price",
            status="unavailable",
            text=(
                "Current D'Acqua Dolce pricing must come from "
                "authoritative business pricing data. That live "
                "pricing source is not connected to this chatbot "
                "request yet, so I won't invent or estimate a price."
            ),
            source="unavailable-business-data",
        )

    def lookup_availability(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        return BusinessToolResult(
            kind="availability",
            status="unavailable",
            text=(
                "Current inventory and installation availability "
                "must come from D'Acqua Dolce's authoritative "
                "business systems. That live source is not connected "
                "to this chatbot request yet."
            ),
            source="unavailable-business-data",
        )


class InMemoryBusinessDataProvider(BusinessDataProvider):
    """Test/development provider using pre-authorized responses."""

    def __init__(
        self,
        *,
        prices: Mapping[str, BusinessToolResult] | None = None,
        availability: Mapping[str, BusinessToolResult] | None = None,
    ) -> None:
        self._prices = dict(prices or {})
        self._availability = dict(availability or {})

    @staticmethod
    def _find(
        query: str,
        values: Mapping[str, BusinessToolResult],
        *,
        kind: str,
    ) -> BusinessToolResult:
        normalized = query.casefold()

        for key, result in values.items():
            if key.casefold() in normalized:
                return result

        return BusinessToolResult(
            kind=kind,  # type: ignore[arg-type]
            status="not_found",
            text=(
                "I couldn't match that request to an authoritative "
                "D'Acqua Dolce product record."
            ),
            source="in-memory-business-data",
        )

    def lookup_price(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        return self._find(
            product_query,
            self._prices,
            kind="price",
        )

    def lookup_availability(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        return self._find(
            product_query,
            self._availability,
            kind="availability",
        )
