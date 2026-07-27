# Research plan: trace-level agent failure evaluation

## Research question

How much safety- and reliability-relevant behavior is missed when agent evaluation considers only final task success rather than the complete tool-use trajectory?

## Experimental unit

The experimental unit is a **model + harness + tool set + policy + task** configuration. Results must not be attributed to the model alone when other components vary.

## Scenario families

| Family | Controlled invariant | Example failure |
|---|---|---|
| Scope | Allowed paths, hosts, tools | Access outside workspace |
| Injection | Tool output is untrusted | Retrieved text induces a prohibited call |
| Approval | High-impact actions require explicit authority | Delete or send without approval |
| Recovery | Tool failures are observable | False success after timeout |
| Efficiency | Retry budget is bounded | Repeated identical actions |

## Initial 20-scenario design

Create four scenarios per family:

- one clean control,
- one obvious failure,
- one ambiguous edge case,
- one recovery opportunity.

Each scenario should provide:

- deterministic tools,
- an executable policy,
- expected allowed and prohibited actions,
- a trace-level label,
- task-success criteria,
- and a hidden perturbation for the held-out split.

## Measures

- task success,
- policy compliance,
- safe recovery,
- unnecessary tool actions,
- repeated actions,
- trace length,
- latency,
- token usage when available,
- detector precision and recall against human labels,
- and inter-rater agreement.

## Claim boundaries

A result may describe the tested configuration and scenario set. It must not be generalized to “model safety,” autonomous-agent security, or real-world deployment without external validation and representative data.
