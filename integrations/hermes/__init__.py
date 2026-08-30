"""Native Hermes adapter for IntentGuard continuous supervision.

The adapter observes Hermes through native lifecycle/tool hooks rather than
trusting Hermes' own narrative as the sole execution record.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

SUPERVISOR_URL = os.getenv("INTENTGUARD_SUPERVISOR_URL", "http://127.0.0.1:8765")
TIMEOUT = float(os.getenv("INTENTGUARD_HOOK_TIMEOUT", "8"))


def _post(event: dict[str, Any]) -> dict[str, Any]:
    raw = json.dumps(event, default=str).encode("utf-8")
    req = urllib.request.Request(
        f"{SUPERVISOR_URL.rstrip('/')}/event",
        data=raw,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8")
        value = json.loads(body or "{}")
        return value if isinstance(value, dict) else {}
    except Exception as exc:
        return {"action": "allow", "observer_error": str(exc)}


def register(ctx):
    def emit(kind: str, **payload):
        return _post({"source": "hermes_runtime", "kind": kind, **payload})

    def pre_tool_call(tool_name: str, args: dict, task_id: str = "", **kwargs):
        decision = emit(
            "TOOL_CALL_REQUESTED",
            tool_name=tool_name,
            args=args,
            task_id=task_id,
            runtime=kwargs,
        )
        action = decision.get("action")
        message = decision.get("message") or "Blocked by IntentGuard supervisor"
        if action == "block":
            return {"action": "block", "message": message}
        if action == "intervene" and message:
            try:
                ctx.inject_message(message, role="user")
            except Exception:
                pass
            return {"action": "block", "message": "Paused for IntentGuard intervention"}
        return None

    def post_tool_call(
        tool_name: str,
        args: dict,
        result: str,
        task_id: str = "",
        duration_ms: int = 0,
        **kwargs,
    ):
        decision = emit(
            "TOOL_RESULT_OBSERVED",
            tool_name=tool_name,
            args=args,
            result=result,
            task_id=task_id,
            duration_ms=duration_ms,
            runtime=kwargs,
        )
        if decision.get("action") == "intervene" and decision.get("message"):
            try:
                ctx.inject_message(decision["message"], role="user")
            except Exception:
                pass

    def pre_llm_call(
        session_id: str = "",
        user_message: str = "",
        conversation_history: list | None = None,
        is_first_turn: bool = False,
        model: str = "",
        platform: str = "",
        **kwargs,
    ):
        if user_message:
            emit(
                "HUMAN_INPUT_CAPTURED",
                session_id=session_id,
                text=user_message,
                source_channel="direct_text",
            )
        decision = emit(
            "LLM_TURN_START",
            session_id=session_id,
            user_message=user_message,
            conversation_history=conversation_history or [],
            is_first_turn=is_first_turn,
            model=model,
            platform=platform,
            runtime=kwargs,
        )
        context = decision.get("context")
        if context:
            return {"context": context}
        return None

    def post_llm_call(**kwargs):
        decision = emit("LLM_TURN_END", runtime=kwargs)
        if decision.get("action") == "intervene" and decision.get("message"):
            try:
                ctx.inject_message(decision["message"], role="user")
            except Exception:
                pass

    def subagent_start(**kwargs):
        emit("SUBAGENT_START", runtime=kwargs)

    def subagent_stop(**kwargs):
        emit("SUBAGENT_STOP", runtime=kwargs)

    def on_session_start(**kwargs):
        emit("SESSION_START", runtime=kwargs)

    def on_session_end(**kwargs):
        emit("SESSION_END", runtime=kwargs)

    ctx.register_hook("pre_tool_call", pre_tool_call)
    ctx.register_hook("post_tool_call", post_tool_call)
    ctx.register_hook("pre_llm_call", pre_llm_call)
    ctx.register_hook("post_llm_call", post_llm_call)
    ctx.register_hook("subagent_start", subagent_start)
    ctx.register_hook("subagent_stop", subagent_stop)
    ctx.register_hook("on_session_start", on_session_start)
    ctx.register_hook("on_session_end", on_session_end)
