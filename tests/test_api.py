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

    def status(self) -> InferenceStatus:
        return InferenceStatus(
            provider="fake",
            model="fake-model",
            device="cpu",
            loaded=True,
        )

    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        max_new_tokens: int = 128,
    ) -> GenerationResult:
        if not messages:
            raise ValueError("At least one message is required.")

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
        self.client_context = TestClient(
            create_app(FakeProvider())
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
            response.json(),
            {
                "status": "ok",
                "provider": "fake",
                "model": "fake-model",
                "device": "cpu",
                "loaded": True,
            },
        )

    def test_chat(self) -> None:
        response = self.client.post(
            "/v1/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
                "max_new_tokens": 64,
            },
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(
            body["text"],
            "Synthetic response",
        )
        self.assertEqual(
            body["model"],
            "fake-model",
        )
        self.assertEqual(
            body["output_tokens"],
            3,
        )

    def test_empty_messages_are_rejected(self) -> None:
        response = self.client.post(
            "/v1/chat",
            json={
                "messages": [],
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_unknown_fields_are_rejected(self) -> None:
        response = self.client.post(
            "/v1/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello",
                    }
                ],
                "unexpected": True,
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
