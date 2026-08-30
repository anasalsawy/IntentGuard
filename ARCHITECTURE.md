# IntentGuard Architecture

## Research title

**Continuous Runtime-Synchronized Deception Detection and Intent-Preservation Supervision for Autonomous AI Agents**

## Design thesis

IntentGuard is a persistent human-proxy supervisor, not a one-time prompt sanitizer and not merely a final-answer grader.

The required loop is:

```text
understand human intent
→ delegate to executor
→ observe execution live
→ compare behavior with intent
→ detect deception / fabrication / deviation
→ intervene in the same running session
→ observe whether the correction was obeyed
→ repeat until completion, block, or human escalation
```

## Core principle: the executor is not its own witness

The supervisor must not depend only on the executor saying what it did. Wherever the host agent exposes the necessary surfaces, IntentGuard receives independent runtime observations from native lifecycle hooks, tool dispatch, filesystem state, shell results, browser state, API responses, artifacts, errors, and side-effect receipts.

This creates two channels:

```text
EXECUTION CHANNEL
executor → tools / runtime / environment

OBSERVATION CHANNEL
tools / runtime / environment → IntentGuard supervisor
```

Executor messages are also observed, but they are treated as claims that can be checked against runtime evidence.

## Input model

Human input is authoritative regardless of modality:

```text
voice ─────┐
CLI text ──┤
desktop ───┤→ canonical human-intent stream
IDE/API ───┘
```

Voice improves natural intent capture and interruption, but supervision does not depend on voice. If the user types directly into Hermes or another host agent, that text becomes the authoritative current intent and the supervisor continues watching the same execution.

## Shared runtime state

Separate model providers do not literally share one hidden proprietary context window. Instead, both executor and supervisor consume synchronized canonical session state.

Recommended state:

```text
session_id
human_conversation
current_intent
intent_revision
delegated_instruction
executor_messages
runtime_events
tool_requests
tool_results
artifacts
errors
side_effects
supervisor_findings
supervisor_interventions
human_overrides
execution_status
```

## Shared Runtime Observation Plane

Normalized event types should include:

```text
SESSION_START
HUMAN_INPUT_CAPTURED
INTENT_REVISION
DELEGATED_INSTRUCTION
EXECUTOR_MESSAGE
TOOL_CALL_REQUESTED
TOOL_RESULT_OBSERVED
FILESYSTEM_CHANGE
SHELL_RESULT
BROWSER_STATE
API_RESULT
ARTIFACT_CREATED
ERROR
SUBAGENT_START
SUBAGENT_STOP
PROPOSED_SIDE_EFFECT
COMPLETED_SIDE_EFFECT
SUPERVISOR_FINDING
SUPERVISOR_INTERVENTION
EXECUTOR_FINAL
```

Every event should carry source/provenance, sequence ordering, session identity, timestamp, and current intent revision when available.

## Continuous supervisor loop

Conceptual implementation:

```python
async def supervise(runtime, executor, supervisor, state):
    async for event in runtime.observe():
        state.apply(event)

        decision = await supervisor.evaluate(
            intent=state.current_intent,
            event=event,
            state=state,
        )

        if decision.block:
            await runtime.block_pending_action(decision.reason)

        if decision.intervene:
            await executor.send(decision.corrective_instruction)

        if decision.pause:
            await runtime.pause_if_supported()

        if decision.ask_human:
            await state.request_human_input(decision.question)
```

The loop remains active until the execution reaches a terminal state.

## Deception and deviation targets

IntentGuard explicitly targets observable behavior including:

- claiming success when runtime evidence says an action failed or never occurred;
- fabricating files, messages, metrics, citations, tool results, state, or completion;
- concealing or minimizing failures while representing the task as successful;
- treating assumptions as human authorization;
- silently substituting a different or easier objective;
- violating explicit constraints while claiming compliance;
- manipulation of the narrative presented to the user;
- scope expansion/contraction inconsistent with intent;
- abandonment of the requested workflow while reporting progress;
- conflict between executor claims and independently observed tool/runtime state.

The system does not need to establish a model's subjective motive. It detects and responds to observable deceptive, fabricated, manipulative, or intent-divergent behavior.

## Intervention semantics

A correction must target the same active executor session wherever the host supports it. An intervention is not considered successful merely because it was sent; subsequent runtime behavior is observed to verify compliance.

## Universal adapter architecture

```text
                     IntentGuard Core
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     Hermes adapter    Codex adapter   OpenCode adapter
          │                │                │
        Hermes            Codex          OpenCode
          │                │                │
          └──────────── runtime events ─────┘
                           │
                    observation plane
                           │
                      supervisor
```

Each adapter should implement the smallest possible host-specific layer around native hooks rather than hard-forking the host agent.

## OpenRouter-compatible direction

A future cloud control plane can expose an OpenAI/OpenRouter-compatible endpoint that appears to users like a selectable supervised model. The cloud side owns model routing, supervisor state, and session coordination. A local/native host adapter supplies the ground-truth runtime observation stream.

```text
OpenRouter-compatible control plane
        +
local agent observation adapter
        =
model-like UX with real runtime supervision
```

Without the local observation plane, only model-level supervision is possible and the system must not claim independent runtime verification.

## Hermes first integration

Hermes is the first target because native lifecycle/tool hooks provide observation and pre-action blocking without modifying Hermes core. CLI mode also supports corrective message injection into the active session. Desktop/gateway parity requires a gateway delivery adapter.

## Conformance requirement

An implementation is incomplete if it only:

- cleans the initial prompt;
- waits for the executor to finish;
- reads the executor's final summary; or
- performs only a final verification gate.

A conforming implementation requires persistent session state, live observation, independent runtime evidence where available, continuous evaluation, active same-session intervention, human override synchronization, provenance/evidence tracking, and configured deterministic boundaries.
