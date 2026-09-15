"""Inference-provider contracts for the D'Acqua Dolce chatbot."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Sequence


ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """One message supplied to an inference provider."""

    role: ChatRole
    content: str


@dataclass(frozen=True, slots=True)
class GenerationResult:
    """Normalized result returned by any inference provider."""

    text: str
    model: str
    device: str
    input_tokens: int
    output_tokens: int
    generation_seconds: float


@dataclass(frozen=True, slots=True)
class InferenceStatus:
    """Provider-independent runtime status."""

    provider: str
    model: str
    device: str
    loaded: bool


class InferenceProvider(ABC):
    """Provider-independent interface for text generation."""

    @abstractmethod
    def status(self) -> InferenceStatus:
        """Return normalized provider/runtime status."""
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        max_new_tokens: int = 128,
    ) -> GenerationResult:
        """Generate one assistant response."""
        raise NotImplementedError
