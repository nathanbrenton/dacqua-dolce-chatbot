"""Inference-provider selection."""

import os

from .base import InferenceProvider
from .transformers_provider import TransformersProvider


PROVIDER_ENV = "DACQUA_INFERENCE_PROVIDER"


def create_inference_provider() -> InferenceProvider:
    """Create the configured inference provider."""

    provider_name = os.environ.get(
        PROVIDER_ENV,
        "transformers",
    ).strip().lower()

    if provider_name == "transformers":
        return TransformersProvider.from_environment()

    raise RuntimeError(
        f"Unsupported inference provider: {provider_name}"
    )
