# Hugging Face launch guide

The project can be published as three linked Hub artifacts:

1. a source repository on GitHub,
2. a Hugging Face Space using `space/app.py`,
3. a Hugging Face Dataset using `dataset/` plus redacted STS traces.

## 1. Authenticate

```bash
hf auth login
```

Use a token with the minimum write permissions needed for the target repositories.

## 2. Create and publish the Space

Create a Gradio Space named `agent-failure-atlas`, then clone it and copy the repository contents into it. The root `README.md` contains Space metadata and points to `space/app.py`.

```bash
hf repo create <username>/agent-failure-atlas --repo-type space --space-sdk gradio

git clone https://huggingface.co/spaces/<username>/agent-failure-atlas hf-space
rsync -av --exclude .git ./ hf-space/
cd hf-space
git add .
git commit -m "Launch Open Agent Failure Atlas MVP"
git push
```

Do not put secrets in Space variables unless they are configured through the Space settings. The included demo requires no token or model API.

## 3. Create and publish the synthetic dataset

```bash
hf repo create <username>/agent-failure-atlas-smoke --repo-type dataset
hf upload <username>/agent-failure-atlas-smoke dataset . --repo-type dataset
hf upload <username>/agent-failure-atlas-smoke examples/traces traces --repo-type dataset
```

The synthetic dataset should be described as a software smoke set, not an accuracy benchmark.

## 4. Upload an STS trace only after review

```bash
agent-atlas redact session.jsonl --out session.redacted.jsonl
agent-atlas scan session.redacted.jsonl --out session.redacted.report.json
hf upload <username>/<trace-dataset> session.redacted.jsonl . --repo-type dataset
```

Redaction is best effort. Open and review the resulting file before publishing it.

## 5. Reviewer-facing launch package

The initial launch should include:

- one sentence explaining the gap between trace viewing and failure analysis,
- a 60–90 second screen recording,
- the Space,
- the synthetic dataset,
- the GitHub repository,
- exact limitations,
- and an invitation for trace adapters and taxonomy feedback.
