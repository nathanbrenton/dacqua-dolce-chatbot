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


class FakeProvider(InferenceProvider):
    """Inference provider that never loads a real model."""

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
            create_app(self.provider)
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
        self.assertEqual(
            response.json()["provider"],
            "fake",
        )

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

        body = response.json()

        self.assertEqual(body["source"], "model")
        self.assertIsNone(body["policy_rule"])
        self.assertEqual(self.provider.calls, 1)

    def test_pricing_request_uses_policy(self) -> None:
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

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(body["source"], "policy")
        self.assertEqual(
            body["policy_rule"],
            "authoritative_pricing_required",
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
