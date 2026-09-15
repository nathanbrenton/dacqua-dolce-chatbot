"""Provider-independent chatbot orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from dacqua_chatbot.inference import (
    ChatMessage,
    InferenceProvider,
)
from dacqua_chatbot.policies import ChatPolicy
from dacqua_chatbot.tools import (
    BusinessDataProvider,
    BusinessQueryRouter,
)


ResponseSource = Literal["model", "policy", "tool"]


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
    tool_status: str | None = None
    tool_source: str | None = None


class ChatService:
    """Coordinate policy, authoritative tools, and inference."""

    def __init__(
        self,
        provider: InferenceProvider,
        policy: ChatPolicy,
        business_data: BusinessDataProvider,
        *,
        business_router: BusinessQueryRouter | None = None,
    ) -> None:
        self.provider = provider
        self.policy = policy
        self.business_data = business_data
        self.business_router = (
            business_router
            if business_router is not None
            else BusinessQueryRouter()
        )

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        max_new_tokens: int = 128,
    ) -> ChatResult:
        """Policy-check, tool-route, or generate one response."""

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

        business_kind = self.business_router.classify(
            messages
        )

        if business_kind is not None:
            query = self.business_router.latest_user_text(
                messages
            )

            if business_kind == "price":
                tool_result = self.business_data.lookup_price(
                    query
                )
            else:
                tool_result = (
                    self.business_data.lookup_availability(
                        query
                    )
                )

            return ChatResult(
                text=tool_result.text,
                source="tool",
                model="authoritative-business-data",
                device="server",
                input_tokens=0,
                output_tokens=0,
                generation_seconds=0.0,
                tool_status=tool_result.status,
                tool_source=tool_result.source,
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
        )
