#!/usr/bin/env python3
"""Report whether the local Codex public knowledge client is ready.

The diagnostic reads only the installed plugin state, bundled configuration,
hook declaration, and local consent receipt. It does not inspect a project or
contact the knowledge service.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


SCHEMA = "jl-client-doctor-v1"
CLIENT_VERSION = "0.8.5"
PLUGIN_ID = "jl-knowledge-base-skill@jl-knowledge"
MCP_NAME = "jl-knowledge-base"
MCP_URL = f"https://luminsai.com/knowledge/mcp?client_version={CLIENT_VERSION}"
REQUIRED_HOOKS = {"UserPromptSubmit", "PreToolUse", "PostToolUse", "Stop"}
TRUSTED_POSIX_COMMAND = (
    'python3 "$PLUGIN_ROOT/hooks/jl_lifecycle.py" || '
    'python "$PLUGIN_ROOT/hooks/jl_lifecycle.py"'
)
TRUSTED_WINDOWS_COMMAND = (
    'cmd.exe /d /c ""%PLUGIN_ROOT%\\hooks\\run_jl_lifecycle.cmd""'
)
EXPECTED_MATCHERS = {
    "UserPromptSubmit": None,
    "PreToolUse": "(?:create_knowledge_task|query_task_fragments|submit_knowledge_candidate|report_client_update)$",
    "PostToolUse": "(?:Bash|Shell|exec_command|run_shell_command|create_knowledge_task|query_task_fragments|submit_knowledge_candidate|report_client_update)$",
    "Stop": None,
}


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=60,
        shell=False,
    )


def _find_codex() -> str | None:
    direct = shutil.which("codex")
    if direct:
        return direct
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        return None
    candidates = list((Path(local_app_data) / "OpenAI" / "Codex" / "bin").glob("*/codex.exe"))
    files = [candidate for candidate in candidates if candidate.is_file()]
    if not files:
        return None
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return str(files[0])


def _bundle_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    if (root / ".codex-plugin" / "plugin.json").is_file():
        return root
    packaged = root / "plugins" / "codex-jl-knowledge-base-skill"
    return packaged if (packaged / ".codex-plugin" / "plugin.json").is_file() else root


def _codex_plugin_state() -> dict[str, Any]:
    codex = _find_codex()
    if codex is None:
        return {"status": "codex_not_found", "version": "", "enabled": False}
    try:
        result = _run([codex, "plugin", "list", "--json"])
        payload = json.loads(result.stdout) if result.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        payload = None
    installed = payload.get("installed") if isinstance(payload, dict) else None
    if not isinstance(installed, list):
        return {"status": "state_unavailable", "version": "", "enabled": False}
    for item in installed:
        if not isinstance(item, dict) or item.get("pluginId") != PLUGIN_ID:
            continue
        version = str(item.get("version") or "").strip()
        enabled = item.get("enabled") is True
        if version != CLIENT_VERSION:
            status = "version_mismatch"
        elif not enabled:
            status = "disabled"
        else:
            status = "ok"
        return {"status": status, "version": version, "enabled": enabled}
    return {"status": "not_installed", "version": "", "enabled": False}


def _mcp_status(root: Path) -> dict[str, str]:
    path = root / ".mcp.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        server = payload["mcpServers"][MCP_NAME]
        url = server["url"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return {"status": "missing_or_invalid"}
    return {"status": "ok" if url == MCP_URL else "url_mismatch"}


def _hook_status(root: Path) -> dict[str, Any]:
    path = root / "hooks" / "hooks.json"
    lifecycle = root / "hooks" / "jl_lifecycle.py"
    windows_launcher = root / "hooks" / "run_jl_lifecycle.cmd"
    if not lifecycle.is_file() or not windows_launcher.is_file():
        return {"status": "launcher_missing", "trust": "manual_check_required"}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        hooks = payload["hooks"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return {"status": "missing_or_invalid", "trust": "manual_check_required"}
    if not isinstance(hooks, dict) or set(hooks) != REQUIRED_HOOKS:
        return {"status": "incomplete", "trust": "manual_check_required"}
    for event_name, expected_matcher in EXPECTED_MATCHERS.items():
        groups = hooks.get(event_name)
        if not isinstance(groups, list) or len(groups) != 1:
            return {"status": "incomplete", "trust": "manual_check_required"}
        group = groups[0]
        if not isinstance(group, dict):
            return {"status": "incomplete", "trust": "manual_check_required"}
        if expected_matcher is None:
            if "matcher" in group:
                return {"status": "command_mismatch", "trust": "manual_check_required"}
        elif group.get("matcher") != expected_matcher:
            return {"status": "command_mismatch", "trust": "manual_check_required"}
        commands = group.get("hooks")
        if not isinstance(commands, list) or len(commands) != 1:
            return {"status": "incomplete", "trust": "manual_check_required"}
        command = commands[0]
        if (
            not isinstance(command, dict)
            or command.get("type") != "command"
            or command.get("command") != TRUSTED_POSIX_COMMAND
            or command.get("commandWindows") != TRUSTED_WINDOWS_COMMAND
        ):
            return {"status": "command_mismatch", "trust": "manual_check_required"}
    return {
        "status": "ok",
        "trust": "manual_check_required",
    }


def _consent_status(root: Path) -> dict[str, str]:
    helper = root / "scripts" / "knowledge_outbox.py"
    try:
        spec = importlib.util.spec_from_file_location("jl_knowledge_outbox_doctor", helper)
        if spec is None or spec.loader is None:
            raise ImportError
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        state_root = module.default_state_dir()
        consent = module._load_consent(state_root)
        granted = module._has_current_consent(state_root)
    except Exception:
        return {"status": "unavailable"}
    if granted:
        return {"status": "granted"}
    return {"status": "refresh_required" if consent else "not_granted"}


def build_report(root: Path | None = None) -> dict[str, Any]:
    bundle = root or _bundle_root()
    plugin = _codex_plugin_state()
    mcp = _mcp_status(bundle)
    hooks = _hook_status(bundle)
    consent = _consent_status(bundle)
    ok = (
        plugin["status"] == "ok"
        and mcp["status"] == "ok"
        and hooks["status"] == "ok"
        and consent["status"] == "granted"
    )
    if plugin["status"] != "ok":
        action = "repair_plugin_installation"
    elif mcp["status"] != "ok" or hooks["status"] != "ok":
        action = "reinstall_public_plugin"
    elif consent["status"] != "granted":
        action = "type_exact_consent_in_chat"
    else:
        action = "ready"
    return {
        "schema": SCHEMA,
        "ok": ok,
        "client": "codex",
        "plugin": plugin,
        "mcp_config": mcp,
        "hooks": hooks,
        "consent": consent,
        "next_action": action,
        "project_source_accessed": False,
        "network_accessed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the local JL public knowledge client without network access.")
    parser.parse_args(argv)
    report = build_report()
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
