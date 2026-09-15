"""Run deterministic retrieval baseline evaluations."""

from __future__ import annotations

import json
from pathlib import Path

from dacqua_chatbot.knowledge import (
    LexicalKnowledgeRetriever,
    load_knowledge_corpus,
)


ROOT = Path(__file__).resolve().parents[1]

CASES_PATH = (
    ROOT
    / "evals"
    / "cases"
    / "retrieval-baseline.json"
)

JSON_REPORT = (
    ROOT
    / "evals"
    / "reports"
    / "retrieval-baseline.json"
)

MD_REPORT = (
    ROOT
    / "evals"
    / "reports"
    / "retrieval-baseline.md"
)


def main() -> None:
    config = json.loads(
        CASES_PATH.read_text(
            encoding="utf-8"
        )
    )

    corpus_path = (
        ROOT
        / config["corpus"]
    )

    documents = (
        load_knowledge_corpus(
            corpus_path
        )
    )

    retriever = (
        LexicalKnowledgeRetriever(
            documents
        )
    )

    top_k = int(
        config.get(
            "top_k",
            3,
        )
    )

    results = []

    passed = 0

    for case in config["cases"]:
        hits = retriever.search(
            case["query"],
            limit=top_k,
        )

        retrieved_ids = [
            hit.document.id
            for hit in hits
        ]

        expected_ids = (
            case[
                "expected_document_ids"
            ]
        )

        success = all(
            expected_id
            in retrieved_ids
            for expected_id
            in expected_ids
        )

        if success:
            passed += 1

        result = {
            "id": case["id"],
            "query": case["query"],
            "expected_document_ids": (
                expected_ids
            ),
            "retrieved": [
                {
                    "document_id": (
                        hit.document.id
                    ),
                    "title": (
                        hit.document.title
                    ),
                    "score": hit.score,
                    "matched_terms": list(
                        hit.matched_terms
                    ),
                }
                for hit in hits
            ],
            "passed": success,
        }

        results.append(result)

        status = (
            "PASS"
            if success
            else "FAIL"
        )

        print(
            f"{status}: "
            f"{case['id']} -> "
            f"{retrieved_ids}"
        )

    total = len(results)

    report = {
        "label": config["label"],
        "top_k": top_k,
        "passed": passed,
        "total": total,
        "results": results,
    }

    JSON_REPORT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    JSON_REPORT.write_text(
        json.dumps(
            report,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Retrieval Baseline",
        "",
        f"- Label: `{config['label']}`",
        f"- Top-k: `{top_k}`",
        f"- Passed: `{passed}/{total}`",
        "",
        "| Case | Result | Retrieved |",
        "| --- | --- | --- |",
    ]

    for result in results:
        retrieved = ", ".join(
            item["document_id"]
            for item
            in result["retrieved"]
        )

        lines.append(
            "| "
            + result["id"]
            + " | "
            + (
                "PASS"
                if result["passed"]
                else "FAIL"
            )
            + " | "
            + retrieved
            + " |"
        )

    MD_REPORT.write_text(
        "\n".join(lines)
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "Retrieval baseline: "
        f"{passed}/{total} passed"
    )

    if passed != total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
