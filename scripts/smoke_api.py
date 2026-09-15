"""Real offline API, business-tool, policy, and model smoke test."""

import os

from fastapi.testclient import TestClient

from dacqua_chatbot.api import create_app


def main() -> None:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault(
        "TOKENIZERS_PARALLELISM",
        "false",
    )
    os.environ.setdefault(
        "DACQUA_INFERENCE_PROVIDER",
        "transformers",
    )

    app = create_app()

    with TestClient(app) as client:
        print("===== HEALTH BEFORE REQUESTS =====")

        before = client.get("/health")
        print(before.json())

        if before.json()["loaded"]:
            raise RuntimeError(
                "Model should not be loaded at startup."
            )

        print()
        print("===== AUTHORITATIVE PRICE ROUTE =====")

        pricing = client.post(
            "/v1/chat",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "What is the current price of the "
                            "D'Acqua Dolce Origin system?"
                        ),
                    }
                ]
            },
        )

        print(pricing.json())

        if pricing.status_code != 200:
            raise RuntimeError(
                "Price request failed."
            )

        if pricing.json()["source"] != "tool":
            raise RuntimeError(
                "Price request did not route to business tool."
            )

        if pricing.json()["tool_status"] != "unavailable":
            raise RuntimeError(
                "Unexpected default tool status."
            )

        after_tool = client.get("/health")

        print()
        print("===== HEALTH AFTER TOOL REQUEST =====")
        print(after_tool.json())

        if after_tool.json()["loaded"]:
            raise RuntimeError(
                "Tool-only request unexpectedly loaded model."
            )

        print()
        print("===== NORMAL MODEL REQUEST =====")

        normal = client.post(
            "/v1/chat",
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a concise assistant for "
                            "D'Acqua Dolce, a premium water "
                            "filtration company."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "In one sentence, explain what "
                            "reverse osmosis does."
                        ),
                    },
                ],
                "max_new_tokens": 80,
            },
        )

        print(normal.json())

        if normal.status_code != 200:
            raise RuntimeError(
                "Normal model request failed."
            )

        if normal.json()["source"] != "model":
            raise RuntimeError(
                "Normal question did not reach model."
            )

        final_health = client.get("/health")

        print()
        print("===== HEALTH AFTER MODEL REQUEST =====")
        print(final_health.json())

        if not final_health.json()["loaded"]:
            raise RuntimeError(
                "Model failed to enter loaded state."
            )


if __name__ == "__main__":
    main()
