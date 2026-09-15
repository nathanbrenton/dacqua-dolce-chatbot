"""Real offline API-to-model smoke test."""

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
        print("===== HEALTH BEFORE GENERATION =====")
        before = client.get("/health")
        print(before.status_code)
        print(before.json())

        print()
        print("===== CHAT =====")

        response = client.post(
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

        print(response.status_code)
        print(response.json())

        if response.status_code != 200:
            raise RuntimeError(
                "Chat endpoint smoke test failed."
            )

        print()
        print("===== HEALTH AFTER GENERATION =====")
        after = client.get("/health")
        print(after.status_code)
        print(after.json())

        if not after.json()["loaded"]:
            raise RuntimeError(
                "Provider did not report loaded state."
            )


if __name__ == "__main__":
    main()
