#!/usr/bin/env python3
"""Enforce one evidence-backed knowledge closeout for each public JL task.

The hook inspects only the current lifecycle event. It never opens a
transcript and persists no prompt, tool input, tool output, task identifier,
fragment, source, log, or project path.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


STATE_VERSION = 2
OUTCOMES = {"usage_recorded", "solution_candidate", "server_gap"}
STATE_FIELDS = {
    "version",
    "jl_task_active",
    "consent_checked",
    "consent_granted",
    "agreement_reply_seen",
    "queried_task_hash",
    "knowledge_outcome",
}
JL_PROMPT = re.compile(
    r"(?:\bjl(?:i|sdk)?\b|jieli|杰理|蓝牙耳机|tws|anc|通透|"
    r"(?:ac|jl)\d{3,5}[a-z]*|br\d{2,4})",
    re.IGNORECASE,
)
OUTBOX_STATUS = re.compile(r"knowledge_outbox\.py(?:\"|'|\s)+status(?:\s|$)", re.IGNORECASE)
OUTBOX_GRANT = re.compile(
    r"knowledge_outbox\.py(?:\"|'|\s)+grant\s+--accept\s+(?:\"|')?同意(?:\"|')?(?:\s|$)",
    re.IGNORECASE,
)
OUTBOX_REVOKE = re.compile(r"knowledge_outbox\.py(?:\"|'|\s)+revoke(?:\s|$)", re.IGNORECASE)


def _event() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _empty_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "jl_task_active": False,
        "consent_checked": False,
        "consent_granted": False,
        "agreement_reply_seen": False,
        "queried_task_hash": None,
        "knowledge_outcome": None,
    }


def _state_path() -> Path | None:
    plugin_data = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    return Path(plugin_data) / "jl_lifecycle.json" if plugin_data else None


def _valid_state(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != STATE_FIELDS:
        return False
    if value.get("version") != STATE_VERSION:
        return False
    for field in (
        "jl_task_active",
        "consent_checked",
        "consent_granted",
        "agreement_reply_seen",
    ):
        if not isinstance(value.get(field), bool):
            return False
    task_hash = value.get("queried_task_hash")
    if task_hash is not None and (
        not isinstance(task_hash, str)
        or len(task_hash) != 64
        or any(character not in "0123456789abcdef" for character in task_hash)
    ):
        return False
    return value.get("knowledge_outcome") is None or value.get("knowledge_outcome") in OUTCOMES


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if path is None:
        return _empty_state()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    return value if _valid_state(value) else _empty_state()


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    if path is None or not _valid_state(state):
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(state, sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        if os.name != "nt":
            os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    except OSError:
        pass


def _context(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": message,
                }
            },
            ensure_ascii=False,
        )
    )


def _tool_key(tool_name: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(tool_name).lower())


def _tool_is(tool_name: Any, expected: str) -> bool:
    return _tool_key(tool_name).endswith(_tool_key(expected))


def _parse_json_object(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    text = value.strip()
    if len(text) > 65_536 or not text.startswith("{"):
        return None
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _tool_payload(response: Any) -> dict[str, Any] | None:
    """Return a conservative structured success payload without persisting it."""

    envelope = _parse_json_object(response)
    if envelope is None:
        return None
    if envelope.get("isError") is True or envelope.get("is_error") is True:
        return None
    exit_code = envelope.get("exit_code")
    if isinstance(exit_code, int) and exit_code != 0:
        return None

    for key in ("structuredContent", "structured_content"):
        payload = _parse_json_object(envelope.get(key))
        if payload is not None:
            return None if payload.get("ok") is False or "error" in payload else payload

    content = envelope.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                payload = _parse_json_object(item.get("text"))
                if payload is not None:
                    return None if payload.get("ok") is False or "error" in payload else payload

    output = envelope.get("output")
    payload = _parse_json_object(output)
    if payload is not None:
        return None if payload.get("ok") is False or "error" in payload else payload

    return None if envelope.get("ok") is False or "error" in envelope else envelope


def _task_hash(task_id: Any) -> str | None:
    if not isinstance(task_id, str):
        return None
    normalized = task_id.strip()
    if not normalized or len(normalized) > 512:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _record_query(state: dict[str, Any], event: dict[str, Any]) -> None:
    tool_input = event.get("tool_input")
    payload = _tool_payload(event.get("tool_response"))
    if not isinstance(tool_input, dict) or payload is None:
        return
    input_task_id = tool_input.get("task_id")
    task = payload.get("task")
    response_task_id = task.get("task_id") if isinstance(task, dict) else None
    fragments = payload.get("fragments")
    if (
        not isinstance(input_task_id, str)
        or response_task_id != input_task_id
        or not isinstance(fragments, list)
    ):
        return
    task_hash = _task_hash(input_task_id)
    if task_hash is None:
        return
    if state.get("queried_task_hash") not in {None, task_hash}:
        state["knowledge_outcome"] = None
    state["queried_task_hash"] = task_hash
    if fragments:
        if state["knowledge_outcome"] != "solution_candidate":
            state["knowledge_outcome"] = "usage_recorded"
    elif state["knowledge_outcome"] not in {"usage_recorded", "solution_candidate"}:
        state["knowledge_outcome"] = "server_gap"


def _record_submission(state: dict[str, Any], event: dict[str, Any]) -> None:
    tool_input = event.get("tool_input")
    payload = _tool_payload(event.get("tool_response"))
    if not isinstance(tool_input, dict) or payload is None:
        return
    input_task_id = tool_input.get("task_id")
    input_hash = _task_hash(input_task_id)
    candidate = tool_input.get("candidate")
    if (
        input_hash is None
        or input_hash != state.get("queried_task_hash")
        or payload.get("task_id") != input_task_id
        or payload.get("status") != "queued_for_review"
        or not isinstance(candidate, dict)
    ):
        return
    candidate_kind = candidate.get("candidate_kind")
    if candidate_kind == "solution":
        state["knowledge_outcome"] = "solution_candidate"
    elif (
        candidate_kind == "knowledge_gap"
        and state["knowledge_outcome"] not in {"usage_recorded", "solution_candidate"}
    ):
        state["knowledge_outcome"] = "server_gap"


def _record_consent_command(state: dict[str, Any], event: dict[str, Any]) -> bool:
    if not _tool_is(event.get("tool_name"), "Bash"):
        return False
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return False
    command = tool_input.get("command")
    if not isinstance(command, str):
        return False
    payload = _tool_payload(event.get("tool_response"))
    if payload is None:
        return False

    if OUTBOX_REVOKE.search(command):
        state["consent_checked"] = True
        state["consent_granted"] = False
        state["agreement_reply_seen"] = False
        return True
    if OUTBOX_STATUS.search(command) or OUTBOX_GRANT.search(command):
        granted = payload.get("consent_granted")
        if not isinstance(granted, bool):
            return False
        state["consent_checked"] = True
        state["consent_granted"] = granted
        if granted:
            state["agreement_reply_seen"] = False
        return True
    return False


def _prompt_submit(event: dict[str, Any]) -> None:
    prompt = event.get("prompt")
    state = _load_state()
    if isinstance(prompt, str) and prompt.strip() == "同意" and state["jl_task_active"]:
        state["agreement_reply_seen"] = True
        _save_state(state)
        _context(
            "The user supplied the exact agreement phrase for the active task. Record it with "
            "knowledge_outbox.py grant --accept 同意 before any shared tool call. A final answer "
            "cannot close this task until that command and a task-scoped query have actually succeeded."
        )
        return
    if isinstance(prompt, str) and JL_PROMPT.search(prompt):
        state = _empty_state()
        state["jl_task_active"] = True
        _save_state(state)
        _context(
            "Treat this as a substantive Jieli SDK task using the unified bundled workflow; never "
            "ask for a $Skill name. Check the local one-time agreement receipt first. With current "
            "agreement, create one narrow task and run query_task_fragments. The lifecycle hook "
            "accepts only an actual successful MCP result: a hit records usage, an empty hit records "
            "the server gap, and a later successfully queued solution candidate replaces either. "
            "Words in the answer cannot satisfy this closeout."
        )


def _post_tool_use(event: dict[str, Any]) -> None:
    state = _load_state()
    if not state["jl_task_active"]:
        return
    if _record_consent_command(state, event):
        _save_state(state)
        return
    tool_name = event.get("tool_name")
    if _tool_is(tool_name, "query_task_fragments"):
        _record_query(state, event)
    elif _tool_is(tool_name, "submit_knowledge_candidate"):
        _record_submission(state, event)
    _save_state(state)


def _stop(_event_value: dict[str, Any]) -> None:
    state = _load_state()
    if not state["jl_task_active"]:
        print(json.dumps({"continue": True}))
        return
    if not state["consent_checked"]:
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "Check the bundled one-time agreement receipt with knowledge_outbox.py "
                        "status. If it is absent, show the prominent disclosure and ask the user "
                        "to enter the exact phrase 同意; do not call shared tools yet."
                    ),
                },
                ensure_ascii=False,
            )
        )
        return
    if not state["consent_granted"]:
        if state["agreement_reply_seen"]:
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": (
                            "The user entered the exact agreement phrase. Run knowledge_outbox.py "
                            "grant --accept 同意 and verify its successful consent receipt before "
                            "using the shared service or finishing this task."
                        ),
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(json.dumps({"continue": True}))
        return
    if state["knowledge_outcome"] not in OUTCOMES:
        print(
            json.dumps(
                {
                    "decision": "block",
                    "reason": (
                        "This task has no verified knowledge closeout. Complete a successful "
                        "task-scoped query_task_fragments call. A hit records usage_recorded and "
                        "an empty result records server_gap. If local work produced reusable "
                        "knowledge, successfully queue one sanitized solution candidate so the "
                        "final state becomes solution_candidate. Answer wording never counts."
                    ),
                },
                ensure_ascii=False,
            )
        )
        return
    state["jl_task_active"] = False
    _save_state(state)
    print(json.dumps({"continue": True}))


def main() -> int:
    event = _event()
    name = event.get("hook_event_name")
    if name == "UserPromptSubmit":
        _prompt_submit(event)
    elif name == "PostToolUse":
        _post_tool_use(event)
    elif name == "Stop":
        _stop(event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
