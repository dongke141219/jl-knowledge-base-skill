#!/usr/bin/env python3
"""Coordinate one bounded shared-knowledge workflow for confirmed JL projects.

The hook uses a bounded local filename scan to identify Jieli SDK projects. It
never opens source files or a transcript and persists no prompt, tool input,
tool output, task identifier, fragment, source, log, or project path. Only
booleans, enums, counters, and one-way hashes are stored in local client state.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


STATE_VERSION = 5
CLIENT_VERSION = "0.8.0"
CLIENT_UPDATE_ACTION = "run_bundled_updater_v1"
CLIENT_MANUAL_UPDATE_ACTION = "manual_upgrade_required"
PROJECT_STATES = {"unknown", "ambiguous", "confirmed", "non_jl"}
OUTCOMES = {
    "usage_recorded",
    "server_gap",
    "query_unavailable",
    "solution_candidate",
    "local_only",
}
STATE_FIELDS = {
    "version",
    "workspace_hash",
    "project_state",
    "project_confirmation_pending",
    "project_confirmed_by_user",
    "jl_task_active",
    "consent_checked",
    "consent_granted",
    "agreement_reply_seen",
    "create_attempted",
    "create_succeeded",
    "query_attempted",
    "queried_task_hash",
    "knowledge_outcome",
    "candidate_attempt_count",
    "candidate_attempt_hashes",
    "accepted_candidate_hash",
    "candidate_already_uploaded",
    "closeout_prompted",
    "local_only_selected",
    "update_target_version",
    "update_prompted",
    "update_attempted",
    "update_reported",
}

# These words may indicate that clarification is useful, but never prove that
# a project belongs to Jieli. Platform confirmation comes from local project
# signatures or an explicit user answer.
JL_PLATFORM_HINT = re.compile(
    r"(?:\bjieli\b|杰理|\bjl\s*[-_ ]?sdk\b|\b(?:ac|jl)\d{3,5}[a-z]*\b|\bbr\d{2,4}\b)",
    re.IGNORECASE,
)
ENGINEERING_TASK_HINT = re.compile(
    r"(?:实现|修改|改一下|调整|新增|增加|删除|优化|修复|解决|处理|排查|检查|分析|诊断|编译|构建|烧录|适配|配置|迁移|移植|升级|"
    r"功能|问题|异常|失败|报错|无效|不生效|为什么|怎么|如何|日志|源码|代码|固件|SDK|"
    r"按键|灯效|充电|蓝牙|TWS|ANC|通透|音频|麦克风|功耗|协议|APP|"
    r"\b(?:implement|fix|debug|diagnose|build|compile|configure|migrate|firmware|sdk)\b)",
    re.IGNORECASE,
)
EXPLICIT_JL_PROJECT = re.compile(
    r"(?:这是|就是|确认(?:是|为)?|属于|基于|使用|当前(?:项目|工程)(?:是|属于))"
    r"[^\r\n]{0,16}(?:杰理|jieli|jl\s*[-_ ]?sdk)[^\r\n]{0,12}(?:项目|工程|sdk)?",
    re.IGNORECASE,
)
PROJECT_CONFIRM_REPLIES = {
    "是",
    "是的",
    "对",
    "对的",
    "确认",
    "没错",
    "确认是杰理项目",
    "这是杰理项目",
    "属于杰理项目",
}
PROJECT_REJECT_REPLIES = {"否", "不是", "不是的", "不是杰理项目", "不属于杰理项目"}
CONSENT_DECLINE_REPLIES = {"不同意", "拒绝", "不同意，继续本地处理", "不同意继续本地处理"}

OUTBOX_STATUS = re.compile(r"knowledge_outbox\.py(?:\"|'|\s)+status(?:\s|$)", re.IGNORECASE)
OUTBOX_GRANT = re.compile(
    r"knowledge_outbox\.py(?:\"|'|\s)+grant\s+--accept\s+(?:\"|')?同意(?:\"|')?(?:\s|$)",
    re.IGNORECASE,
)
OUTBOX_REVOKE = re.compile(r"knowledge_outbox\.py(?:\"|'|\s)+revoke(?:\s|$)", re.IGNORECASE)
OUTBOX_ENQUEUE = re.compile(r"knowledge_outbox\.py(?:\"|'|\s)+enqueue(?:\s|$)", re.IGNORECASE)
CLIENT_UPDATE_COMMAND = re.compile(
    r"client_update\.py(?:\"|'|\s).*(?:--action-id(?:=|\s+)(?:\"|')?run_bundled_updater_v1)",
    re.IGNORECASE,
)

SKIPPED_SCAN_DIRS = {
    ".git",
    ".svn",
    ".hg",
    ".codex",
    "node_modules",
    "build",
    "dist",
    "output",
    "out",
}
JL_PROJECT_FILENAMES = {"sdk_config.h", "jlstream_node_cfg.h"}
JL_CPU_DIR = re.compile(r"^br\d{2,4}$", re.IGNORECASE)


def _event() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def _empty_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "workspace_hash": None,
        "project_state": "unknown",
        "project_confirmation_pending": False,
        "project_confirmed_by_user": False,
        "jl_task_active": False,
        "consent_checked": False,
        "consent_granted": False,
        "agreement_reply_seen": False,
        "create_attempted": False,
        "create_succeeded": False,
        "query_attempted": False,
        "queried_task_hash": None,
        "knowledge_outcome": None,
        "candidate_attempt_count": 0,
        "candidate_attempt_hashes": [],
        "accepted_candidate_hash": None,
        "candidate_already_uploaded": False,
        "closeout_prompted": False,
        "local_only_selected": False,
        "update_target_version": None,
        "update_prompted": False,
        "update_attempted": False,
        "update_reported": False,
    }


def _reset_task_fields(state: dict[str, Any], *, active: bool) -> None:
    state["jl_task_active"] = active
    state["consent_checked"] = False
    state["consent_granted"] = False
    state["agreement_reply_seen"] = False
    state["create_attempted"] = False
    state["create_succeeded"] = False
    state["query_attempted"] = False
    state["queried_task_hash"] = None
    state["knowledge_outcome"] = None
    state["candidate_attempt_count"] = 0
    state["candidate_attempt_hashes"] = []
    state["accepted_candidate_hash"] = None
    state["candidate_already_uploaded"] = False
    state["closeout_prompted"] = False
    state["local_only_selected"] = False


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


def _is_hash(value: Any) -> bool:
    return bool(
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _valid_state(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != STATE_FIELDS:
        return False
    if value.get("version") != STATE_VERSION or value.get("project_state") not in PROJECT_STATES:
        return False
    for field in (
        "project_confirmation_pending",
        "project_confirmed_by_user",
        "jl_task_active",
        "consent_checked",
        "consent_granted",
        "agreement_reply_seen",
        "create_attempted",
        "create_succeeded",
        "query_attempted",
        "candidate_already_uploaded",
        "closeout_prompted",
        "local_only_selected",
        "update_prompted",
        "update_attempted",
        "update_reported",
    ):
        if not isinstance(value.get(field), bool):
            return False
    if value["project_confirmation_pending"] and value["project_state"] != "ambiguous":
        return False
    if value["create_succeeded"] and not value["create_attempted"]:
        return False
    if not isinstance(value.get("candidate_attempt_count"), int):
        return False
    if not 0 <= value["candidate_attempt_count"] <= 1:
        return False
    attempt_hashes = value.get("candidate_attempt_hashes")
    if not isinstance(attempt_hashes, list) or len(attempt_hashes) > 1:
        return False
    if len(set(attempt_hashes)) != len(attempt_hashes) or not all(_is_hash(item) for item in attempt_hashes):
        return False
    for field in ("workspace_hash", "queried_task_hash", "accepted_candidate_hash"):
        if value.get(field) is not None and not _is_hash(value.get(field)):
            return False
    update_target = value.get("update_target_version")
    if update_target is not None and (
        not isinstance(update_target, str)
        or re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", update_target)
        is None
    ):
        return False
    if value["update_attempted"] and not value["update_prompted"]:
        return False
    if value["update_reported"] and not value["update_attempted"]:
        return False
    if value["update_prompted"] and update_target is None:
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
            {"hookSpecificOutput": {"hookEventName": event_name, "additionalContext": message}},
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
    envelope = _parse_json_object(response)
    if envelope is None:
        return None
    if envelope.get("isError") is True or envelope.get("is_error") is True:
        return None
    exit_code = envelope.get("exit_code")
    if isinstance(exit_code, int) and exit_code != 0:
        return None
    return _nested_payload(envelope)


def _version_tuple(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)",
        value.strip(),
    )
    if match is None:
        return None
    return tuple(int(match.group(index)) for index in range(1, 4))


def _valid_update_report(value: Any, target_version: str) -> bool:
    required = {
        "client_version",
        "attempt_id",
        "client_kind",
        "from_version",
        "target_version",
        "observed_version",
        "action_id",
        "outcome",
        "stage",
        "reason_code",
        "repaired",
    }
    return bool(
        isinstance(value, dict)
        and set(value) == required
        and value.get("client_version") == CLIENT_VERSION
        and value.get("from_version") == CLIENT_VERSION
        and value.get("target_version") == target_version
        and value.get("action_id") == CLIENT_UPDATE_ACTION
        and value.get("client_kind") in {"codex", "gemini", "zcode"}
        and value.get("outcome") in {"success", "failed", "manual_required"}
        and isinstance(value.get("repaired"), bool)
        and re.fullmatch(r"[a-f0-9]{32}", str(value.get("attempt_id") or "")) is not None
    )


def _task_hash(task_id: Any) -> str | None:
    if not isinstance(task_id, str):
        return None
    normalized = task_id.strip()
    if not normalized or len(normalized) > 512:
        return None
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _candidate_hash(candidate: Any) -> str | None:
    if not isinstance(candidate, dict):
        return None
    try:
        encoded = json.dumps(
            candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    if len(encoded) > 64 * 1024:
        return None
    return hashlib.sha256(encoded).hexdigest()


def _event_workspace(event: dict[str, Any]) -> Path:
    for key in ("cwd", "working_directory", "workspace_root", "project_dir"):
        value = event.get(key)
        if isinstance(value, str) and value.strip() and len(value) <= 4096:
            candidate = Path(value).expanduser()
            if candidate.is_dir():
                return candidate
    return Path.cwd()


def _workspace_hash(path: Path) -> str:
    try:
        text = str(path.resolve())
    except OSError:
        text = str(path.absolute())
    return hashlib.sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest()


def _child(parent: Path, name: str, *, directory: bool | None = None) -> Path | None:
    try:
        with os.scandir(parent) as entries:
            for index, entry in enumerate(entries):
                if index >= 512:
                    break
                if entry.name.casefold() != name.casefold() or entry.is_symlink():
                    continue
                if directory is True and not entry.is_dir(follow_symlinks=False):
                    continue
                if directory is False and not entry.is_file(follow_symlinks=False):
                    continue
                return Path(entry.path)
    except OSError:
        return None
    return None


def _bounded_signature_scan(root: Path) -> tuple[bool, bool, bool]:
    """Return whether .jlproj, .x6flow, and known JL config names exist."""

    found_jlproj = False
    found_x6flow = False
    found_config = False
    stack: list[tuple[Path, int]] = [(root, 0)]
    visited = 0
    while stack and visited < 1200:
        directory, depth = stack.pop()
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    visited += 1
                    if visited >= 1200:
                        break
                    name = entry.name.casefold()
                    if entry.is_symlink():
                        continue
                    if entry.is_file(follow_symlinks=False):
                        if name.endswith(".jlproj"):
                            found_jlproj = True
                        elif name.endswith(".x6flow"):
                            found_x6flow = True
                        elif name in JL_PROJECT_FILENAMES:
                            found_config = True
                    elif depth < 3 and entry.is_dir(follow_symlinks=False) and name not in SKIPPED_SCAN_DIRS:
                        stack.append((Path(entry.path), depth + 1))
        except OSError:
            continue
        if found_jlproj and found_x6flow and found_config:
            break
    return found_jlproj, found_x6flow, found_config


def _direct_signature_scan(root: Path) -> tuple[bool, bool, bool]:
    found_jlproj = False
    found_x6flow = False
    found_config = False
    try:
        with os.scandir(root) as entries:
            for index, entry in enumerate(entries):
                if index >= 512:
                    break
                if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                    continue
                name = entry.name.casefold()
                found_jlproj = found_jlproj or name.endswith(".jlproj")
                found_x6flow = found_x6flow or name.endswith(".x6flow")
                found_config = found_config or name in JL_PROJECT_FILENAMES
    except OSError:
        pass
    return found_jlproj, found_x6flow, found_config


def _anchor_score(anchor: Path, *, scan_descendants: bool) -> int:
    sdk = _child(anchor, "SDK", directory=True)
    roots = [sdk] if sdk is not None else []
    roots.append(anchor)
    best = 0
    for root in roots:
        score = 1 if sdk is not None and root == sdk else 0
        makefile = _child(root, "Makefile", directory=False)
        cpu = _child(root, "cpu", directory=True)
        apps = _child(root, "apps", directory=True)
        include_lib = _child(root, "include_lib", directory=True)
        vscode = _child(root, ".vscode", directory=True)
        winmk = _child(vscode, "winmk.bat", directory=False) if vscode else None
        if makefile:
            score += 1
        if cpu:
            score += 2
            try:
                with os.scandir(cpu) as entries:
                    if any(
                        JL_CPU_DIR.fullmatch(entry.name) and entry.is_dir(follow_symlinks=False)
                        for index, entry in enumerate(entries)
                        if index < 128 and not entry.is_symlink()
                    ):
                        score += 2
            except OSError:
                pass
        if apps or include_lib:
            score += 1
        if winmk:
            score += 3
        best = max(best, score)
    direct_jlproj, direct_x6flow, direct_config = _direct_signature_scan(anchor)
    if direct_jlproj:
        best += 5
    if direct_x6flow:
        best += 2
    if direct_config:
        best += 1
    if scan_descendants:
        nested_jlproj, nested_x6flow, nested_config = _bounded_signature_scan(anchor)
        if nested_jlproj and not direct_jlproj:
            best += 2
        if nested_x6flow and not direct_x6flow:
            best += 1
        if nested_config and not direct_config:
            best += 1
    return best


def _detect_jl_project(workspace: Path) -> tuple[str, Path]:
    candidates = [workspace]
    candidates.extend(list(workspace.parents)[:4])
    best_score = 0
    best_anchor = workspace
    for index, anchor in enumerate(candidates):
        if not anchor.is_dir():
            continue
        score = _anchor_score(anchor, scan_descendants=index == 0)
        if score > best_score:
            best_score = score
            best_anchor = anchor
        if score >= 5:
            return "confirmed", anchor
    if best_score >= 2:
        return "ambiguous", best_anchor
    return "unknown", workspace


def _activate_task(state: dict[str, Any]) -> None:
    _reset_task_fields(state, active=True)
    state["project_state"] = "confirmed"
    state["project_confirmation_pending"] = False


def _workflow_context(event_name: str, *, resumed: bool = False) -> None:
    prefix = "Resume" if resumed else "Handle"
    _context(
        f"{prefix} this as a confirmed Jieli SDK project task. Classify the request as a feature or issue: "
        "product -> domain -> capability -> subfeature/problem -> boundary. Check the local consent receipt. "
        "With current consent, create one narrow task and query at most once. Use only relevant returned "
        "fragments as reference; on a miss, unrelated result, or outage, continue local work without retrying. "
        "Finish all local work, then assess value once. Submit at most one sanitized solution only for a "
        "genuinely new reusable conclusion produced locally. Never submit returned knowledge, source, logs, "
        "paths, identities, keys, credentials, or private payloads.",
        event_name,
    )


def _prompt_submit(event: dict[str, Any]) -> None:
    prompt = event.get("prompt")
    if not isinstance(prompt, str):
        return
    event_name = str(event.get("hook_event_name") or "UserPromptSubmit")
    normalized = prompt.strip()
    state = _load_state(event)
    workspace = _event_workspace(event)
    detected, anchor = _detect_jl_project(workspace)
    current_workspace_hash = _workspace_hash(anchor if detected != "unknown" else workspace)
    if state["workspace_hash"] not in {None, current_workspace_hash}:
        state = _empty_state()
    state["workspace_hash"] = current_workspace_hash

    if normalized == "同意" and state["jl_task_active"]:
        state["agreement_reply_seen"] = True
        state["local_only_selected"] = False
        _save_state(state, event)
        _context(
            "The user supplied the exact agreement phrase for the active confirmed-JL task. Record it with "
            "knowledge_outbox.py grant --accept 同意 before any shared call. Then classify the pending question "
            "and make at most one narrow query. A gateway failure must fall back to local work, not repeat forever.",
            event_name,
        )
        return

    if state["project_confirmation_pending"]:
        folded = normalized.casefold()
        if folded in {item.casefold() for item in PROJECT_CONFIRM_REPLIES} or EXPLICIT_JL_PROJECT.search(normalized):
            state["project_state"] = "confirmed"
            state["project_confirmed_by_user"] = True
            _activate_task(state)
            _save_state(state, event)
            _workflow_context(event_name, resumed=True)
            return
        if folded in {item.casefold() for item in PROJECT_REJECT_REPLIES}:
            state["project_state"] = "non_jl"
            state["project_confirmation_pending"] = False
            _reset_task_fields(state, active=False)
            _save_state(state, event)
            _context(
                "The user confirmed that this is not a Jieli SDK project. Do not use the JL shared-knowledge "
                "workflow for this workspace; continue with ordinary local assistance.",
                event_name,
            )
            return
        _save_state(state, event)
        _context(
            "Project ownership is still ambiguous. Ask only whether the current project is a Jieli/JL SDK "
            "project. Do not call the JL shared service before confirmation.",
            event_name,
        )
        return

    if state["jl_task_active"]:
        if not state["consent_granted"] and normalized.casefold() in {
            item.casefold() for item in CONSENT_DECLINE_REPLIES
        }:
            state["local_only_selected"] = True
            _save_state(state, event)
            _context(
                "The user declined shared knowledge. Continue this task from authorized local project evidence "
                "only; do not create, query, enqueue, or submit shared knowledge.",
                event_name,
            )
        return

    if EXPLICIT_JL_PROJECT.search(normalized):
        state["project_state"] = "confirmed"
        state["project_confirmed_by_user"] = True
    elif detected == "confirmed":
        state["project_state"] = "confirmed"
        state["project_confirmed_by_user"] = False
    elif state["project_state"] == "non_jl":
        _save_state(state, event)
        return
    elif state["project_state"] != "confirmed":
        if ENGINEERING_TASK_HINT.search(normalized) and (
            detected == "ambiguous" or JL_PLATFORM_HINT.search(normalized)
        ):
            state["project_state"] = "ambiguous"
            state["project_confirmation_pending"] = True
            _save_state(state, event)
            _context(
                "The request may concern a Jieli SDK, but keywords alone do not prove project ownership. Ask one "
                "short question: 当前工程是否为杰理 SDK 项目？ Do not call the shared service yet.",
                event_name,
            )
            return
        _save_state(state, event)
        return

    if ENGINEERING_TASK_HINT.search(normalized):
        _activate_task(state)
        _save_state(state, event)
        _workflow_context(event_name)
    else:
        _save_state(state, event)


def _blocking_result(event: dict[str, Any], reason: str) -> None:
    name = str(event.get("hook_event_name") or "")
    decision = "deny" if name in {"BeforeTool", "AfterAgent"} else "block"
    print(json.dumps({"decision": decision, "reason": reason}, ensure_ascii=False))


def _pre_tool_use(event: dict[str, Any]) -> None:
    state = _load_state(event)
    if not state["jl_task_active"]:
        return
    tool_name = event.get("tool_name")
    if _tool_is(tool_name, "report_client_update"):
        tool_input = event.get("tool_input")
        target = state.get("update_target_version")
        if (
            not state["update_attempted"]
            or not isinstance(target, str)
            or not _valid_update_report(tool_input, target)
        ):
            _blocking_result(
                event,
                "Only report the exact fixed-enum result returned by the bundled client updater for the "
                "server-advertised target. Never add paths, commands, raw output, device names, or identity.",
            )
            return
        if state["update_reported"]:
            _blocking_result(event, "This update attempt was already reported. Continue the local task.")
        return
    if any(
        _tool_is(tool_name, expected)
        for expected in ("create_knowledge_task", "query_task_fragments", "submit_knowledge_candidate")
    ) and (not state["consent_checked"] or not state["consent_granted"]):
        _blocking_result(
            event,
            "Shared JL knowledge requires a current local consent receipt. Check status and obtain the user's "
            "exact 同意 when needed; otherwise continue local-only work.",
        )
        return
    if _tool_is(tool_name, "create_knowledge_task"):
        if state["create_attempted"]:
            _blocking_result(event, "This task already attempted its one server-task creation. Continue locally.")
            return
        state["create_attempted"] = True
        _save_state(state, event)
        return
    if _tool_is(tool_name, "query_task_fragments"):
        if not state["create_succeeded"]:
            _blocking_result(event, "No server task was created successfully. Continue locally without querying.")
            return
        if state["query_attempted"]:
            _blocking_result(event, "This task already used its one scoped knowledge query. Continue locally.")
            return
        state["query_attempted"] = True
        _save_state(state, event)
        return
    if _tool_is(tool_name, "submit_knowledge_candidate"):
        tool_input = event.get("tool_input")
        candidate = tool_input.get("candidate") if isinstance(tool_input, dict) else None
        fingerprint = _candidate_hash(candidate)
        if state["candidate_already_uploaded"]:
            _blocking_result(event, "The local receipt shows this reusable result was already uploaded. Finish without resubmitting.")
            return
        if state["queried_task_hash"] is None:
            _blocking_result(event, "No valid scoped query exists for this server task. Finish locally without submitting.")
            return
        if not isinstance(candidate, dict) or candidate.get("candidate_kind") != "solution":
            _blocking_result(event, "Only one new, sanitized candidate_kind: solution may be submitted after final assessment.")
            return
        if state["accepted_candidate_hash"] is not None:
            _blocking_result(event, "This task already submitted one accepted solution candidate. Do not resubmit it.")
            return
        if fingerprint is not None and fingerprint in state["candidate_attempt_hashes"]:
            _blocking_result(event, "The same candidate fingerprint was already attempted in this task. Do not retry it now.")
            return
        if state["candidate_attempt_count"] >= 1:
            _blocking_result(event, "This task reached its bounded candidate-attempt limit. Preserve safe local work and finish.")
            return
        state["candidate_attempt_count"] += 1
        if fingerprint is not None:
            state["candidate_attempt_hashes"].append(fingerprint)
        _save_state(state, event)


def _record_consent_command(state: dict[str, Any], event: dict[str, Any]) -> bool:
    tool_name = event.get("tool_name")
    if not any(
        _tool_is(tool_name, expected)
        for expected in ("Bash", "Shell", "exec_command", "run_shell_command")
    ):
        return False
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return False
    command = tool_input.get("command") or tool_input.get("cmd")
    if not isinstance(command, str):
        return False
    payload = _tool_payload(event.get("tool_response"))
    if payload is None:
        return False
    if OUTBOX_REVOKE.search(command):
        state["consent_checked"] = True
        state["consent_granted"] = False
        state["agreement_reply_seen"] = False
        state["local_only_selected"] = True
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
    if OUTBOX_ENQUEUE.search(command) and payload.get("already_uploaded") is True:
        state["candidate_already_uploaded"] = True
        return True
    return False


def _record_client_update_notice(
    state: dict[str, Any], event: dict[str, Any], payload: dict[str, Any] | None
) -> bool:
    if not isinstance(payload, dict):
        return False
    notice = payload.get("client_update")
    if not isinstance(notice, dict) or notice.get("update_available") is not True:
        return False
    target = notice.get("latest_version")
    current = _version_tuple(CLIENT_VERSION)
    target_tuple = _version_tuple(target)
    action_id = notice.get("action_id")
    if current is None or target_tuple is None or target_tuple <= current:
        return False
    if action_id not in {CLIENT_UPDATE_ACTION, CLIENT_MANUAL_UPDATE_ACTION}:
        return False
    if state["update_prompted"]:
        return False
    state["update_target_version"] = str(target)
    state["update_prompted"] = True
    event_name = str(event.get("hook_event_name") or "PostToolUse")
    if action_id == CLIENT_UPDATE_ACTION and notice.get("automatic_update_eligible") is True:
        _context(
            f"The server reports JL Knowledge Base Skill {target}. Run the installed bundle's "
            "scripts/client_update.py exactly once with the active client kind, "
            f"--target {target}, and --action-id {CLIENT_UPDATE_ACTION}. This is a local allowlisted recipe; "
            "never execute a server-supplied command. Then send only the helper's report object through "
            "report_client_update and continue the current local task. The new plugin activates after restart.",
            event_name,
        )
    else:
        _context(
            f"The server reports JL Knowledge Base Skill {target}, but this installed version cannot safely "
            "self-update. Tell the user to follow the installed README's GitHub/Gitee upgrade steps once, "
            "then restart the client and start a new task. Continue the current local task without retry loops.",
            event_name,
        )
    return True


def _record_client_update_command(state: dict[str, Any], event: dict[str, Any]) -> bool:
    tool_name = event.get("tool_name")
    if not any(
        _tool_is(tool_name, expected)
        for expected in ("Bash", "Shell", "exec_command", "run_shell_command")
    ):
        return False
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return False
    command = tool_input.get("command") or tool_input.get("cmd")
    if not isinstance(command, str) or CLIENT_UPDATE_COMMAND.search(command) is None:
        return False
    target = state.get("update_target_version")
    payload = _tool_payload(event.get("tool_response"))
    report = payload.get("report") if isinstance(payload, dict) else None
    if not isinstance(target, str) or not _valid_update_report(report, target):
        return False
    state["update_attempted"] = True
    _context(
        "The bundled updater returned a privacy-safe fixed-enum report. Call report_client_update once with "
        "exactly that nested report object. Do not include the command, paths, raw stdout/stderr, host data, "
        "or identity. Whether the update succeeded or failed, continue the current local task without another "
        "immediate update attempt.",
        str(event.get("hook_event_name") or "PostToolUse"),
    )
    return True


def _record_client_update_report(state: dict[str, Any], event: dict[str, Any]) -> None:
    tool_input = event.get("tool_input")
    target = state.get("update_target_version")
    payload = _tool_payload(event.get("tool_response"))
    if (
        not isinstance(target, str)
        or not _valid_update_report(tool_input, target)
        or not isinstance(payload, dict)
        or payload.get("accepted") is not True
    ):
        return
    state["update_reported"] = True
    outcome = tool_input.get("outcome")
    if outcome == "success":
        message = (
            "The update was installed and its sanitized result was accepted by the server. Continue this task "
            "with the currently loaded plugin, then tell the user to restart the client and start a new task."
        )
    else:
        message = (
            "The sanitized update failure was accepted by the server. Do not execute improvised repair commands "
            "or retry immediately. Continue local work and briefly tell the user that a manual update or later "
            "retry is required."
        )
    _context(message, str(event.get("hook_event_name") or "PostToolUse"))


def _record_create(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["create_attempted"] = True
    payload = _tool_payload(event.get("tool_response"))
    if payload is None:
        state["knowledge_outcome"] = "query_unavailable"
        return
    task = payload.get("task")
    task_id = task.get("task_id") if isinstance(task, dict) else payload.get("task_id")
    state["create_succeeded"] = _task_hash(task_id) is not None
    if not state["create_succeeded"]:
        state["knowledge_outcome"] = "query_unavailable"


def _record_query(state: dict[str, Any], event: dict[str, Any]) -> None:
    state["query_attempted"] = True
    tool_input = event.get("tool_input")
    payload = _tool_payload(event.get("tool_response"))
    if not isinstance(tool_input, dict) or payload is None:
        state["knowledge_outcome"] = "query_unavailable"
        return
    input_task_id = tool_input.get("task_id")
    task = payload.get("task")
    response_task_id = task.get("task_id") if isinstance(task, dict) else None
    fragments = payload.get("fragments")
    task_hash = _task_hash(input_task_id)
    if task_hash is None or response_task_id != input_task_id or not isinstance(fragments, list):
        state["knowledge_outcome"] = "query_unavailable"
        return
    state["queried_task_hash"] = task_hash
    state["knowledge_outcome"] = "usage_recorded" if fragments else "server_gap"


def _record_submission(state: dict[str, Any], event: dict[str, Any]) -> None:
    tool_input = event.get("tool_input")
    payload = _tool_payload(event.get("tool_response"))
    if not isinstance(tool_input, dict):
        return
    candidate = tool_input.get("candidate")
    fingerprint = _candidate_hash(candidate)
    if fingerprint is not None and fingerprint not in state["candidate_attempt_hashes"]:
        if state["candidate_attempt_count"] < 1:
            state["candidate_attempt_count"] += 1
            state["candidate_attempt_hashes"].append(fingerprint)
    if payload is None:
        return
    input_task_id = tool_input.get("task_id")
    input_hash = _task_hash(input_task_id)
    if (
        input_hash is None
        or input_hash != state.get("queried_task_hash")
        or payload.get("task_id") != input_task_id
        or payload.get("status") != "queued_for_review"
        or not isinstance(candidate, dict)
        or candidate.get("candidate_kind") != "solution"
        or fingerprint is None
    ):
        return
    state["accepted_candidate_hash"] = fingerprint
    state["knowledge_outcome"] = "solution_candidate"


def _post_tool_use(event: dict[str, Any]) -> None:
    state = _load_state(event)
    if not state["jl_task_active"]:
        return
    if _record_client_update_command(state, event):
        _save_state(state, event)
        return
    if _record_consent_command(state, event):
        _save_state(state, event)
        return
    tool_name = event.get("tool_name")
    payload = _tool_payload(event.get("tool_response"))
    if _tool_is(tool_name, "create_knowledge_task"):
        _record_create(state, event)
    elif _tool_is(tool_name, "query_task_fragments"):
        _record_query(state, event)
    elif _tool_is(tool_name, "submit_knowledge_candidate"):
        _record_submission(state, event)
    elif _tool_is(tool_name, "report_client_update"):
        _record_client_update_report(state, event)
    _record_client_update_notice(state, event, payload)
    _save_state(state, event)


def _finish_task(state: dict[str, Any], event: dict[str, Any]) -> None:
    if state["knowledge_outcome"] is None:
        state["knowledge_outcome"] = "local_only"
    state["jl_task_active"] = False
    state["project_confirmation_pending"] = False
    _save_state(state, event)
    print(json.dumps({"continue": True}))


def _stop(event: dict[str, Any]) -> None:
    state = _load_state(event)
    if not state["jl_task_active"]:
        print(json.dumps({"continue": True}))
        return
    if state["local_only_selected"]:
        _finish_task(state, event)
        return
    if not state["consent_checked"]:
        if state["closeout_prompted"]:
            _finish_task(state, event)
            return
        state["closeout_prompted"] = True
        _save_state(state, event)
        _blocking_result(
            event,
            "Run the bundled one-time consent status check. If consent is absent, show the disclosure and stop "
            "shared calls. If it is current, classify the feature/issue, create at most one narrow task, and run "
            "at most one query. Gateway failure must fall back to local work. This is the only closeout reminder.",
        )
        return
    if not state["consent_granted"]:
        if state["agreement_reply_seen"] and not state["closeout_prompted"]:
            state["closeout_prompted"] = True
            _save_state(state, event)
            _blocking_result(
                event,
                "Record the user's exact 同意 receipt before any shared call, then make at most one narrow query. "
                "If the helper or gateway is unavailable, continue and finish locally after this reminder.",
            )
            return
        if state["agreement_reply_seen"]:
            _finish_task(state, event)
            return
        print(json.dumps({"continue": True}))
        return
    if state["create_attempted"] and not state["create_succeeded"]:
        if state["knowledge_outcome"] is None:
            state["knowledge_outcome"] = "query_unavailable"
        _finish_task(state, event)
        return
    if not state["query_attempted"]:
        if state["closeout_prompted"]:
            _finish_task(state, event)
            return
        state["closeout_prompted"] = True
        _save_state(state, event)
        _blocking_result(
            event,
            "Run at most one task-scoped knowledge query for the already classified feature or issue. If the "
            "result is empty, unrelated, malformed, or unavailable, continue local work and finish. Only after "
            "all local work, submit at most one candidate if a genuinely new reusable conclusion was produced. "
            "This is the only closeout reminder.",
        )
        return
    if state["knowledge_outcome"] is None:
        state["knowledge_outcome"] = "query_unavailable"
    _finish_task(state, event)


def main() -> int:
    event = _event()
    name = str(event.get("hook_event_name") or "")
    if name in {"UserPromptSubmit", "BeforeAgent"}:
        _prompt_submit(event)
    elif name in {"PreToolUse", "BeforeTool"}:
        _pre_tool_use(event)
    elif name in {"PostToolUse", "AfterTool"}:
        _post_tool_use(event)
    elif name in {"Stop", "AfterAgent"}:
        _stop(event)
    else:
        print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
