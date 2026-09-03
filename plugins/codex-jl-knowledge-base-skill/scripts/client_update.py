#!/usr/bin/env python3
"""Run one allowlisted JL public-client update and emit a privacy-safe report.

The server may select only the fixed action identifier implemented here.  It
cannot provide a command, path, URL, or script body.  Raw subprocess output is
used only for local classification and is never printed or persisted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


CLIENT_VERSION = "0.8.0"
ACTION_ID = "run_bundled_updater_v1"
PLUGIN_ID = "jl-knowledge-base-skill@jl-knowledge"
PLUGIN_NAME = "jl-knowledge-base-skill"
MARKETPLACE_NAME = "jl-knowledge"
STATE_VERSION = 1
RETRY_AFTER_HOURS = 6
SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")


def _version_tuple(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = SEMVER_RE.fullmatch(value.strip())
    if match is None:
        return None
    return tuple(int(match.group(index)) for index in range(1, 4))


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _utc_text(value: dt.datetime | None = None) -> str:
    return (value or _utc_now()).astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _state_dir() -> Path:
    override = os.environ.get("JL_KNOWLEDGE_CLIENT_HOME", "").strip()
    if override:
        return Path(override).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if os.name == "nt" and local_app_data:
        return Path(local_app_data) / "JLKnowledgeBaseSkill"
    xdg_state = os.environ.get("XDG_STATE_HOME", "").strip()
    if xdg_state:
        return Path(xdg_state).expanduser() / "jl-knowledge-base-skill"
    return Path.home() / ".local" / "state" / "jl-knowledge-base-skill"


def _state_path() -> Path:
    return _state_dir() / "client_updates.json"


def _empty_state() -> dict[str, Any]:
    return {"version": STATE_VERSION, "attempts": {}}


def _valid_report(value: Any) -> bool:
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
        and re.fullmatch(r"[a-f0-9]{32}", str(value.get("attempt_id") or ""))
        and value.get("client_kind") in {"codex", "gemini", "zcode"}
        and _version_tuple(value.get("from_version")) is not None
        and _version_tuple(value.get("target_version")) is not None
        and (
            value.get("observed_version") == ""
            or _version_tuple(value.get("observed_version")) is not None
        )
        and value.get("action_id") == ACTION_ID
        and value.get("outcome") in {"success", "failed", "manual_required"}
        and value.get("stage")
        in {
            "version_check",
            "marketplace_refresh",
            "plugin_install",
            "extension_update",
            "verification",
            "restart_required",
        }
        and value.get("reason_code")
        in {
            "none",
            "executable_not_found",
            "marketplace_not_configured",
            "network_error",
            "permission_denied",
            "install_failed",
            "verification_failed",
            "version_mismatch",
            "unsupported_client",
            "already_attempted",
            "unknown",
        }
        and isinstance(value.get("repaired"), bool)
    )


def _load_state() -> dict[str, Any]:
    try:
        value = json.loads(_state_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_state()
    if not isinstance(value, dict) or set(value) != {"version", "attempts"}:
        return _empty_state()
    attempts = value.get("attempts")
    if value.get("version") != STATE_VERSION or not isinstance(attempts, dict):
        return _empty_state()
    if len(attempts) > 32:
        return _empty_state()
    for key, item in attempts.items():
        if not isinstance(key, str) or not isinstance(item, dict):
            return _empty_state()
        if set(item) != {"report", "attempted_at"} or not _valid_report(item.get("report")):
            return _empty_state()
        try:
            dt.datetime.fromisoformat(str(item["attempted_at"]).replace("Z", "+00:00"))
        except ValueError:
            return _empty_state()
    return value


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    if os.name != "nt":
        os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def _safe_result(report: dict[str, Any], *, already_attempted: bool = False) -> dict[str, Any]:
    return {
        "ok": report["outcome"] == "success",
        "report": report,
        "already_attempted": already_attempted,
        "restart_required": report["outcome"] == "success",
        "raw_output_included": False,
        "server_command_executed": False,
    }


def _base_report(client_kind: str, target_version: str) -> dict[str, Any]:
    return {
        "client_version": CLIENT_VERSION,
        "attempt_id": uuid.uuid4().hex,
        "client_kind": client_kind,
        "from_version": CLIENT_VERSION,
        "target_version": target_version,
        "observed_version": "",
        "action_id": ACTION_ID,
        "outcome": "failed",
        "stage": "version_check",
        "reason_code": "unknown",
        "repaired": False,
    }


def _classify_failure(text: str, *, default: str = "install_failed") -> str:
    folded = text.casefold()[:65_536]
    if any(term in folded for term in ("timed out", "timeout", "network", "connection", "dns", "tls", "ssl")):
        return "network_error"
    if any(term in folded for term in ("permission denied", "access is denied", "eacces", "eperm")):
        return "permission_denied"
    if "marketplace" in folded and any(
        term in folded for term in ("not configured", "not found", "unknown")
    ):
        return "marketplace_not_configured"
    return default


def _run(command: list[str], *, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        timeout=timeout,
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


def _codex_installed_version(codex: str) -> str:
    try:
        result = _run([codex, "plugin", "list", "--json"], timeout=60)
    except (OSError, subprocess.SubprocessError):
        return ""
    if result.returncode != 0:
        return ""
    try:
        payload = json.loads(result.stdout)
    except (TypeError, json.JSONDecodeError):
        return ""
    installed = payload.get("installed") if isinstance(payload, dict) else None
    if not isinstance(installed, list):
        return ""
    for item in installed:
        if not isinstance(item, dict) or item.get("pluginId") != PLUGIN_ID:
            continue
        version = str(item.get("version") or "").strip()
        return version if _version_tuple(version) is not None else ""
    return ""


def _update_codex(report: dict[str, Any]) -> dict[str, Any]:
    codex = _find_codex()
    if codex is None:
        report.update(outcome="failed", stage="version_check", reason_code="executable_not_found")
        return report
    report["stage"] = "marketplace_refresh"
    try:
        refresh = _run(
            [codex, "plugin", "marketplace", "upgrade", MARKETPLACE_NAME, "--json"]
        )
    except subprocess.TimeoutExpired:
        report.update(outcome="failed", reason_code="network_error")
        return report
    except OSError:
        report.update(outcome="failed", reason_code="executable_not_found")
        return report
    report["stage"] = "plugin_install"
    try:
        install = _run([codex, "plugin", "add", PLUGIN_ID, "--json"])
    except subprocess.TimeoutExpired:
        report.update(outcome="failed", reason_code="network_error")
        return report
    except OSError:
        report.update(outcome="failed", reason_code="executable_not_found")
        return report
    if install.returncode != 0:
        combined = "\n".join(
            (refresh.stdout, refresh.stderr, install.stdout, install.stderr)
        )
        report.update(outcome="failed", reason_code=_classify_failure(combined))
        return report
    report["repaired"] = refresh.returncode != 0
    report["stage"] = "verification"
    observed = _codex_installed_version(codex)
    report["observed_version"] = observed
    if observed != report["target_version"]:
        report.update(outcome="failed", reason_code="version_mismatch", repaired=False)
        return report
    report.update(outcome="success", reason_code="none")
    return report


def _gemini_manifest_version() -> str:
    try:
        path = Path.home() / ".gemini" / "extensions" / PLUGIN_NAME / "gemini-extension.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    version = str(payload.get("version") or "") if isinstance(payload, dict) else ""
    return version if _version_tuple(version) is not None else ""


def _update_gemini(report: dict[str, Any]) -> dict[str, Any]:
    gemini = shutil.which("gemini")
    if not gemini:
        report.update(outcome="failed", stage="version_check", reason_code="executable_not_found")
        return report
    report["stage"] = "extension_update"
    try:
        update = _run([gemini, "extensions", "update", PLUGIN_NAME])
    except subprocess.TimeoutExpired:
        report.update(outcome="failed", reason_code="network_error")
        return report
    except OSError:
        report.update(outcome="failed", reason_code="executable_not_found")
        return report
    if update.returncode != 0:
        report.update(
            outcome="failed",
            reason_code=_classify_failure("\n".join((update.stdout, update.stderr))),
        )
        return report
    report["stage"] = "verification"
    observed = _gemini_manifest_version()
    report["observed_version"] = observed
    if observed != report["target_version"]:
        report.update(outcome="failed", reason_code="version_mismatch")
        return report
    report.update(outcome="success", reason_code="none")
    return report


def _run_update(client_kind: str, target_version: str) -> dict[str, Any]:
    report = _base_report(client_kind, target_version)
    if client_kind == "codex":
        return _update_codex(report)
    if client_kind == "gemini":
        return _update_gemini(report)
    report.update(
        outcome="manual_required",
        stage="version_check",
        reason_code="unsupported_client",
    )
    return report


def _prior_result(state: dict[str, Any], key: str) -> dict[str, Any] | None:
    item = state["attempts"].get(key)
    if not isinstance(item, dict) or not _valid_report(item.get("report")):
        return None
    report = dict(item["report"])
    if report["outcome"] == "success" or report["outcome"] == "manual_required":
        return _safe_result(report, already_attempted=True)
    try:
        attempted_at = dt.datetime.fromisoformat(str(item["attempted_at"]).replace("Z", "+00:00"))
    except ValueError:
        return None
    if _utc_now() - attempted_at < dt.timedelta(hours=RETRY_AFTER_HOURS):
        return _safe_result(report, already_attempted=True)
    return None


def _store_report(state: dict[str, Any], key: str, report: dict[str, Any]) -> None:
    state["attempts"][key] = {"report": report, "attempted_at": _utc_text()}
    if len(state["attempts"]) > 32:
        ordered = sorted(
            state["attempts"].items(), key=lambda item: str(item[1].get("attempted_at") or "")
        )
        state["attempts"] = dict(ordered[-32:])
    _save_state(state)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one allowlisted JL client update.")
    parser.add_argument("--client", required=True, choices=("codex", "gemini", "zcode"))
    parser.add_argument("--target", required=True)
    parser.add_argument("--action-id", required=True)
    args = parser.parse_args(argv)
    target = str(args.target).strip()
    target_tuple = _version_tuple(target)
    current_tuple = _version_tuple(CLIENT_VERSION)
    if args.action_id != ACTION_ID or target_tuple is None or current_tuple is None or target_tuple <= current_tuple:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error_code": "invalid_update_request",
                    "raw_output_included": False,
                    "server_command_executed": False,
                },
                separators=(",", ":"),
            )
        )
        return 2
    state = _load_state()
    key = f"{args.client}:{target}"
    prior = _prior_result(state, key)
    if prior is not None:
        print(json.dumps(prior, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    report = _run_update(args.client, target)
    _store_report(state, key, report)
    print(
        json.dumps(
            _safe_result(report),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    # A classified update failure is a valid reportable outcome, not a helper
    # crash.  Keep exit 0 so lifecycle hooks can safely parse and report it.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
