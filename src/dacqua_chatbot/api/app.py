"""FastAPI application factory."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from dacqua_chatbot.chat import ChatService
from dacqua_chatbot.inference import (
    ChatMessage,
    InferenceProvider,
    create_inference_provider,
)
from dacqua_chatbot.policies import DefaultChatPolicy
from dacqua_chatbot.tools import (
    BusinessDataProvider,
    UnavailableBusinessDataProvider,
)

from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
)


LOGGER = logging.getLogger(__name__)


def create_app(
    provider: InferenceProvider | None = None,
    business_data: BusinessDataProvider | None = None,
) -> FastAPI:
    """Create the HTTP application."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        inference = (
            provider
            if provider is not None
            else create_inference_provider()
        )

        business_provider = (
            business_data
            if business_data is not None
            else UnavailableBusinessDataProvider()
        )

        app.state.inference_provider = inference
        app.state.chat_service = ChatService(
            provider=inference,
            policy=DefaultChatPolicy(),
            business_data=business_provider,
        )

        yield

    app = FastAPI(
        title="D'Acqua Dolce Chatbot",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.get(
        "/health",
        response_model=HealthResponse,
    )
    async def health(request: Request) -> HealthResponse:
        inference: InferenceProvider = (
            request.app.state.inference_provider
        )

        status = inference.status()

        return HealthResponse(
            status="ok",
            provider=status.provider,
            model=status.model,
            device=status.device,
            loaded=status.loaded,
        )

    @app.post(
        "/v1/chat",
        response_model=ChatResponse,
    )
    async def chat(
        payload: ChatRequest,
        request: Request,
    ) -> ChatResponse:
        service: ChatService = request.app.state.chat_service

        messages = [
            ChatMessage(
                role=message.role,
                content=message.content,
            )
            for message in payload.messages
        ]

        try:
            call = partial(
                service.chat,
                messages,
                max_new_tokens=payload.max_new_tokens,
            )

            result = await run_in_threadpool(call)

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except Exception as exc:
            LOGGER.exception("Chat request failed")

            raise HTTPException(
                status_code=503,
                detail="Chat service unavailable.",
            ) from exc

        return ChatResponse(
            text=result.text,
            source=result.source,
            model=result.model,
            device=result.device,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            generation_seconds=result.generation_seconds,
            policy_rule=result.policy_rule,
            tool_status=result.tool_status,
            tool_source=result.tool_source,
        )

    return app
