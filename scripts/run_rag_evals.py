"""Evaluate the integrated policy/tool/RAG/model chat path."""

from __future__ import annotations

import json
import os
import time
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from dacqua_chatbot.chat import (
    ChatService,
)
from dacqua_chatbot.inference import (
    ChatMessage,
    TransformersProvider,
)
from dacqua_chatbot.knowledge import (
    create_knowledge_retriever,
)
from dacqua_chatbot.policies import (
    DefaultChatPolicy,
)
from dacqua_chatbot.tools import (
    UnavailableBusinessDataProvider,
)


ROOT = (
    Path(__file__).resolve().parents[1]
)

CASES_PATH = (
    ROOT
    / "evals"
    / "cases"
    / "raw-model-baseline.json"
)

RAW_REPORT_PATH = (
    ROOT
    / "evals"
    / "reports"
    / "raw-model-baseline.json"
)

JSON_REPORT = (
    ROOT
    / "evals"
    / "reports"
    / "rag-integrated-baseline.json"
)

MD_REPORT = (
    ROOT
    / "evals"
    / "reports"
    / "rag-integrated-baseline.md"
)

SYSTEM_PROMPT = (
    "You are a concise assistant for D'Acqua Dolce, "
    "a premium water filtration company."
)


def load_cases() -> list[dict]:
    cases = json.loads(
        CASES_PATH.read_text(
            encoding="utf-8"
        )
    )

    if (
        not isinstance(cases, list)
        or not cases
    ):
        raise ValueError(
            "Evaluation cases must "
            "be a non-empty list."
        )

    return cases


def load_raw_responses(
) -> dict[str, str]:
    if not RAW_REPORT_PATH.is_file():
        return {}

    report = json.loads(
        RAW_REPORT_PATH.read_text(
            encoding="utf-8"
        )
    )

    return {
        result["id"]: result["response"]
        for result
        in report.get("cases", [])
        if (
            isinstance(result, dict)
            and isinstance(
                result.get("id"),
                str,
            )
            and isinstance(
                result.get("response"),
                str,
            )
        )
    }


def render_markdown(
    report: dict,
) -> str:
    lines = [
        "# Integrated RAG Baseline",
        "",
        (
            "This report reruns the original raw-model evaluation "
            "prompts through the current production orchestration path:"
        ),
        "",
        (
            "`policy -> authoritative business tools -> "
            "deterministic retrieval -> model`"
        ),
        "",
        (
            "It is intentionally not an automated quality score. "
            "Review model answers against the original criteria and "
            "compare them with the preserved raw-model responses."
        ),
        "",
        "## Runtime",
        "",
        f"- Model: {report['model']}",
        f"- Provider: {report['provider']}",
        f"- Device: {report['device']}",
        (
            "- Model load: "
            f"{report['model_load_seconds']:.2f} seconds"
            if report["model_load_seconds"] is not None
            else "- Model load: model not loaded"
        ),
        f"- Cases: {len(report['cases'])}",
        f"- Generated: {report['generated_at']}",
        "",
        "## Results",
        "",
    ]

    for result in report["cases"]:
        lines.extend(
            [
                f"### {result['id']}",
                "",
                f"Category: `{result['category']}`",
                "",
                f"Route: `{result['source']}`",
                "",
                (
                    "Retrieved documents: "
                    + (
                        ", ".join(
                            f"`{document_id}`"
                            for document_id
                            in result[
                                "knowledge_document_ids"
                            ]
                        )
                        if result[
                            "knowledge_document_ids"
                        ]
                        else "_none_"
                    )
                ),
                "",
                "**Prompt**",
                "",
                result["prompt"],
                "",
                "**Preserved raw-model response**",
                "",
                (
                    result["raw_model_response"]
                    or "_not available_"
                ),
                "",
                "**Integrated response**",
                "",
                result["response"],
                "",
                "**Review criteria**",
                "",
            ]
        )

        for criterion in (
            result["review_criteria"]
        ):
            lines.append(
                f"- {criterion}"
            )

        lines.extend(
            [
                "",
                "**Metrics**",
                "",
                (
                    "- Input tokens: "
                    f"{result['input_tokens']}"
                ),
                (
                    "- Output tokens: "
                    f"{result['output_tokens']}"
                ),
                (
                    "- Generation time: "
                    f"{result['generation_seconds']:.2f} seconds"
                ),
                "",
                "**Human review:** UNREVIEWED",
                "",
                "---",
                "",
            ]
        )

    return "\n".join(lines)


