"""Provider-independent chatbot orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from dacqua_chatbot.inference import (
    ChatMessage,
    InferenceProvider,
)
from dacqua_chatbot.policies import ChatPolicy


ResponseSource = Literal["model", "policy"]


@dataclass(frozen=True, slots=True)
class ChatResult:
    """Normalized response from chatbot orchestration."""

    text: str
    source: ResponseSource
    model: str
    device: str
    input_tokens: int
    output_tokens: int
    generation_seconds: float
    policy_rule: str | None = None


class ChatService:
    """Coordinate policy evaluation and model inference."""

    def __init__(
        self,
        provider: InferenceProvider,
        policy: ChatPolicy,
    ) -> None:
        self.provider = provider
        self.policy = policy

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        max_new_tokens: int = 128,
    ) -> ChatResult:
        """Generate or policy-handle one chatbot response."""

        if not messages:
            raise ValueError(
                "At least one chat message is required."
            )

        decision = self.policy.evaluate(messages)

        if decision.handled:
            if decision.response is None:
                raise RuntimeError(
                    "Handled policy decision requires a response."
                )

            return ChatResult(
                text=decision.response,
                source="policy",
                model="server-policy",
                device="server",
                input_tokens=0,
                output_tokens=0,
                generation_seconds=0.0,
                policy_rule=decision.rule,
            )

        generated = self.provider.generate(
            messages,
            max_new_tokens=max_new_tokens,
        )

        return ChatResult(
            text=generated.text,
            source="model",
            model=generated.model,
            device=generated.device,
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
            generation_seconds=generated.generation_seconds,
            policy_rule=None,
        )
