"""Smoke-test the chatbot against a live D'Acqua backend."""

from __future__ import annotations

import os

import httpx

from dacqua_chatbot.tools import (
    DacquaBackendBusinessDataProvider,
)


def products_from_payload(
    payload,
):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        products = payload.get(
            "products",
            [],
        )

        if isinstance(products, list):
            return products

    return []


def main() -> None:
    base_url = os.environ[
        "DACQUA_BACKEND_BASE_URL"
    ].rstrip("/")

    response = httpx.get(
        base_url
        + "/api/catalog/products",
        timeout=5.0,
    )

    response.raise_for_status()

    products = products_from_payload(
        response.json()
    )

    if not products:
        raise RuntimeError(
            "Live catalog contains no products."
        )

    product = products[0]

    query_name = (
        product.get("sku")
        or product.get("slug")
        or product.get("name")
    )

    if not isinstance(
        query_name,
        str,
    ):
        raise RuntimeError(
            "First live catalog product "
            "has no usable identifier."
        )

    provider = (
        DacquaBackendBusinessDataProvider(
            base_url
        )
    )

    print(
        "===== LIVE PRODUCT ====="
    )
    print(
        "name:",
        product.get("name"),
    )
    print(
        "slug:",
        product.get("slug"),
    )
    print(
        "sku:",
        product.get("sku"),
    )

    print()
    print(
        "===== LIVE PRICE TOOL ====="
    )

    price = provider.lookup_price(
        f"What is the current price "
        f"of {query_name}?"
    )

    print(price)

    if price.status not in {
        "success",
        "restricted",
    }:
        raise RuntimeError(
            "Live price lookup did not "
            "return an authoritative result."
        )

    print()
    print(
        "===== LIVE AVAILABILITY TOOL ====="
    )

    availability = (
        provider.lookup_availability(
            f"Is {query_name} in stock?"
        )
    )

    print(availability)

    if availability.status != "success":
        raise RuntimeError(
            "Live availability lookup "
            "did not return an "
            "authoritative result."
        )

    print()
    print(
        "PASS: live D'Acqua business "
        "data integration"
    )


if __name__ == "__main__":
    main()
