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


STATE_VERSION = 3
OUTCOMES = {"usage_recorded", "solution_candidate", "server_gap"}
STATE_FIELDS = {
    "version",
    "jl_task_active",
    "consent_checked",
    "consent_granted",
    "agreement_reply_seen",
    "queried_task_hash",
    "knowledge_outcome",
    "work_revision",
    "candidate_revision",
    "diagnosis_marker_required",
    "read_only_outcome",
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
OUTBOX_ENQUEUE = re.compile(r"knowledge_outbox\.py(?:\"|'|\s)+enqueue(?:\s|$)", re.IGNORECASE)
OUTBOX_MARK = re.compile(
    r"knowledge_outbox\.py(?:\"|'|\s)+mark-outcome\s+--(reusable|none)(?:\s|$)",
    re.IGNORECASE,
)
SHELL_WORK = re.compile(
    r"(?:^|[;&|]\s*)(?:"
    r"make(?:\.exe)?(?:\s|$)|ninja(?:\.exe)?(?:\s|$)|cmake(?:\.exe)?\s+--build(?:\s|$)|"
    r"(?:bash|sh)\s+[^;&|]*(?:build|compile)[^;&|]*\.sh(?:\s|$)|"
    r"[^;&|]*(?:build|compile)[^;&|]*\.(?:bat|cmd)(?:\s|$)|"
    r"git\s+apply(?:\s|$)|patch(?:\s|$)|sed\s+-i(?:\s|$)|"
    r"(?:copy|move|ren|rename|set-content|add-content)\s+"
    r")",
    re.IGNORECASE,
)
STRUCTURED_WORK_TOOLS = {
    "applypatch",
    "edit",
    "multiedit",
    "notebookedit",
    "replace",
    "write",
    "writefile",
}
READ_ONLY_TOOLS = {
    "glob",
    "grep",
    "listdirectory",
    "read",
    "readfile",
    "readmanyfiles",
    "search",
    "searchfilecontent",
}
SHELL_READ = re.compile(
    r"(?:^|[;&|]\s*)(?:rg|grep|findstr|select-string|get-content)(?:\.exe)?(?:\s|$)",
    re.IGNORECASE,
)


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
        "work_revision": 0,
        "candidate_revision": 0,
        "diagnosis_marker_required": False,
        "read_only_outcome": None,
    }


def _state_path(event: dict[str, Any] | None = None) -> Path | None:
    plugin_data = (
        os.environ.get("PLUGIN_DATA")
        or os.environ.get("ZCODE_PLUGIN_DATA")
        or os.environ.get("CLAUDE_PLUGIN_DATA")
        or os.environ.get("JL_KNOWLEDGE_CLIENT_HOME")
    )
    filename = "jl_lifecycle.json"
    session_id = (event or {}).get("session_id")
    if isinstance(session_id, str) and session_id.strip():
        digest = hashlib.sha256(session_id.strip().encode("utf-8")).hexdigest()[:24]
        filename = f"jl_lifecycle.{digest}.json"
    if plugin_data:
        return Path(plugin_data).expanduser() / filename

    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state).expanduser() / "jl-knowledge-base-skill" / filename
    local_app_data = os.environ.get("LOCALAPPDATA")
    if os.name == "nt" and local_app_data:
        return Path(local_app_data) / "JLPrivateKnowledgeClient" / filename
    try:
        return Path.home() / ".local" / "state" / "jl-knowledge-base-skill" / filename
    except (OSError, RuntimeError):
        return None


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
        "diagnosis_marker_required",
    ):
        if not isinstance(value.get(field), bool):
            return False
    for field in ("work_revision", "candidate_revision"):
        if not isinstance(value.get(field), int) or value[field] < 0:
            return False
    if value["candidate_revision"] > value["work_revision"]:
        return False
    if value.get("read_only_outcome") not in {None, "reusable", "none"}:
        return False
    task_hash = value.get("queried_task_hash")
    if task_hash is not None and (
        not isinstance(task_hash, str)
        or len(task_hash) != 64
        or any(character not in "0123456789abcdef" for character in task_hash)
    ):
        return False
    return value.get("knowledge_outcome") is None or value.get("knowledge_outcome") in OUTCOMES


def _load_state(event: dict[str, Any]) -> dict[str, Any]:
    path = _state_path(event)
    if path is None:
        return _empty_state()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    return value if _valid_state(value) else _empty_state()


