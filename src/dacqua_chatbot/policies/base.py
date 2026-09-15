"""Policy contracts for chatbot request handling."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Sequence

from dacqua_chatbot.inference import ChatMessage


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Result of evaluating a chat request against server policy."""

    handled: bool
    response: str | None = None
    rule: str | None = None


class ChatPolicy(ABC):
    """Server-controlled policy interface."""

    @abstractmethod
    def evaluate(
        self,
        messages: Sequence[ChatMessage],
    ) -> PolicyDecision:
        """Evaluate whether policy should answer before inference."""
        raise NotImplementedError
