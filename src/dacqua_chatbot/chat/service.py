"""Provider-independent chatbot orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

from dacqua_chatbot.inference import (
    ChatMessage,
    InferenceProvider,
)
from dacqua_chatbot.knowledge import (
    KnowledgeRetriever,
    RetrievalHit,
    build_knowledge_context,
)
from dacqua_chatbot.policies import ChatPolicy
from dacqua_chatbot.tools import (
    BusinessDataProvider,
    BusinessQueryRouter,
)


ResponseSource = Literal[
    "model",
    "policy",
    "tool",
]


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
    knowledge_document_ids: tuple[str, ...] = ()


class ChatService:
    """Coordinate policy, authoritative tools, retrieval, and inference."""

    def __init__(
        self,
        provider: InferenceProvider,
        policy: ChatPolicy,
        business_data: BusinessDataProvider,
        *,
        business_router: BusinessQueryRouter | None = None,
        knowledge_retriever: KnowledgeRetriever | None = None,
        knowledge_limit: int = 3,
    ) -> None:
        if knowledge_limit < 1:
            raise ValueError(
                "knowledge_limit must be at least 1."
            )

        self.provider = provider
        self.policy = policy
        self.business_data = business_data
        self.business_router = (
            business_router
            if business_router is not None
            else BusinessQueryRouter()
        )
        self.knowledge_retriever = (
            knowledge_retriever
        )
        self.knowledge_limit = (
            knowledge_limit
        )

    @staticmethod
    def _augment_with_knowledge(
        messages: Sequence[ChatMessage],
        hits: Sequence[RetrievalHit],
    ) -> list[ChatMessage]:
        """Insert retrieved reference material before conversation turns."""

        if not hits:
            return list(messages)

        knowledge_message = ChatMessage(
            role="system",
            content=build_knowledge_context(
                hits
            ),
        )

        leading_system_messages: list[
            ChatMessage
        ] = []

        index = 0

        while (
            index < len(messages)
            and messages[index].role == "system"
        ):
            leading_system_messages.append(
                messages[index]
            )
            index += 1

        return [
            *leading_system_messages,
            knowledge_message,
            *messages[index:],
        ]

    def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        max_new_tokens: int = 128,
    ) -> ChatResult:
        """Policy-check, tool-route, retrieve, or generate."""

        if not messages:
            raise ValueError(
                "At least one chat message is required."
            )

        decision = self.policy.evaluate(
            messages
        )

        if decision.handled:
            if decision.response is None:
                raise RuntimeError(
                    "Handled policy decision requires "
                    "a response."
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

        business_kind = (
            self.business_router.classify(
                messages
            )
        )

        if business_kind is not None:
            query = (
                self.business_router
                .latest_user_text(
                    messages
                )
            )

            if business_kind == "price":
                tool_result = (
                    self.business_data
                    .lookup_price(
                        query
                    )
                )
            else:
                tool_result = (
                    self.business_data
                    .lookup_availability(
                        query
                    )
                )

            return ChatResult(
                text=tool_result.text,
                source="tool",
                model=(
                    "authoritative-business-data"
                ),
                device="server",
                input_tokens=0,
                output_tokens=0,
                generation_seconds=0.0,
                tool_status=tool_result.status,
                tool_source=tool_result.source,
            )

        generation_messages = list(
            messages
        )

        knowledge_document_ids: tuple[
            str,
            ...
        ] = ()

        if self.knowledge_retriever is not None:
            query = (
                self.business_router
                .latest_user_text(
                    messages
                )
            )

            if query:
                hits = (
                    self.knowledge_retriever
                    .search(
                        query,
                        limit=self.knowledge_limit,
                    )
                )

                if hits:
                    generation_messages = (
                        self._augment_with_knowledge(
                            messages,
                            hits,
                        )
                    )

                    knowledge_document_ids = (
                        tuple(
                            hit.document.id
                            for hit in hits
                        )
                    )

        generated = self.provider.generate(
            generation_messages,
            max_new_tokens=max_new_tokens,
        )

        return ChatResult(
            text=generated.text,
            source="model",
            model=generated.model,
            device=generated.device,
            input_tokens=generated.input_tokens,
            output_tokens=generated.output_tokens,
            generation_seconds=(
                generated.generation_seconds
            ),
            knowledge_document_ids=(
                knowledge_document_ids
            ),
        )