def _save_state(state: dict[str, Any], event: dict[str, Any]) -> None:
    path = _state_path(event)
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


def _context(message: str, event_name: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event_name,
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


def _nested_payload(value: Any, *, depth: int = 0) -> dict[str, Any] | None:
    """Find one structured JSON object in supported client tool envelopes."""

    if depth > 5:
        return None
    parsed = _parse_json_object(value)
    if parsed is not None and not isinstance(value, dict):
        return _nested_payload(parsed, depth=depth + 1)
    if isinstance(value, list):
        for item in value[:32]:
            payload = _nested_payload(item, depth=depth + 1)
            if payload is not None:
                return payload
        return None
    if not isinstance(value, dict):
        return None
    if value.get("isError") is True or value.get("is_error") is True or value.get("error"):
        return None
    if value.get("ok") is False:
        return None

    for key in (
        "structuredContent",
        "structured_content",
        "llmContent",
        "returnDisplay",
        "content",
        "output",
        "text",
    ):
        if key in value:
            payload = _nested_payload(value.get(key), depth=depth + 1)
            if payload is not None:
                return payload
    return value


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

    return _nested_payload(envelope)


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
        state["candidate_revision"] = 0
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
        state["candidate_revision"] = state["work_revision"]
        state["diagnosis_marker_required"] = False
        state["read_only_outcome"] = "reusable"
    elif (
        candidate_kind == "knowledge_gap"
        and state["knowledge_outcome"] not in {"usage_recorded", "solution_candidate"}
    ):
        state["knowledge_outcome"] = "server_gap"


def _record_consent_command(state: dict[str, Any], event: dict[str, Any]) -> bool:
    tool_name = event.get("tool_name")
    if not (
        _tool_is(tool_name, "Bash")
        or _tool_is(tool_name, "run_shell_command")
    ):
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


def _record_outcome_marker(state: dict[str, Any], event: dict[str, Any]) -> bool:
    tool_name = event.get("tool_name")
    if not (
        _tool_is(tool_name, "Bash")
        or _tool_is(tool_name, "run_shell_command")
    ):
        return False
    tool_input = event.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    match = OUTBOX_MARK.search(command) if isinstance(command, str) else None
    if match is None:
        return False
    payload = _tool_payload(event.get("tool_response"))
    marker = match.group(1).lower()
    if payload is None or payload.get("outcome_marker") != marker:
        return False
    state["diagnosis_marker_required"] = False
    state["read_only_outcome"] = marker
    if marker == "reusable":
        state["work_revision"] += 1
    return True


def _tool_succeeded(event: dict[str, Any]) -> bool:
    response = event.get("tool_response")
    if not isinstance(response, dict):
        return response is not None
    if response.get("isError") is True or response.get("is_error") is True:
        return False
    if response.get("error"):
        return False
    exit_code = response.get("exit_code")
    return not isinstance(exit_code, int) or exit_code == 0


def _record_work_revision(state: dict[str, Any], event: dict[str, Any]) -> None:
    if not _tool_succeeded(event):
        return
    tool_name = event.get("tool_name")
    tool_key = _tool_key(tool_name)
    is_work = any(tool_key.endswith(expected) for expected in STRUCTURED_WORK_TOOLS)
    tool_input = event.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if isinstance(command, str):
        if OUTBOX_ENQUEUE.search(command):
            payload = _tool_payload(event.get("tool_response"))
            is_work = bool(payload and payload.get("queued") is True)
        elif SHELL_WORK.search(command):
            is_work = True
    if is_work:
        state["work_revision"] += 1


def _record_read_only_evidence(state: dict[str, Any], event: dict[str, Any]) -> None:
    if not _tool_succeeded(event):
        return
    tool_key = _tool_key(event.get("tool_name"))
    is_read = any(tool_key.endswith(expected) for expected in READ_ONLY_TOOLS)
    tool_input = event.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if isinstance(command, str) and SHELL_READ.search(command):
        is_read = True
    if is_read:
        state["diagnosis_marker_required"] = True
        state["read_only_outcome"] = None


def _prompt_submit(event: dict[str, Any]) -> None:
    prompt = event.get("prompt")
    event_name = str(event.get("hook_event_name") or "UserPromptSubmit")
    state = _load_state(event)
    if isinstance(prompt, str) and prompt.strip() == "同意" and state["jl_task_active"]:
        state["agreement_reply_seen"] = True
        _save_state(state, event)
        _context(
            "The user supplied the exact agreement phrase for the active task. Record it with "
            "knowledge_outbox.py grant --accept 同意 before any shared tool call. A final answer "
            "cannot close this task until that command and a task-scoped query have actually succeeded.",
            event_name,
        )
        return
    if isinstance(prompt, str) and JL_PROMPT.search(prompt):
        if not state["jl_task_active"]:
            state = _empty_state()
            state["jl_task_active"] = True
            _save_state(state, event)
        _context(
            "Treat this as a substantive Jieli SDK task using the unified bundled workflow; never "
            "ask for a $Skill name. Check the local one-time agreement receipt first. With current "
            "agreement, create one narrow task and run query_task_fragments. The lifecycle hook "
            "accepts only an actual successful MCP result: a hit records usage, an empty hit records "
            "the server gap, and a later successfully queued solution candidate replaces either. "
            "After read-only local diagnosis, record a structured mark-outcome --reusable or --none; "
            "reusable requires an accepted solution candidate. Words in the answer cannot satisfy "
            "this closeout.",
            event_name,
        )


def _post_tool_use(event: dict[str, Any]) -> None:
    state = _load_state(event)
    if not state["jl_task_active"]:
        return
    if _record_consent_command(state, event):
        _save_state(state, event)
        return
    if _record_outcome_marker(state, event):
        _save_state(state, event)
        return
    tool_name = event.get("tool_name")
    if _tool_is(tool_name, "query_task_fragments"):
        _record_query(state, event)
    elif _tool_is(tool_name, "submit_knowledge_candidate"):
        _record_submission(state, event)
    else:
        _record_work_revision(state, event)
        _record_read_only_evidence(state, event)
    _save_state(state, event)


def _blocking_result(event: dict[str, Any], reason: str) -> None:
    decision = "deny" if event.get("hook_event_name") == "AfterAgent" else "block"
    print(json.dumps({"decision": decision, "reason": reason}, ensure_ascii=False))


def _stop(event: dict[str, Any]) -> None:
    state = _load_state(event)
    if not state["jl_task_active"]:
        print(json.dumps({"continue": True}))
        return
    if not state["consent_checked"]:
        _blocking_result(
            event,
            "Check the bundled one-time agreement receipt with knowledge_outbox.py "
            "status. If it is absent, show the prominent disclosure and ask the user "
            "to enter the exact phrase 同意; do not call shared tools yet.",
        )
        return
    if not state["consent_granted"]:
        if state["agreement_reply_seen"]:
            _blocking_result(
                event,
                "The user entered the exact agreement phrase. Run knowledge_outbox.py "
                "grant --accept 同意 and verify its successful consent receipt before "
                "using the shared service or finishing this task.",
            )
        else:
            print(json.dumps({"continue": True}))
        return
    if state["knowledge_outcome"] not in OUTCOMES:
        _blocking_result(
            event,
            "This task has no verified knowledge closeout. Complete a successful "
            "task-scoped query_task_fragments call. A hit records usage_recorded and "
            "an empty result records server_gap. If local work produced reusable "
            "knowledge, successfully queue one sanitized solution candidate so the "
            "final state becomes solution_candidate. Answer wording never counts.",
        )
        return
    if state["diagnosis_marker_required"]:
        _blocking_result(
            event,
            "Local project evidence was read after the last structured diagnosis marker. Run "
            "knowledge_outbox.py mark-outcome --reusable when that inspection established a "
            "reusable result, or mark-outcome --none when it did not. Do not infer this from answer "
            "wording. A reusable marker must then be followed by an accepted solution candidate.",
        )
        return
    if state["work_revision"] > state["candidate_revision"]:
        _blocking_result(
            event,
            "The current task changed project content, ran a real build, or prepared a structured "
            "reusable finding after its last accepted candidate. Enqueue and successfully submit "
            "one fresh sanitized solution candidate for the latest work revision before finishing. "
            "A previous query or candidate cannot close later engineering work.",
        )
        return
    state["jl_task_active"] = False
    _save_state(state, event)
    print(json.dumps({"continue": True}))


def main() -> int:
    event = _event()
    name = event.get("hook_event_name")
    if name in {"UserPromptSubmit", "BeforeAgent"}:
        _prompt_submit(event)
    elif name in {"PostToolUse", "AfterTool"}:
        _post_tool_use(event)
    elif name in {"Stop", "AfterAgent"}:
        _stop(event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
