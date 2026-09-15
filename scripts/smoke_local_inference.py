"""Offline local-inference smoke test."""

import os

from dacqua_chatbot.inference import (
    ChatMessage,
    TransformersProvider,
)


def main() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    provider = TransformersProvider.from_environment()

    print("===== PROVIDER =====")
    print("Model: ", provider.model_name)
    print("Device:", provider.device)

    provider.load()

    print(
        "Load:  ",
        f"{provider.load_seconds:.2f}s"
        if provider.load_seconds is not None
        else "unknown",
    )

    result = provider.generate(
        [
            ChatMessage(
                role="system",
                content=(
                    "You are a concise assistant for D'Acqua Dolce, "
                    "a premium water filtration company."
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    "In one sentence, explain what reverse osmosis does."
                ),
            ),
        ],
        max_new_tokens=80,
    )

    print()
    print("===== RESPONSE =====")
    print(result.text)

    print()
    print("===== METRICS =====")
    print("Model:             ", result.model)
    print("Device:            ", result.device)
    print("Input tokens:      ", result.input_tokens)
    print("Output tokens:     ", result.output_tokens)
    print(
        "Generation time:   ",
        f"{result.generation_seconds:.2f}s",
    )


if __name__ == "__main__":
    main()