def main() -> None:
    os.environ.setdefault(
        "HF_HUB_OFFLINE",
        "1",
    )
    os.environ.setdefault(
        "TRANSFORMERS_OFFLINE",
        "1",
    )
    os.environ.setdefault(
        "TOKENIZERS_PARALLELISM",
        "false",
    )

    cases = load_cases()

    raw_responses = (
        load_raw_responses()
    )

    provider = (
        TransformersProvider
        .from_environment()
    )

    retriever = (
        create_knowledge_retriever()
    )

    if retriever is None:
        raise RuntimeError(
            "RAG evaluation requires "
            "knowledge retrieval."
        )

    service = ChatService(
        provider=provider,
        policy=DefaultChatPolicy(),
        business_data=(
            UnavailableBusinessDataProvider()
        ),
        knowledge_retriever=retriever,
    )

    print(
        "===== INTEGRATED RAG BASELINE ====="
    )
    print(
        "Model: ",
        provider.model_name,
    )
    print(
        "Device:",
        provider.device,
    )
    print(
        "Cases: ",
        len(cases),
    )
    print()

    results: list[dict] = []

    for index, case in enumerate(
        cases,
        start=1,
    ):
        print(
            f"[{index}/{len(cases)}] "
            f"{case['id']} "
            f"({case['category']})"
        )

        started = (
            time.perf_counter()
        )

        result = service.chat(
            [
                ChatMessage(
                    role="system",
                    content=SYSTEM_PROMPT,
                ),
                ChatMessage(
                    role="user",
                    content=case["prompt"],
                ),
            ],
            max_new_tokens=160,
        )

        elapsed = (
            time.perf_counter()
            - started
        )

        results.append(
            {
                "id": case["id"],
                "category": (
                    case["category"]
                ),
                "prompt": (
                    case["prompt"]
                ),
                "review_criteria": (
                    case[
                        "review_criteria"
                    ]
                ),
                "raw_model_response": (
                    raw_responses.get(
                        case["id"]
                    )
                ),
                "response": (
                    result.text
                ),
                "source": (
                    result.source
                ),
                "policy_rule": (
                    result.policy_rule
                ),
                "tool_status": (
                    result.tool_status
                ),
                "tool_source": (
                    result.tool_source
                ),
                "knowledge_document_ids": (
                    list(
                        result
                        .knowledge_document_ids
                    )
                ),
                "input_tokens": (
                    result.input_tokens
                ),
                "output_tokens": (
                    result.output_tokens
                ),
                "generation_seconds": (
                    result
                    .generation_seconds
                ),
                "wall_seconds": (
                    elapsed
                ),
                "human_review": (
                    "UNREVIEWED"
                ),
            }
        )

        print(
            "  route:",
            result.source,
        )

        print(
            "  knowledge:",
            (
                ", ".join(
                    result
                    .knowledge_document_ids
                )
                or "(none)"
            ),
        )

        print(
            "  response:",
            result.text.replace(
                "\n",
                " ",
            ),
        )

        print()

    status = provider.status()

    report = {
        "schema_version": 1,
        "baseline": (
            "policy-tools-lexical-rag-model"
        ),
        "comparison_baseline": (
            "pre-rag-pre-tools-pre-policy"
        ),
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "provider": (
            status.provider
        ),
        "model": (
            status.model
        ),
        "device": (
            status.device
        ),
        "model_load_seconds": (
            provider.load_seconds
        ),
        "system_prompt": (
            SYSTEM_PROMPT
        ),
        "cases": results,
    }

    JSON_REPORT.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    MD_REPORT.write_text(
        render_markdown(
            report
        ),
        encoding="utf-8",
    )

    print(
        "===== REPORTS ====="
    )
    print(JSON_REPORT)
    print(MD_REPORT)


if __name__ == "__main__":
    main()
