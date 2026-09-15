"""Tests for the chatbot HTTP API."""

import unittest
from typing import Sequence

from fastapi.testclient import TestClient

from dacqua_chatbot.api import create_app
from dacqua_chatbot.inference import (
    ChatMessage,
    GenerationResult,
    InferenceProvider,
    InferenceStatus,
)
from dacqua_chatbot.tools import (
    UnavailableBusinessDataProvider,
)


class FakeProvider(InferenceProvider):
    def __init__(self) -> None:
        self.calls = 0

    def status(self) -> InferenceStatus:
        return InferenceStatus(
            provider="fake",
            model="fake-model",
            device="cpu",
            loaded=self.calls > 0,
        )

    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        max_new_tokens: int = 128,
    ) -> GenerationResult:
        self.calls += 1

        return GenerationResult(
            text="Synthetic response",
            model="fake-model",
            device="cpu",
            input_tokens=12,
            output_tokens=3,
            generation_seconds=0.01,
        )


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = FakeProvider()

        self.client_context = TestClient(
            create_app(
                provider=self.provider,
                business_data=UnavailableBusinessDataProvider(),
            )
        )

        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(
            None,
            None,
            None,
        )

    def test_health(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)

    def test_normal_chat_uses_model(self) -> None:
        response = self.client.post(
            "/v1/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "What does reverse osmosis do?",
                    }
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["source"],
            "model",
        )
        self.assertEqual(self.provider.calls, 1)

    def test_price_request_uses_business_tool(self) -> None:
        response = self.client.post(
            "/v1/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "What is the current price of the "
                            "D'Acqua Dolce Origin system?"
                        ),
                    }
                ]
            },
        )

        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            body["source"],
            "tool",
        )
        self.assertEqual(
            body["tool_status"],
            "unavailable",
        )
        self.assertEqual(self.provider.calls, 0)

    def test_empty_messages_are_rejected(self) -> None:
        response = self.client.post(
            "/v1/chat",
            json={"messages": []},
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
