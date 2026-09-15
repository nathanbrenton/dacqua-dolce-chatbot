"""Authoritative business data from the primary D'Acqua backend."""

from __future__ import annotations

from decimal import Decimal
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from .base import (
    BusinessDataProvider,
    BusinessToolResult,
)


class DacquaBackendBusinessDataProvider(
    BusinessDataProvider
):
    """Read customer-safe business data from the D'Acqua API."""

    _INSTALLATION_TERMS = (
        "installation",
        "install this",
        "install it",
        "installed this",
        "installation this",
        "installation next",
        "schedule",
        "appointment",
        "book installation",
    )

    _FAMILY_ALIASES = {
        "origin": (
            "reverse osmosis",
            "reverse_osmosis",
        ),
        "source": (
            "reverse osmosis",
            "reverse_osmosis",
        ),
        "pure": (
            "reverse osmosis",
            "reverse_osmosis",
        ),
        "clarity": (
            "carbon",
        ),
        "refine": (
            "carbon",
        ),
        "silken": (
            "softener",
            "softening",
        ),
        "smooth": (
            "softener",
            "softening",
        ),
        "serein": (
            "softener",
            "softening",
        ),
        "harmony": (
            "conditioner",
            "conditioning",
        ),
        "balance": (
            "conditioner",
            "conditioning",
        ),
        "lucent": (
            "ultraviolet",
            "uv",
        ),
    }

    def __init__(
        self,
        base_url: str,
        *,
        timeout_seconds: float = 5.0,
        client: httpx.Client | None = None,
    ) -> None:
        normalized = base_url.rstrip("/")
        parsed = urlparse(normalized)

        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
        ):
            raise ValueError(
                "D'Acqua backend URL must be an HTTP or HTTPS URL."
            )

        self.base_url = normalized
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _get(
        self,
        path: str,
    ) -> httpx.Response:
        if self._client is not None:
            return self._client.get(path)

        with httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            follow_redirects=False,
        ) as client:
            return client.get(path)

    def _catalog_products(
        self,
    ) -> list[dict[str, Any]]:
        response = self._get(
            "/api/catalog/products"
        )
        response.raise_for_status()

        payload = response.json()

        if isinstance(payload, list):
            products = payload

        elif isinstance(payload, dict):
            products = payload.get("products", [])

        else:
            raise ValueError(
                "Invalid D'Acqua catalog response."
            )

        if not isinstance(products, list):
            raise ValueError(
                "Invalid D'Acqua product collection."
            )

        return [
            product
            for product in products
            if isinstance(product, dict)
        ]

    @classmethod
    def _alias_score(
        cls,
        normalized_query: str,
        product: dict[str, Any],
    ) -> int:
        product_family = product.get(
            "product_family"
        )

        if not isinstance(product_family, str):
            return 0

        family = product_family.casefold()

        for alias, family_terms in (
            cls._FAMILY_ALIASES.items()
        ):
            if alias not in normalized_query:
                continue

            if any(
                term in family
                for term in family_terms
            ):
                return 300

        return 0

    @classmethod
    def _match_product(
        cls,
        query: str,
        products: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        normalized = query.casefold()

        ranked: list[
            tuple[int, dict[str, Any]]
        ] = []

        for product in products:
            score = cls._alias_score(
                normalized,
                product,
            )

            fields = (
                (1000, product.get("sku")),
                (900, product.get("slug")),
                (800, product.get("name")),
                (
                    400,
                    product.get(
                        "product_family"
                    ),
                ),
            )

            for weight, value in fields:
                if not isinstance(value, str):
                    continue

                candidate = (
                    value.strip().casefold()
                )

                if (
                    candidate
                    and candidate in normalized
                ):
                    score = max(
                        score,
                        weight,
                    )

            if score:
                ranked.append(
                    (score, product)
                )

        if not ranked:
            return None

        ranked.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        top_score = ranked[0][0]

        matches = [
            product
            for score, product in ranked
            if score == top_score
        ]

        if len(matches) != 1:
            return None

        return matches[0]

    @staticmethod
    def _not_found(
        kind: str,
    ) -> BusinessToolResult:
        return BusinessToolResult(
            kind=kind,  # type: ignore[arg-type]
            status="not_found",
            text=(
                "I couldn't uniquely match that request "
                "to a D'Acqua Dolce product. Please "
                "specify the product name or SKU."
            ),
            source=(
                "dacqua-backend-public-catalog"
            ),
        )

    @staticmethod
    def _unavailable(
        kind: str,
    ) -> BusinessToolResult:
        return BusinessToolResult(
            kind=kind,  # type: ignore[arg-type]
            status="unavailable",
            text=(
                "The authoritative D'Acqua Dolce "
                "business-data service is temporarily "
                "unavailable, so I won't guess or "
                "invent current information."
            ),
            source=(
                "dacqua-backend-public-catalog"
            ),
        )

    @staticmethod
    def _format_price(
        amount_minor: int,
        currency: str,
    ) -> str:
        amount = (
            Decimal(amount_minor)
            / Decimal(100)
        )

        if currency.upper() == "USD":
            return f"${amount:,.2f}"

        return (
            f"{currency.upper()} "
            f"{amount:,.2f}"
        )

    def lookup_price(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        try:
            products = self._catalog_products()

            product = self._match_product(
                product_query,
                products,
            )

            if product is None:
                return self._not_found(
                    "price"
                )

            name = str(
                product.get("name")
                or "this system"
            )

            pricing = product.get("pricing")

            if not isinstance(pricing, dict):
                raise ValueError(
                    "Catalog product has no "
                    "pricing decision."
                )

            display_price = (
                pricing.get("display_price")
                is True
            )

            amount_minor = pricing.get(
                "amount_minor"
            )

            currency = pricing.get(
                "currency"
            )

            if display_price:
                if (
                    not isinstance(
                        amount_minor,
                        int,
                    )
                    or not isinstance(
                        currency,
                        str,
                    )
                ):
                    raise ValueError(
                        "Displayable price is "
                        "missing amount/currency."
                    )

                formatted = self._format_price(
                    amount_minor,
                    currency,
                )

                return BusinessToolResult(
                    kind="price",
                    status="success",
                    text=(
                        "The current publicly "
                        "displayable price for "
                        f"{name} is {formatted}."
                    ),
                    source=(
                        "dacqua-backend-"
                        "public-catalog"
                    ),
                )

            action_label = pricing.get(
                "action_label"
            )

            if not isinstance(
                action_label,
                str,
            ):
                action_label = (
                    "Request a Quote"
                )

            return BusinessToolResult(
                kind="price",
                status="restricted",
                text=(
                    f"Pricing for {name} is not "
                    "publicly displayed in this "
                    f"channel. {action_label}."
                ),
                source=(
                    "dacqua-backend-public-catalog"
                ),
            )

        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            ValueError,
        ):
            return self._unavailable(
                "price"
            )

    def lookup_availability(
        self,
        product_query: str,
    ) -> BusinessToolResult:
        normalized = (
            product_query.casefold()
        )

        if any(
            term in normalized
            for term in self._INSTALLATION_TERMS
        ):
            return BusinessToolResult(
                kind="availability",
                status="unavailable",
                text=(
                    "Current installation scheduling "
                    "is not yet available through the "
                    "authoritative chatbot interface. "
                    "I won't guess whether an "
                    "installation slot is available."
                ),
                source=(
                    "dacqua-backend-no-"
                    "installation-scheduling"
                ),
            )

        try:
            products = self._catalog_products()

            product = self._match_product(
                product_query,
                products,
            )

            if product is None:
                return self._not_found(
                    "availability"
                )

            slug = product.get("slug")

            if not isinstance(slug, str):
                raise ValueError(
                    "Catalog product has no slug."
                )

            name = str(
                product.get("name")
                or "this system"
            )

            response = self._get(
                "/api/catalog/products/"
                + quote(
                    slug,
                    safe="",
                )
                + "/availability"
            )

            if response.status_code == 404:
                return self._not_found(
                    "availability"
                )

            response.raise_for_status()

            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError(
                    "Invalid availability response."
                )

            state = payload.get("status")

            action_label = payload.get(
                "action_label"
            )

            if state == "in_stock":
                text = (
                    f"{name} is currently "
                    "shown as available."
                )

            elif state == "low_stock":
                text = (
                    f"{name} currently has "
                    "limited availability."
                )

            elif state == "backordered":
                text = (
                    f"{name} is currently "
                    "shown as backordered."
                )

            elif state == "unavailable":
                text = (
                    f"{name} is currently "
                    "shown as unavailable."
                )

            elif state == "contact":
                label = (
                    action_label
                    if isinstance(
                        action_label,
                        str,
                    )
                    else (
                        "Contact for Availability"
                    )
                )

                text = (
                    f"Availability for {name} "
                    "requires confirmation. "
                    f"{label}."
                )

            else:
                raise ValueError(
                    "Unknown availability state."
                )

            return BusinessToolResult(
                kind="availability",
                status="success",
                text=text,
                source=(
                    "dacqua-backend-public-catalog"
                ),
            )

        except (
            httpx.HTTPError,
            KeyError,
            TypeError,
            ValueError,
        ):
            return self._unavailable(
                "availability"
            )
