"""Local Hugging Face Transformers inference provider."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Sequence

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .base import (
    ChatMessage,
    GenerationResult,
    InferenceProvider,
    InferenceStatus,
)


MODEL_PATH_ENV = "DACQUA_MODEL_PATH"


class TransformersProvider(InferenceProvider):
    """Run a local causal language model through Transformers."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        device: str | None = None,
    ) -> None:
        self.model_path = Path(model_path).expanduser().resolve()

        if not self.model_path.is_dir():
            raise FileNotFoundError(
                f"Model directory does not exist: {self.model_path}"
            )

        self._device = self._resolve_device(device)
        self._tokenizer = None
        self._model = None
        self._load_seconds: float | None = None

    @classmethod
    def from_environment(cls) -> "TransformersProvider":
        """Create a provider using DACQUA_MODEL_PATH."""

        model_path = os.environ.get(MODEL_PATH_ENV)

        if not model_path:
            raise RuntimeError(
                f"{MODEL_PATH_ENV} must point to a local model directory."
            )

        return cls(model_path)

    @staticmethod
    def _resolve_device(requested: str | None) -> torch.device:
        if requested is None:
            requested = (
                "mps"
                if torch.backends.mps.is_available()
                else "cpu"
            )

        if requested == "mps" and not torch.backends.mps.is_available():
            raise RuntimeError(
                "MPS was requested but is not available."
            )

        return torch.device(requested)

    @property
    def device(self) -> str:
        return str(self._device)

    @property
    def model_name(self) -> str:
        return self.model_path.name

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    @property
    def load_seconds(self) -> float | None:
        return self._load_seconds

    def status(self) -> InferenceStatus:
        """Return provider status without forcing model loading."""

        return InferenceStatus(
            provider="transformers",
            model=self.model_name,
            device=self.device,
            loaded=self.is_loaded,
        )

    def load(self) -> None:
        """Load tokenizer and model entirely from local files."""

        if self.is_loaded:
            return

        started = time.perf_counter()

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            local_files_only=True,
        )

        model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            local_files_only=True,
            torch_dtype="auto",
        )

        model.to(self._device)
        model.eval()

        self._tokenizer = tokenizer
        self._model = model
        self._load_seconds = time.perf_counter() - started

    def _render_prompt(
        self,
        messages: Sequence[ChatMessage],
    ) -> str:
        if self._tokenizer is None:
            raise RuntimeError("Provider is not loaded.")

        chat = [
            {
                "role": message.role,
                "content": message.content,
            }
            for message in messages
        ]

        try:
            return self._tokenizer.apply_chat_template(
                chat,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            return self._tokenizer.apply_chat_template(
                chat,
                tokenize=False,
                add_generation_prompt=True,
            )

    def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        max_new_tokens: int = 128,
    ) -> GenerationResult:
        """Generate a deterministic local response."""

        if not messages:
            raise ValueError("At least one chat message is required.")

        if max_new_tokens < 1:
            raise ValueError("max_new_tokens must be at least 1.")

        self.load()

        if self._tokenizer is None or self._model is None:
            raise RuntimeError("Provider failed to load.")

        prompt = self._render_prompt(messages)

        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
        )

        inputs = {
            name: tensor.to(self._device)
            for name, tensor in inputs.items()
        }

        input_tokens = int(inputs["input_ids"].shape[-1])

        started = time.perf_counter()

        with torch.inference_mode():
            output = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        generation_seconds = time.perf_counter() - started

        generated_ids = output[0, input_tokens:]
        output_tokens = int(generated_ids.shape[-1])

        text = self._tokenizer.decode(
            generated_ids,
            skip_special_tokens=True,
        ).strip()

        return GenerationResult(
            text=text,
            model=self.model_name,
            device=self.device,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            generation_seconds=generation_seconds,
        )
