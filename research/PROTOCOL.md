# Controlled evaluation protocol

## 1. Preregister the configuration

Copy the experiment manifest template before running agents. Pin the model,
harness, tool set, policy, task set, generation parameters, and seeds. Assign
development and held-out task IDs before inspecting held-out outcomes. Record a
SHA-256 digest of the assignment.

## 2. Acquire traces lawfully

Use traces only with permission and a documented source. Redact locally, retain
the original outside the repository, and hash the exact redacted file supplied
to reviewers. Never upload a trace merely to run Atlas.

## 3. Keep variables separable

Treat model + harness + tool set + policy + task as the experimental unit. A
cross-model comparison changes only the pinned model field. A cross-harness
comparison is reported separately and must not be attributed to the model.

## 4. Review independently

Give at least two reviewers the same redacted trace, taxonomy version, and
rubric. Reviewers label positive, negative, ambiguous, or excluded without
seeing detector output or one another's labels. Positive labels require an
evidence range. Real-trace labels require the trace SHA-256.

Run agreement and freeze the pre-adjudication result before discussing
conflicts. The supplied evaluator computes binary agreement and uses only
unanimous labels for detector metrics; conflicts remain visible and excluded.

## 5. Preserve the held-out boundary

Do not tune policies, detectors, or adapters on held-out outcomes. Any change
after unblinding creates a new experiment revision and a new held-out set.
Synthetic fixtures in `benchmark/` are conformance tests, not a held-out set.

## 6. Report bounded claims

Report fixture conformance separately from reviewed real-trace metrics. Include
sample counts, exclusions, agreement, configuration revisions, and confidence
intervals when the sample supports them. Do not generalize to model safety or
production security.

## Evidence still requiring people or external runs

The repository can enforce structure, hashing, agreement, and consensus. It
cannot manufacture independent reviewers, consent, representative real traces,
or controlled model executions. Those inputs must be collected and documented
before making research-grade performance claims.
