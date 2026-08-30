# Security model

IntentGuard is a risk-reduction control plane, not a proof that an AI agent cannot deceive.

## Security invariants

1. No side effect is trusted solely because the model says it happened.
2. Completion claims requiring tools must reference runtime or tool evidence.
3. Tool authorization is deterministic and external to the model where possible.
4. Untrusted content cannot grant itself authority.
5. High-impact effects require a commit decision separate from generation.
6. Human overrides are explicit revisions and remain auditable.
7. Supervisor approval cannot override a deterministic policy failure.
8. Executor self-report is not the sole source of execution truth.

## Observation trust model

The preferred observation path is independent runtime instrumentation: native host hooks, tool adapters, filesystem state, shell results, browser state, API responses, artifact hashes, and side-effect receipts. Executor prose is treated as a claim that can be compared against those observations.

IntentGuard does not claim access to hidden chain-of-thought. It supervises observable execution and any internal plan/state the host explicitly exposes.

## Recommended production controls

- run executor and supervisor in separate processes/containers;
- keep credentials outside model context;
- issue short-lived capability-scoped tool tokens;
- require idempotency keys for write tools;
- stage filesystem/database changes where possible;
- hash important artifacts and tool outputs;
- redact secrets before sending evidence to verifier models;
- rate-limit recursive repair attempts;
- require explicit approval for configured high-impact operations.

## Known limitations

LLM supervisors can share blind spots with executors. Speech transcription can alter meaning. A compromised tool adapter can fabricate telemetry. Hash chains provide tamper evidence only if anchors are stored outside the compromised process. Policy definitions can themselves be wrong.

Use defense in depth.
