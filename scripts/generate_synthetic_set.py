"""Generate 20 deterministic, sanitized sessions from the known fixture families."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "benchmark" / "synthetic"
CASES = [
    ("safe_trace.jsonl", []), ("scope_violation.jsonl", ["scope_violation"]),
    ("approval_bypass.jsonl", ["approval_bypass"]),
    ("prompt_injection.jsonl", ["prompt_injection", "scope_violation", "secret_exposure"]),
    ("repeated_action.jsonl", ["runaway_loop"]), ("silent_failure.jsonl", ["silent_tool_failure"]),
    ("secret_exposure.jsonl", ["secret_exposure"]), ("path_traversal.jsonl", ["scope_violation"]),
] * 2 + [
    ("safe_trace.jsonl", []), ("approval_bypass.jsonl", ["approval_bypass"]),
    ("scope_violation.jsonl", ["scope_violation"]), ("safe_trace.jsonl", []),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    labels: list[dict] = []
    for index, (source, expected) in enumerate(CASES, start=1):
        session_id = f"synthetic-{index:02d}"
        source_path = ROOT / "examples" / "traces" / source
        rows = [json.loads(line) for line in source_path.read_text(encoding="utf-8").splitlines()]
        rows[0]["id"] = session_id
        rows[0]["harness"] = "atlas-synthetic"
        target = OUT / f"{session_id}.jsonl"
        target.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )
        labels.append({"session_id": session_id, "expected_categories": expected})
    (OUT / "labels.jsonl").write_text(
        "\n".join(json.dumps(row) for row in labels) + "\n", encoding="utf-8"
    )
    print(f"generated {len(CASES)} sessions in {OUT}")


if __name__ == "__main__":
    main()
