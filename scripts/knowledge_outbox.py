#!/usr/bin/env python3
"""Local consent and privacy-checked outbox for JL knowledge proposals.

This helper deliberately has no network or model client.  The Codex host that
loaded the public plugin submits ready entries through the authenticated MCP
tool, then acknowledges or reschedules them here.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import ipaddress
import json
import os
import re
import secrets
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 1
DISCLOSURE_VERSION = "2026-08-31-v2"
CONSENT_PHRASE = "同意"
REVOCATION_PHRASE = "REVOKE_AND_DELETE_PENDING_CONTRIBUTIONS"
SANITIZATION_ACK = "STRUCTURED_ONLY_NO_SOURCE_LOG_IDENTITY_PATH_KEY_OR_CREDENTIAL"
MAX_CANDIDATE_BYTES = 12 * 1024
MAX_QUEUE_ENTRIES = 1000
RETENTION_DAYS = 30

ALLOWED_NODE_TYPES = {
    "capability",
    "subfeature",
    "boundary",
    "issue",
    "rule",
    "api_alias",
}
ALLOWED_LIFECYCLE_EVIDENCE = {
    "processed_pending_verification": {"E1"},
    "compiled_pending_hardware": {"E2"},
    "verified_failed": {"E1", "E2"},
    "verified_pass": {"E3", "E4"},
}
ALLOWED_CANDIDATE_FIELDS = {
    "candidate_kind",
    "product_id",
    "domain_id",
    "capability_id",
    "semantic_id",
    "node_type",
    "parent_semantic_id",
    "title",
    "summary",
    "lifecycle_status",
    "evidence_level",
    "scope",
    "relations",
    "workflow",
    "validation",
    "limitations",
}
REQUIRED_CANDIDATE_FIELDS = ALLOWED_CANDIDATE_FIELDS - {"parent_semantic_id"}
ALLOWED_CANDIDATE_KINDS = {"solution", "knowledge_gap"}
ALLOWED_RELATION_TYPES = {"contains", "depends_on", "extends", "alternative", "supersedes"}
SCOPE_FIELDS = {"products", "chips", "sdk_versions", "platforms", "tags"}
TRANSIENT_REASONS = {"unavailable", "rate_limited", "authentication", "timeout", "other"}
DROP_REASONS = {
    "privacy_rejected", "schema_rejected", "scope_rejected", "user_revoked",
    "server_withdrawn", "obsolete",
}

IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,119}$")
CLASSIFICATION_ID_RE = re.compile(r"^(?:product|domain)\.[a-z0-9]+(?:[.-][a-z0-9]+)*$")
CANONICAL_PRODUCT_DOMAINS = {
    "product.tws-earbuds": {
        "domain.input-output",
        "domain.power-charging",
        "domain.audio-acoustic",
        "domain.bluetooth-tws",
        "domain.app-integration",
        "domain.production-delivery",
    },
    "product.headset": {
        "domain.input-output",
        "domain.power-charging",
        "domain.audio-acoustic",
        "domain.bluetooth",
        "domain.app-integration",
        "domain.production-delivery",
    },
}
ENTRY_ID_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_PATH_RE = re.compile(r"(?i)(?<![A-Za-z0-9])[A-Za-z]:[\\/]")
UNC_PATH_RE = re.compile(r"\\\\[^\\\s]+\\[^\\\s]+")
POSIX_PRIVATE_PATH_RE = re.compile(r"(?:^|\s)/(?:home|users|var|etc|mnt|volume|root|opt|tmp)/", re.I)
DEEP_RELATIVE_PATH_RE = re.compile(r"(?:^|\s)(?:\.{0,2}/)?[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+){2,}")
URL_RE = re.compile(r"(?i)\b(?:(?:[A-Z][A-Z0-9+.-]{1,15})://|www\.)")
EMAIL_RE = re.compile(r"(?i)(?<![A-Z0-9._%+-])[A-Z0-9._%+-]+@[A-Z0-9.-]+(?![A-Z0-9._%+-])")
IPV4_RE = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")
MAC_RE = re.compile(r"(?i)(?<![0-9A-F])(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}(?![0-9A-F])")
MAC_DOTTED_RE = re.compile(r"(?i)(?<![0-9A-F])(?:[0-9A-F]{4}\.){2}[0-9A-F]{4}(?![0-9A-F])")
HOSTNAME_RE = re.compile(
    r"(?i)(?<![A-Z0-9_-])(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
    r"(?:com|net|org|cn|io|ai|dev|app|cloud|tech|site|online|xyz|top|biz|info|me|tv|"
    r"edu|gov|mil|us|uk|jp|de|fr|ru|br|au|ca|local|lan|internal|intranet|corp|home|"
    r"test|example|invalid|arpa)(?![A-Z0-9_-])"
)
LABELLED_HOST_RE = re.compile(
    r"(?i)\b(?:host|hostname|server|machine|device)[ _-]?(?:name|id)?\s*(?:[:=]|\bis\b)\s*[A-Z0-9._-]+"
)
BARE_HOST_RE = re.compile(r"(?i)\b(?:desktop|laptop|server|build|worker|runner|nas|win)[-_][A-Z0-9][A-Z0-9-]{1,62}\b")
LOCALHOST_RE = re.compile(r"(?i)(?<![A-Z0-9_-])localhost(?![A-Z0-9_-])")
NETWORK_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_.-])\[?[A-Za-z0-9:.%_-]{2,}\]?(?![A-Za-z0-9_.-])")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key|access[_-]?key|client[_-]?secret|"
    r"authorization|bearer)\s*[:=]\s*\S+"
)
PRIVATE_KEY_RE = re.compile(
    r"(?i)(?:BEGIN [A-Z ]*PRIVATE KEY|\b\S+\.(?:key|pem|p12|pfx)(?=$|[\s,;)\]}]))"
)
RAW_LOG_RE = re.compile(
    r"(?i)(?:Traceback \(most recent call last\)|"
    r"\b(?:DEBUG|INFO|WARN|ERROR|FATAL)\s*\[[^\]]+\]|"
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\b|"
    r"\b[A-Za-z0-9_.-]+\.(?:c|h|cc|cpp|s):\d+(?::\d+)?\b|"
    r"\b(?:customer|client|company)[ _-]?(?:name|id)\s*[:=]|"
    r"(?:客户|公司)(?:名称|名字|ID|编号)\s*[:：=])"
)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?86[\s.()-]*)?1[3-9](?:[\s.()-]*\d){9}(?!\d)")
SOURCE_CODE_RE = re.compile(
    r"(?i)(?:#\s*(?:include|define|ifn?def|endif)\b|"
    r"\b(?:if|for|while|switch)\s*\([^)]*\)\s*[{;]|"
    r"\b(?:void|int|char|static|const)\s+\w+\s*\([^)]*\)\s*[{;])"
)
HIGH_ENTROPY_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{48,}(?![A-Za-z0-9+/=_-])")
HEX_PAYLOAD_RE = re.compile(r"(?i)(?:(?<![0-9A-F])(?:[0-9A-F]{2})[\s,;:-]+){15,}[0-9A-F]{2}(?![0-9A-F])")


class OutboxError(ValueError):
    """Expected input/state error that is safe to expose."""


def _contains_ip_address(value: str) -> bool:
    for match in NETWORK_TOKEN_RE.finditer(value):
        token = match.group(0).strip("[](){}<>,;")
        if ":" not in token and token.count(".") != 3:
            continue
        address = token.split("%", 1)[0]
        try:
            ipaddress.ip_address(address)
        except ValueError:
            continue
        return True
    return False


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime | None = None) -> str:
    current = value or _utc_now()
    return current.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise OutboxError("Stored outbox timestamp is invalid.") from exc
    if parsed.tzinfo is None:
        raise OutboxError("Stored outbox timestamp has no timezone.")
    return parsed.astimezone(timezone.utc)


def default_state_dir() -> Path:
    override = os.environ.get("JL_KNOWLEDGE_CLIENT_HOME")
    if override:
        return Path(override).expanduser()
    xdg_state = os.environ.get("XDG_STATE_HOME")
    if xdg_state:
        return Path(xdg_state).expanduser() / "jl-knowledge-base-skill"
    local_app_data = os.environ.get("LOCALAPPDATA")
    if os.name == "nt" and local_app_data:
        return Path(local_app_data) / "JLPrivateKnowledgeClient"
    return Path.home() / ".local" / "state" / "jl-knowledge-base-skill"


def _ensure_state_dirs(root: Path) -> None:
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    (root / "outbox").mkdir(mode=0o700, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(root, 0o700)
        os.chmod(root / "outbox", 0o700)


@contextlib.contextmanager
def _state_lock(root: Path, timeout_seconds: float = 5.0) -> Iterator[None]:
    _ensure_state_dirs(root)
    lock_path = root / ".lock"
    handle = lock_path.open("a+b")
    if handle.tell() == 0:
        handle.write(b"\0")
        handle.flush()
    deadline = time.monotonic() + timeout_seconds
    locked = False
    try:
        while not locked:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except OSError:
                if time.monotonic() >= deadline:
                    raise OutboxError("Local contribution outbox is busy; retry later.")
                time.sleep(0.05)
        yield
    finally:
        if locked:
            with contextlib.suppress(OSError):
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _read_json(path: Path, max_bytes: int = 64 * 1024) -> Any:
    if path.is_symlink() or not path.is_file():
        raise OutboxError("Local contribution state file is missing or unsafe.")
    if path.stat().st_size > max_bytes:
        raise OutboxError("Local contribution state file is unexpectedly large.")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise OutboxError("Local contribution state file is invalid.") from exc


def _atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        with contextlib.suppress(OSError):
            os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        with contextlib.suppress(OSError):
            os.chmod(path, 0o600)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()


def _consent_path(root: Path) -> Path:
    return root / "consent.json"


def _outbox_dir(root: Path) -> Path:
    return root / "outbox"


def _load_consent(root: Path) -> dict[str, Any] | None:
    path = _consent_path(root)
    if not path.exists():
        return None
    payload = _read_json(path, 16 * 1024)
    if not isinstance(payload, dict):
        raise OutboxError("Local consent state is invalid.")
    return payload


def _has_current_consent(root: Path) -> bool:
    payload = _load_consent(root)
    return bool(
        payload
        and payload.get("schema_version") == SCHEMA_VERSION
        and payload.get("disclosure_version") == DISCLOSURE_VERSION
        and payload.get("granted") is True
    )


def _require_consent(root: Path) -> None:
    if not _has_current_consent(root):
        raise OutboxError("Consent required: shared-knowledge access needs the user's one-time 同意 agreement.")


def _validate_text(value: Any, field: str, max_length: int, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise OutboxError(f"{field} must be text.")
    cleaned = value.strip()
    if not cleaned and not allow_empty:
        raise OutboxError(f"{field} must not be empty.")
    if len(cleaned) > max_length:
        raise OutboxError(f"{field} is too long for a structured proposal.")
    if "\n" in cleaned or "\r" in cleaned or "```" in cleaned:
        raise OutboxError(f"{field} must be a short structured statement, not source or raw logs.")
    if "{" in cleaned or "}" in cleaned:
        raise OutboxError(f"{field} must not contain source or configuration blocks.")
    for pattern in (
        WINDOWS_PATH_RE,
        UNC_PATH_RE,
        POSIX_PRIVATE_PATH_RE,
        DEEP_RELATIVE_PATH_RE,
        URL_RE,
        EMAIL_RE,
        IPV4_RE,
        MAC_RE,
        MAC_DOTTED_RE,
        HOSTNAME_RE,
        LABELLED_HOST_RE,
        BARE_HOST_RE,
        LOCALHOST_RE,
        SECRET_ASSIGNMENT_RE,
        PRIVATE_KEY_RE,
        RAW_LOG_RE,
        PHONE_RE,
        SOURCE_CODE_RE,
        HIGH_ENTROPY_RE,
        HEX_PAYLOAD_RE,
    ):
        if pattern.search(cleaned):
            raise OutboxError(
                f"{field} contains a forbidden identity, network identifier, path, log, key, or credential pattern."
            )
    if _contains_ip_address(cleaned):
        raise OutboxError(f"{field} contains a forbidden IPv4 or IPv6 address.")
    return cleaned


def _validate_identifier(value: Any, field: str) -> str:
    cleaned = _validate_text(value, field, 120)
    if not IDENTIFIER_RE.fullmatch(cleaned):
        raise OutboxError(f"{field} must be a stable non-identifying semantic identifier.")
    return cleaned


def _validate_classification_id(value: Any, field: str, prefix: str) -> str:
    cleaned = _validate_identifier(value, field)
    if not CLASSIFICATION_ID_RE.fullmatch(cleaned) or not cleaned.startswith(prefix + "."):
        raise OutboxError(f"{field} must be a lowercase generic {prefix}.* semantic id, never an identity.")
    return cleaned


def _validate_text_list(value: Any, field: str, *, max_items: int, item_length: int) -> list[str]:
    if not isinstance(value, list) or len(value) > max_items:
        raise OutboxError(f"{field} must be a short list.")
    return [_validate_text(item, f"{field}[{index}]", item_length) for index, item in enumerate(value)]


def _validate_relations(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > 12:
        raise OutboxError("relations must be a short list.")
    result: list[dict[str, str]] = []
    for index, relation in enumerate(value):
        if not isinstance(relation, dict) or set(relation) != {"type", "target_semantic_id"}:
            raise OutboxError(f"relations[{index}] must contain only type and target_semantic_id.")
        relation_type = _validate_identifier(relation["type"], f"relations[{index}].type")
        if relation_type not in ALLOWED_RELATION_TYPES:
            raise OutboxError(
                f"relations[{index}].type must be contains, depends_on, extends, alternative, or supersedes."
            )
        result.append(
            {
                "type": relation_type,
                "target_semantic_id": _validate_identifier(
                    relation["target_semantic_id"], f"relations[{index}].target_semantic_id"
                ),
            }
        )
    return result


def validate_candidate(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise OutboxError("Candidate must be a JSON object.")
    unknown = set(candidate) - ALLOWED_CANDIDATE_FIELDS
    missing = REQUIRED_CANDIDATE_FIELDS - set(candidate)
    if unknown:
        raise OutboxError(f"Candidate contains unsupported fields: {', '.join(sorted(unknown))}.")
    if missing:
        raise OutboxError(f"Candidate is missing fields: {', '.join(sorted(missing))}.")

    candidate_kind = _validate_text(candidate["candidate_kind"], "candidate_kind", 32)
    if candidate_kind not in ALLOWED_CANDIDATE_KINDS:
        raise OutboxError("candidate_kind must be solution or knowledge_gap.")
    node_type = _validate_text(candidate["node_type"], "node_type", 32)
    if node_type not in ALLOWED_NODE_TYPES:
        raise OutboxError("node_type is not allowed.")
    lifecycle = _validate_text(candidate["lifecycle_status"], "lifecycle_status", 48)
    evidence = _validate_text(candidate["evidence_level"], "evidence_level", 2)
    if candidate_kind == "knowledge_gap" and (
        node_type != "issue" or lifecycle != "processed_pending_verification" or evidence != "E1"
    ):
        raise OutboxError(
            "A knowledge_gap must be an E1 processed_pending_verification issue, not a solution claim."
        )
    if lifecycle not in ALLOWED_LIFECYCLE_EVIDENCE or evidence not in ALLOWED_LIFECYCLE_EVIDENCE[lifecycle]:
        raise OutboxError("Lifecycle and evidence level do not match actual-evidence rules.")

    parent = candidate.get("parent_semantic_id")
    if node_type == "capability":
        if parent not in (None, ""):
            raise OutboxError("A root capability must not declare parent_semantic_id.")
        parent_value = None
    else:
        parent_value = _validate_identifier(parent, "parent_semantic_id")

    scope = candidate["scope"]
    if not isinstance(scope, dict) or set(scope) - SCOPE_FIELDS:
        raise OutboxError("scope contains unsupported fields.")
    normalized_scope = {
        name: _validate_text_list(scope.get(name, []), f"scope.{name}", max_items=12, item_length=80)
        for name in sorted(SCOPE_FIELDS)
    }

    product_id = _validate_classification_id(candidate["product_id"], "product_id", "product")
    domain_id = _validate_classification_id(candidate["domain_id"], "domain_id", "domain")
    if product_id not in CANONICAL_PRODUCT_DOMAINS:
        raise OutboxError("product_id is not in the server-controlled product taxonomy.")
    if domain_id not in CANONICAL_PRODUCT_DOMAINS[product_id]:
        raise OutboxError("domain_id is not valid for product_id in the server-controlled taxonomy.")

    normalized: dict[str, Any] = {
        "candidate_kind": candidate_kind,
        "product_id": product_id,
        "domain_id": domain_id,
        "capability_id": _validate_identifier(candidate["capability_id"], "capability_id"),
        "semantic_id": _validate_identifier(candidate["semantic_id"], "semantic_id"),
        "node_type": node_type,
        "title": _validate_text(candidate["title"], "title", 160),
        "summary": _validate_text(candidate["summary"], "summary", 800),
        "lifecycle_status": lifecycle,
        "evidence_level": evidence,
        "scope": normalized_scope,
        "relations": _validate_relations(candidate["relations"]),
        "workflow": _validate_text_list(candidate["workflow"], "workflow", max_items=16, item_length=400),
        "validation": _validate_text_list(candidate["validation"], "validation", max_items=12, item_length=400),
        "limitations": _validate_text_list(candidate["limitations"], "limitations", max_items=12, item_length=400),
    }
    if parent_value:
        normalized["parent_semantic_id"] = parent_value

    encoded = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_CANDIDATE_BYTES:
        raise OutboxError("Candidate exceeds the local structured-proposal size limit.")
    return normalized


def _entry_path(root: Path, entry_id: str) -> Path:
    if not ENTRY_ID_RE.fullmatch(entry_id):
        raise OutboxError("Outbox entry id is invalid.")
    return _outbox_dir(root) / f"{entry_id}.json"


def _entry_paths(root: Path) -> list[Path]:
    return sorted(path for path in _outbox_dir(root).glob("*.json") if ENTRY_ID_RE.fullmatch(path.stem))


def _load_entry(path: Path) -> dict[str, Any]:
    payload = _read_json(path, MAX_CANDIDATE_BYTES + 8 * 1024)
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        raise OutboxError("Local outbox entry is invalid.")
    if path.stem != payload.get("id"):
        raise OutboxError("Local outbox entry identity does not match its file name.")
    if payload.get("idempotency_key") != payload.get("id"):
        raise OutboxError("Local outbox idempotency key is invalid.")
    stored_candidate = payload.get("candidate")
    if isinstance(stored_candidate, dict) and "candidate_kind" not in stored_candidate:
        # v0.5.x outbox entries predate explicit solution/gap classification.
        # Preserve those already-consented local items as solutions, while new
        # enqueue requests must always state candidate_kind explicitly.
        stored_candidate = {**stored_candidate, "candidate_kind": "solution"}
    payload["candidate"] = validate_candidate(stored_candidate)
    _parse_utc(payload.get("queued_at"))
    _parse_utc(payload.get("next_attempt_at"))
    return payload


def _purge_expired(root: Path) -> int:
    cutoff = _utc_now() - timedelta(days=RETENTION_DAYS)
    removed = 0
    for path in _entry_paths(root):
        entry = _load_entry(path)
        if _parse_utc(entry["queued_at"]) < cutoff:
            path.unlink()
            removed += 1
    return removed


def _read_candidate_file(value: str) -> Any:
    try:
        if value == "-":
            raw = sys.stdin.buffer.read(MAX_CANDIDATE_BYTES + 1)
        else:
            path = Path(value)
            if path.is_symlink() or not path.is_file():
                raise OutboxError("Candidate input must be a regular file.")
            if path.stat().st_size > MAX_CANDIDATE_BYTES:
                raise OutboxError("Candidate input is too large.")
            raw = path.read_bytes()
    except OSError as exc:
        raise OutboxError("Candidate input could not be read.") from exc
    if len(raw) > MAX_CANDIDATE_BYTES:
        raise OutboxError("Candidate input is too large.")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise OutboxError("Candidate input is not valid UTF-8 JSON.") from exc


def _update_stats(root: Path, field: str) -> None:
    consent = _load_consent(root)
    if not consent:
        return
    stats = consent.setdefault("stats", {})
    stats[field] = int(stats.get(field, 0)) + 1
    stats["last_changed_at"] = _utc_text()
    _atomic_write_json(_consent_path(root), consent)


def command_status(root: Path, _args: argparse.Namespace) -> dict[str, Any]:
    with _state_lock(root):
        purged = _purge_expired(root)
        consent = _load_consent(root)
        paths = _entry_paths(root)
        now = _utc_now()
        ready = sum(1 for path in paths if _parse_utc(_load_entry(path)["next_attempt_at"]) <= now)
        return {
            "schema_version": SCHEMA_VERSION,
            "disclosure_version": DISCLOSURE_VERSION,
            "consent_granted": _has_current_consent(root),
            "consent_needs_refresh": bool(consent) and not _has_current_consent(root),
            "shared_knowledge_access_enabled": _has_current_consent(root),
            "automatic_mode": "outbox_first_best_effort_mcp_submit",
            "pending_count": len(paths),
            "ready_count": ready,
            "expired_purged": purged,
            "network_or_model_calls": False,
        }


def command_grant(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if args.accept != CONSENT_PHRASE:
        raise OutboxError("The user must enter the exact one-time agreement phrase: 同意")
    with _state_lock(root):
        previous = _load_consent(root) or {}
        payload = {
            "schema_version": SCHEMA_VERSION,
            "disclosure_version": DISCLOSURE_VERSION,
            "granted": True,
            "granted_at": _utc_text(),
            "mode": "shared_access_and_automatic_sanitized_candidates",
            "stats": previous.get("stats", {}),
        }
        _atomic_write_json(_consent_path(root), payload)
    return {
        "consent_granted": True,
        "disclosure_version": DISCLOSURE_VERSION,
        "shared_knowledge_access_enabled": True,
        "per_task_confirmation_required": False,
    }


def command_revoke(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if args.confirm != REVOCATION_PHRASE:
        raise OutboxError("The exact revocation phrase is required.")
    with _state_lock(root):
        pending = _entry_paths(root)
        for path in pending:
            path.unlink()
        with contextlib.suppress(FileNotFoundError):
            _consent_path(root).unlink()
    return {
        "consent_granted": False,
        "shared_knowledge_access_enabled": False,
        "pending_deleted": len(pending),
    }


def command_enqueue(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if args.sanitization_ack != SANITIZATION_ACK:
        raise OutboxError("The exact sanitization acknowledgement is required.")
    with _state_lock(root):
        _require_consent(root)
    candidate = validate_candidate(_read_candidate_file(args.candidate_file))
    canonical = json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    entry_id = hashlib.sha256(canonical).hexdigest()
    with _state_lock(root):
        _require_consent(root)
        _purge_expired(root)
        path = _entry_path(root, entry_id)
        if path.exists():
            _load_entry(path)
            return {"id": entry_id, "idempotency_key": entry_id, "queued": True, "duplicate": True}
        if len(_entry_paths(root)) >= MAX_QUEUE_ENTRIES:
            raise OutboxError("Local contribution outbox is full; no candidate was stored.")
        now = _utc_text()
        payload = {
            "schema_version": SCHEMA_VERSION,
            "id": entry_id,
            "idempotency_key": entry_id,
            "queued_at": now,
            "next_attempt_at": now,
            "attempt_count": 0,
            "last_transient_reason": None,
            "candidate": candidate,
        }
        _atomic_write_json(path, payload)
        _update_stats(root, "queued_count")
    return {"id": entry_id, "idempotency_key": entry_id, "queued": True, "duplicate": False}


def command_ready(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not 1 <= args.limit <= 10:
        raise OutboxError("ready limit must be between 1 and 10.")
    with _state_lock(root):
        _require_consent(root)
        purged = _purge_expired(root)
        now = _utc_now()
        entries = []
        for path in _entry_paths(root):
            entry = _load_entry(path)
            if _parse_utc(entry["next_attempt_at"]) <= now:
                entries.append(entry)
            if len(entries) >= args.limit:
                break
    return {"entries": entries, "expired_purged": purged}


def command_ack(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    with _state_lock(root):
        _require_consent(root)
        path = _entry_path(root, args.id)
        existed = path.exists()
        if existed:
            _load_entry(path)
            path.unlink()
            _update_stats(root, "uploaded_count")
    return {"id": args.id, "acknowledged": existed}


def command_retry(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if args.reason not in TRANSIENT_REASONS:
        raise OutboxError("Retry reason is not a transient category.")
    with _state_lock(root):
        _require_consent(root)
        path = _entry_path(root, args.id)
        if not path.exists():
            raise OutboxError("Outbox entry does not exist.")
        entry = _load_entry(path)
        attempt_count = int(entry.get("attempt_count", 0)) + 1
        delay_seconds = min(60 * (2 ** min(attempt_count - 1, 10)), 24 * 60 * 60)
        entry["attempt_count"] = attempt_count
        entry["last_transient_reason"] = args.reason
        entry["next_attempt_at"] = _utc_text(_utc_now() + timedelta(seconds=delay_seconds))
        _atomic_write_json(path, entry)
    return {
        "id": args.id,
        "scheduled": True,
        "attempt_count": attempt_count,
        "retry_after_seconds": delay_seconds,
    }


def command_drop(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    if args.reason not in DROP_REASONS:
        raise OutboxError("Drop reason is not an allowed non-transient category.")
    with _state_lock(root):
        path = _entry_path(root, args.id)
        existed = path.exists()
        if existed:
            _load_entry(path)
            path.unlink()
            _update_stats(root, "dropped_count")
    return {"id": args.id, "dropped": existed, "reason": args.reason}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage one-time consent and a local sanitized JL proposal outbox.")
    parser.add_argument("--state-dir", type=Path, default=default_state_dir())
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status")
    status.set_defaults(handler=command_status)

    grant = subparsers.add_parser("grant")
    grant.add_argument("--accept", required=True)
    grant.set_defaults(handler=command_grant)

    revoke = subparsers.add_parser("revoke")
    revoke.add_argument("--confirm", required=True)
    revoke.set_defaults(handler=command_revoke)

    enqueue = subparsers.add_parser("enqueue")
    enqueue.add_argument("--candidate-file", required=True, help="UTF-8 JSON file, or - for stdin")
    enqueue.add_argument("--sanitization-ack", required=True)
    enqueue.set_defaults(handler=command_enqueue)

    ready = subparsers.add_parser("ready")
    ready.add_argument("--limit", type=int, default=3)
    ready.set_defaults(handler=command_ready)

    ack = subparsers.add_parser("ack")
    ack.add_argument("--id", required=True)
    ack.set_defaults(handler=command_ack)

    retry = subparsers.add_parser("retry")
    retry.add_argument("--id", required=True)
    retry.add_argument("--reason", required=True, choices=sorted(TRANSIENT_REASONS))
    retry.set_defaults(handler=command_retry)

    drop = subparsers.add_parser("drop")
    drop.add_argument("--id", required=True)
    drop.add_argument("--reason", required=True, choices=sorted(DROP_REASONS))
    drop.set_defaults(handler=command_drop)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.handler(args.state_dir.expanduser(), args)
    except OutboxError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
