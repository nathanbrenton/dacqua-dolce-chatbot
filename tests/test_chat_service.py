"""Tests for chatbot orchestration."""

import unittest
from typing import Sequence

from dacqua_chatbot.chat import ChatService
from dacqua_chatbot.inference import (
    ChatMessage,
    GenerationResult,
    InferenceProvider,
    InferenceStatus,
)
from dacqua_chatbot.policies import DefaultChatPolicy


class CountingProvider(InferenceProvider):
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
            text="Model response",
            model="fake-model",
            device="cpu",
            input_tokens=10,
            output_tokens=2,
            generation_seconds=0.01,
        )


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = CountingProvider()
        self.service = ChatService(
            provider=self.provider,
            policy=DefaultChatPolicy(),
        )

    def test_normal_question_calls_model(self) -> None:
        result = self.service.chat(
            [
                ChatMessage(
                    role="user",
                    content="What does reverse osmosis do?",
                )
            ]
        )

        self.assertEqual(result.source, "model")
        self.assertEqual(self.provider.calls, 1)

    def test_price_policy_does_not_call_model(self) -> None:
        result = self.service.chat(
            [
                ChatMessage(
                    role="user",
                    content=(
                        "What is the current price of the "
                        "D'Acqua Dolce Origin system?"
                    ),
                )
            ]
        )

        self.assertEqual(result.source, "policy")
        self.assertEqual(
            result.policy_rule,
            "authoritative_pricing_required",
        )
        self.assertEqual(self.provider.calls, 0)


if __name__ == "__main__":
    unittest.main()
