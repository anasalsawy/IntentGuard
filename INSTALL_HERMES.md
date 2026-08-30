# Install and Test IntentGuard with Hermes

This guide installs the current Hermes MVP without modifying Hermes core source.

Once installed, supervision is intended to remain active whenever Hermes starts. Voice is optional. If the user types directly into Hermes, the adapter captures that text as authoritative human intent and the supervisor still watches supported runtime events.

## 1. Clone the standalone repository

```bash
git clone https://github.com/anasalsawy/IntentGuard.git
cd IntentGuard
```

## 2. Install the Hermes plugin

Linux/macOS:

```bash
mkdir -p ~/.hermes/plugins/anti-deception-supervisor
cp integrations/hermes/plugin.yaml ~/.hermes/plugins/anti-deception-supervisor/plugin.yaml
cp integrations/hermes/__init__.py ~/.hermes/plugins/anti-deception-supervisor/__init__.py
```

Windows PowerShell:

```powershell
$dest = "$HOME\.hermes\plugins\anti-deception-supervisor"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item .\integrations\hermes\plugin.yaml "$dest\plugin.yaml" -Force
Copy-Item .\integrations\hermes\__init__.py "$dest\__init__.py" -Force
```

Restart Hermes after copying the plugin.

## 3. Start the supervisor service

```bash
python mvp_supervisor.py
```

Expected output:

```text
IntentGuard live supervisor listening on http://127.0.0.1:8765
semantic model: (not configured - observation/deterministic mode)
```

Leave this terminal running.

## 4. Start Hermes normally

```bash
hermes
```

There is no special supervised command. The production target is normal agent startup with supervision already active.

## 5. Test direct-text intent capture

Type into Hermes:

```text
Inspect the current project. Do not modify any files. Tell me what you find.
```

The supervisor should receive runtime events such as:

```text
HUMAN_INPUT_CAPTURED
LLM_TURN_START
TOOL_CALL_REQUESTED
TOOL_RESULT_OBSERVED
```

The important point is that direct text works even when no voice frontend is used.

## 6. Add a semantic supervisor model

The MVP accepts an OpenAI-compatible chat-completions endpoint.

Linux/macOS example:

```bash
export SUPERVISOR_BASE_URL="https://openrouter.ai/api/v1"
export SUPERVISOR_API_KEY="YOUR_KEY"
export SUPERVISOR_MODEL="YOUR_MODEL"
python mvp_supervisor.py
```

Windows PowerShell:

```powershell
$env:SUPERVISOR_BASE_URL="https://openrouter.ai/api/v1"
$env:SUPERVISOR_API_KEY="YOUR_KEY"
$env:SUPERVISOR_MODEL="YOUR_MODEL"
python .\mvp_supervisor.py
```

Then test a clear constraint:

```text
Diagnose why this project fails. Read-only investigation only. Do not edit files, restart services, deploy, or change configuration.
```

## 7. Inspect shared state

Health endpoint:

```text
http://127.0.0.1:8765/health
```

Session ledger:

```text
http://127.0.0.1:8765/session/<session-id>
```

## Current integration status

CLI currently provides the strongest intervention path. Hermes native hooks provide observation and pre-tool blocking. Corrective injection into the active CLI session is supported by the adapter where Hermes exposes `ctx.inject_message()`.

Desktop/gateway observation can use the same hook layer, but full mid-turn intervention parity requires a gateway/session delivery adapter.

## Production target

```text
install once
→ start Hermes normally
→ IntentGuard supervisor starts automatically
→ typed or voice intent enters one canonical human-intent stream
→ runtime observation stays active for the full session
→ no special invocation required
```
