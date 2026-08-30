# IntentGuard

## Continuous Runtime-Synchronized Deception Detection and Intent-Preservation Supervision for Autonomous AI Agents

**A live supervisory architecture that sits between a human and an execution model, continuously shares the execution context, observes the agent while it works, detects deception, fabrication, manipulation, and deviation from user intent, and automatically intervenes before the run continues unchecked.**

Working implementation name: **IntentGuard**.

## Problem being addressed

Modern AI agents can deviate from a user's actual intent during long-running work. They can fabricate progress, report actions that did not occur, misrepresent tool results, take shortcuts, silently reinterpret instructions, manipulate the framing of a failure, or drift away from the original objective. A second practical problem is the human workflow this creates: the user repeatedly explains an objective to one model, asks it to formulate a better instruction, copies that instruction into an execution agent, watches the execution agent, notices problems, returns to the first model, explains what happened, receives a corrective prompt, and copies that correction back again.

This project turns that manual back-and-forth into a persistent supervisory control loop.

The central idea is **not** to send a cleaned prompt to an execution agent, install static guardrails, and disappear. The anti-deception layer remains present for the entire execution. It behaves more like a human supervisor sitting beside the execution agent: it knows what the user intended, knows the instruction it sent, receives the live execution context and event stream, watches what the agent says and does, compares that behavior continuously with the user's intent, and can speak back to the execution agent with corrective instructions while the task is still running.

## Core architecture

```text
                         HUMAN
              ┌────────────┴────────────┐
              │                         │
          Voice input              Direct typing
              │                         │
              ▼                         │
   ┌────────────────────────┐           │
   │ ANTI-DECEPTION LAYER   │           │
   │ Executive / Supervisor │◄──────────┘
   │                        │  authoritative override
   │ • understands intent   │
   │ • compiles instruction │
   │ • maintains live state │
   │ • continuously watches │
   │ • detects deviation    │
   │ • sends corrections    │
   └───────────┬────────────┘
               │ initial structured instruction
               ▼
        ┌───────────────┐
        │ EXECUTION AI  │
        └───────┬───────┘
                │
                │ live text + tool calls + tool results
                │ plans + errors + artifacts + state changes
                ▼
   ┌─────────────────────────────┐
   │ SHARED RUNTIME OBSERVATION  │
   │ PLANE / CANONICAL STATE     │
   └───────────┬─────────────────┘
               │
               └──────────────► Anti-Deception Supervisor
                                      │
                          deviation?  │
                         ┌────────────┴────────────┐
                         │ NO                      │ YES
                         ▼                         ▼
                    keep observing        corrective intervention
                                                 │
                                                 ▼
                                         Execution AI
```

## Ground-truth observation

The executor is not treated as the witness to its own actions. The supervisor should receive runtime/tool/environment telemetry independently of the executor's prose wherever the host agent exposes such hooks. This allows the system to compare what the executor **claims** with what the execution environment **actually reports**.

Examples include requested tool calls, tool arguments, actual tool results, shell exit codes, filesystem writes/diffs, browser state, API responses, errors, artifacts, and completed side effects.

The architecture does not claim access to hidden chain-of-thought. It supervises the full observable execution trajectory and any internal plan/state the host agent explicitly exposes.

## Continuous observation and intervention

The supervisor does not leave after delegation. It maintains synchronized state containing the original human conversation, current intent, delegated instruction, direct typed overrides, executor messages, tool requests, tool results, artifacts, errors, findings, interventions, and current task state.

The loop is continuous:

```text
observe → compare → detect → intervene → observe → compare → ...
```

When deception, fabricated success, unsupported completion claims, manipulation, scope drift, misunderstanding, or intent deviation is detected, the supervisor can send a correction into the **same running execution session** and then continue watching whether that correction was obeyed.

## Input modality

Voice is a first-class human interface, not a dependency. If the user speaks, the voice layer extracts and revises intent. If the user types directly into Hermes, Codex, another desktop agent, or a CLI agent, that direct human input becomes the authoritative intent stream and supervision continues exactly the same way.

The target product behavior is:

```text
start the agent normally
→ supervision is already enabled
→ talk or type
→ shared intent updates
→ runtime observation continues for the full session
```

## Universal integration direction

IntentGuard is designed as an agent-independent supervisory runtime with thin host adapters:

```text
IntentGuard core
├── Hermes adapter
├── Codex adapter
├── Claude Code adapter
├── OpenCode adapter
├── browser-agent adapter
└── generic runtime/MCP adapter
```

Each adapter maps the host's native hooks into a common observation schema and provides intervention/blocking where supported.

A future OpenRouter-compatible control plane can make the product feel model-native: the user selects an IntentGuard-supervised model endpoint while a local observation adapter supplies ground-truth runtime telemetry to the same supervised session.

## Hermes MVP

The repository includes the first native Hermes adapter and a runnable local supervisor service. The Hermes integration uses native lifecycle/tool hooks rather than hard-forking Hermes core.

See `INSTALL_HERMES.md`.

## Reference implementation

Requires Python 3.11+.

```bash
python -m pip install -e .
python examples/demo.py
python -m pytest
```

## Project status

Current components include:

- Intent/evidence/policy reference structures;
- append-only audit model;
- Hermes native hook adapter;
- direct-text human-intent capture;
- runtime event observation;
- pre-tool blocking;
- live supervisor service compatible with OpenAI-style endpoints;
- architecture and security documentation;
- tests and demo code.

The next major milestones are fully runtime-synchronized shared state in the core library, gateway/desktop intervention parity, automatic daemon startup, voice frontend integration, and generic adapter packaging.

## License

MIT. See `LICENSE`.
