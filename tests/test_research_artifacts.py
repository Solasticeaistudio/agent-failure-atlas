import json


def test_research_json_artifacts_are_parseable(root):
    for path in (
        root / "schemas" / "annotation.schema.json",
        root / "schemas" / "experiment-manifest.schema.json",
        root / "research" / "experiment-manifest.template.json",
    ):
        assert json.loads(path.read_text(encoding="utf-8"))

    annotation_template = root / "research" / "annotations.template.jsonl"
    rows = [
        json.loads(line)
        for line in annotation_template.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert {row["reviewer_id"] for row in rows} == {"reviewer-a", "reviewer-b"}
    assert all(row["label"] == "excluded" for row in rows)


def test_private_research_directories_are_ignored(root):
    ignored = (root / ".gitignore").read_text(encoding="utf-8")
    for name in ("annotations", "results", "traces"):
        assert f"research/{name}/" in ignored
