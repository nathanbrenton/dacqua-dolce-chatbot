"""Run the pre-RAG raw-model evaluation baseline."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from dacqua_chatbot.inference import (
    ChatMessage,
    TransformersProvider,
)


ROOT = Path(__file__).resolve().parents[1]

CASES_PATH = ROOT / "evals/cases/raw-model-baseline.json"
JSON_REPORT = ROOT / "evals/reports/raw-model-baseline.json"
MD_REPORT = ROOT / "evals/reports/raw-model-baseline.md"

SYSTEM_PROMPT = (
    "You are a concise assistant for D'Acqua Dolce, "
    "a premium water filtration company."
)


def load_cases() -> list[dict]:
    """Load and minimally validate evaluation cases."""

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation case file must contain a non-empty list.")

    seen_ids: set[str] = set()

    for case in cases:
        for key in (
            "id",
            "category",
            "prompt",
            "review_criteria",
        ):
            if key not in case:
                raise ValueError(
                    f"Evaluation case is missing required field: {key}"
                )

        if case["id"] in seen_ids:
            raise ValueError(
                f"Duplicate evaluation case id: {case['id']}"
            )

        seen_ids.add(case["id"])

    return cases


def render_markdown(report: dict) -> str:
    """Render a human-reviewable Markdown report."""

    lines = [
        "# Raw Model Baseline",
        "",
        "This report captures model behavior before RAG, business-data tools, "
        "or the production policy layer are added.",
        "",
        "It is intentionally not an automated quality score. Each response "
        "should be reviewed against the listed criteria.",
        "",
        "## Runtime",
        "",
        f"- Model: {report['model']}",
        f"- Provider: {report['provider']}",
        f"- Device: {report['device']}",
        f"- Model load: {report['model_load_seconds']:.2f} seconds",
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
                "**Prompt**",
                "",
                result["prompt"],
                "",
                "**Raw response**",
                "",
                result["response"],
                "",
                "**Review criteria**",
                "",
            ]
        )

        for criterion in result["review_criteria"]:
            lines.append(f"- {criterion}")

        lines.extend(
            [
                "",
                "**Metrics**",
                "",
                f"- Input tokens: {result['input_tokens']}",
                f"- Output tokens: {result['output_tokens']}",
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
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    cases = load_cases()

    provider = TransformersProvider.from_environment()

    print("===== RAW MODEL BASELINE =====")
    print("Model: ", provider.model_name)
    print("Device:", provider.device)
    print("Cases: ", len(cases))
    print()

    provider.load()

    results = []

    for index, case in enumerate(cases, start=1):
        print(
            f"[{index}/{len(cases)}] "
            f"{case['id']} "
            f"({case['category']})"
        )

        started = time.perf_counter()

        result = provider.generate(
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

        elapsed = time.perf_counter() - started

        results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "prompt": case["prompt"],
                "review_criteria": case["review_criteria"],
                "response": result.text,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "generation_seconds": result.generation_seconds,
                "wall_seconds": elapsed,
                "human_review": "UNREVIEWED",
            }
        )

        print("  response:", result.text.replace("\n", " "))
        print(
            "  generation:",
            f"{result.generation_seconds:.2f}s",
        )
        print()

    status = provider.status()

    report = {
        "schema_version": 1,
        "baseline": "pre-rag-pre-tools-pre-policy",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "provider": status.provider,
        "model": status.model,
        "device": status.device,
        "model_load_seconds": provider.load_seconds,
        "system_prompt": SYSTEM_PROMPT,
        "cases": results,
    }

    JSON_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        render_markdown(report),
        encoding="utf-8",
    )

    print("===== REPORTS =====")
    print(JSON_REPORT)
    print(MD_REPORT)


if __name__ == "__main__":
    main()
