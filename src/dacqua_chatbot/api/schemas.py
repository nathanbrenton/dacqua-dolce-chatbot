"""HTTP API schemas."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """One incoming chat message."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant"]
    content: str = Field(
        min_length=1,
        max_length=16000,
    )


class ChatRequest(BaseModel):
    """Chat generation request."""

    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessageRequest] = Field(
        min_length=1,
        max_length=64,
    )
    max_new_tokens: int = Field(
        default=128,
        ge=1,
        le=512,
    )


class ChatResponse(BaseModel):
    """Normalized chat response."""

    text: str
    model: str
    device: str
    input_tokens: int
    output_tokens: int
    generation_seconds: float


class HealthResponse(BaseModel):
    """Service and inference-provider health."""

    status: Literal["ok"]
    provider: str
    model: str
    device: str
    loaded: bool
