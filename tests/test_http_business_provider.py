"""Tests for the D'Acqua backend business-data provider."""

import unittest

import httpx

from dacqua_chatbot.tools import (
    DacquaBackendBusinessDataProvider,
)


def catalog_payload(
    *,
    display_price: bool,
    amount_minor: int | None,
    mode: str,
    action_label: str,
) -> dict:
    return {
        "products": [
            {
                "id": "product-1",
                "name": "Origin",
                "slug": "dd5ro",
                "sku": "DD5RO",
                "description": (
                    "Reverse osmosis system."
                ),
                "product_family": (
                    "Reverse Osmosis"
                ),
                "category": (
                    "Drinking Water"
                ),
                "public_path": (
                    "/systems/dd5ro"
                ),
                "primary_image": None,
                "pricing": {
                    "mode": mode,
                    "amount_minor": (
                        amount_minor
                    ),
                    "currency": "USD",
                    "display_price": (
                        display_price
                    ),
                    "can_add_to_cart": (
                        display_price
                    ),
                    "can_checkout_online": (
                        display_price
                    ),
                    "action": (
                        "ADD_TO_CART"
                    ),
                    "action_label": (
                        action_label
                    ),
                },
            }
        ]
    }


class BackendBusinessDataProviderTests(
    unittest.TestCase
):
    def provider(
        self,
        handler,
    ) -> (
        DacquaBackendBusinessDataProvider
    ):
        transport = httpx.MockTransport(
            handler
        )

        client = httpx.Client(
            base_url="http://dacqua.test",
            transport=transport,
        )

        self.addCleanup(
            client.close
        )

        return (
            DacquaBackendBusinessDataProvider(
                "http://dacqua.test",
                client=client,
            )
        )

    def test_public_price_can_be_presented(
        self,
    ) -> None:
        def handler(
            request: httpx.Request,
        ) -> httpx.Response:
            self.assertEqual(
                request.url.path,
                "/api/catalog/products",
            )

            return httpx.Response(
                200,
                json=catalog_payload(
                    display_price=True,
                    amount_minor=12500,
                    mode="PUBLIC",
                    action_label="Add to Cart",
                ),
            )

        result = self.provider(
            handler
        ).lookup_price(
            "What is the current price "
            "of Origin?"
        )

        self.assertEqual(
            result.status,
            "success",
        )

        self.assertIn(
            "$125.00",
            result.text,
        )

    def test_hidden_price_is_never_reconstructed(
        self,
    ) -> None:
        def handler(
            request: httpx.Request,
        ) -> httpx.Response:
            return httpx.Response(
                200,
                json=catalog_payload(
                    display_price=False,
                    amount_minor=None,
                    mode="PRIVATE_QUOTE",
                    action_label=(
                        "Request a Quote"
                    ),
                ),
            )

        result = self.provider(
            handler
        ).lookup_price(
            "What is the current price "
            "of Origin?"
        )

        self.assertEqual(
            result.status,
            "restricted",
        )

        self.assertNotIn(
            "$",
            result.text,
        )

        self.assertIn(
            "Request a Quote",
            result.text,
        )

    def test_hidden_price_is_ignored_even_if_present(
        self,
    ) -> None:
        def handler(
            request: httpx.Request,
        ) -> httpx.Response:
            return httpx.Response(
                200,
                json=catalog_payload(
                    display_price=False,
                    amount_minor=987654,
                    mode="PRIVATE_QUOTE",
                    action_label=(
                        "Request a Quote"
                    ),
                ),
            )

        result = self.provider(
            handler
        ).lookup_price(
            "Price of Origin"
        )

        self.assertEqual(
            result.status,
            "restricted",
        )

        self.assertNotIn(
            "9,876",
            result.text,
        )

    def test_customer_safe_availability(
        self,
    ) -> None:
        def handler(
            request: httpx.Request,
        ) -> httpx.Response:
            if (
                request.url.path
                == "/api/catalog/products"
            ):
                return httpx.Response(
                    200,
                    json=catalog_payload(
                        display_price=True,
                        amount_minor=12500,
                        mode="PUBLIC",
                        action_label=(
                            "Add to Cart"
                        ),
                    ),
                )

            if (
                request.url.path
                == (
                    "/api/catalog/products/"
                    "dd5ro/availability"
                )
            ):
                return httpx.Response(
                    200,
                    json={
                        "status": (
                            "low_stock"
                        ),
                        "available": True,
                        "action": (
                            "AVAILABLE"
                        ),
                        "action_label": (
                            "Limited Availability"
                        ),
                    },
                )

            return httpx.Response(404)

        result = self.provider(
            handler
        ).lookup_availability(
            "Is Origin in stock?"
        )

        self.assertEqual(
            result.status,
            "success",
        )

        self.assertIn(
            "limited availability",
            result.text.lower(),
        )

        self.assertNotIn(
            "quantity",
            result.text.lower(),
        )

    def test_installation_schedule_not_invented(
        self,
    ) -> None:
        calls = 0

        def handler(
            request: httpx.Request,
        ) -> httpx.Response:
            nonlocal calls
            calls += 1

            return httpx.Response(500)

        result = self.provider(
            handler
        ).lookup_availability(
            "Can Origin be installed "
            "this week?"
        )

        self.assertEqual(
            result.status,
            "unavailable",
        )

        self.assertIn(
            "installation",
            result.text.lower(),
        )

        self.assertEqual(
            calls,
            0,
        )

    def test_backend_failure_does_not_use_model_data(
        self,
    ) -> None:
        def handler(
            request: httpx.Request,
        ) -> httpx.Response:
            return httpx.Response(503)

        result = self.provider(
            handler
        ).lookup_price(
            "Current price of Origin"
        )

        self.assertEqual(
            result.status,
            "unavailable",
        )

        self.assertIn(
            "won't",
            result.text,
        )


if __name__ == "__main__":
    unittest.main()
