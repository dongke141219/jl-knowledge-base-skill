from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "client_doctor.py"
SPEC = importlib.util.spec_from_file_location("jl_client_doctor", SCRIPT)
assert SPEC and SPEC.loader
client_doctor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client_doctor)


def write_hook_fixture(root: Path) -> None:
    hooks_dir = root / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "jl_lifecycle.py").write_text("# trusted fixture\n", encoding="utf-8")
    (hooks_dir / "run_jl_lifecycle.cmd").write_text("@echo off\n", encoding="utf-8")
    groups: dict[str, list[dict[str, object]]] = {}
    for event_name, matcher in client_doctor.EXPECTED_MATCHERS.items():
        group: dict[str, object] = {
            "hooks": [
                {
                    "type": "command",
                    "command": client_doctor.TRUSTED_POSIX_COMMAND,
                    "commandWindows": client_doctor.TRUSTED_WINDOWS_COMMAND,
                }
            ]
        }
        if matcher is not None:
            group["matcher"] = matcher
        groups[event_name] = [group]
    (hooks_dir / "hooks.json").write_text(
        json.dumps({"hooks": groups}), encoding="utf-8"
    )


class ClientDoctorTests(unittest.TestCase):
    def test_shipped_codex_hook_config_matches_the_trusted_recipe(self) -> None:
        self.assertEqual(
            client_doctor._hook_status(ROOT / "plugins" / "codex-jl-knowledge-base-skill")["status"],
            "ok",
        )

    def test_local_bundle_checks_require_mcp_and_all_codex_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_hook_fixture(root)
            (root / ".mcp.json").write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            client_doctor.MCP_NAME: {
                                "type": "http",
                                "url": client_doctor.MCP_URL,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(client_doctor._mcp_status(root)["status"], "ok")
            self.assertEqual(client_doctor._hook_status(root)["status"], "ok")

    def test_hook_check_rejects_empty_events_wrong_commands_and_missing_launcher(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_hook_fixture(root)
            hooks_path = root / "hooks" / "hooks.json"
            payload = json.loads(hooks_path.read_text(encoding="utf-8"))
            payload["hooks"]["PostToolUse"] = []
            hooks_path.write_text(json.dumps(payload), encoding="utf-8")
            self.assertNotEqual(client_doctor._hook_status(root)["status"], "ok")

            write_hook_fixture(root / "wrong-command")
            wrong_root = root / "wrong-command"
            wrong_path = wrong_root / "hooks" / "hooks.json"
            wrong = json.loads(wrong_path.read_text(encoding="utf-8"))
            wrong["hooks"]["Stop"][0]["hooks"][0]["command"] = "python untrusted.py"
            wrong_path.write_text(json.dumps(wrong), encoding="utf-8")
            self.assertEqual(
                client_doctor._hook_status(wrong_root)["status"], "command_mismatch"
            )

            write_hook_fixture(root / "missing-launcher")
            missing_root = root / "missing-launcher"
            (missing_root / "hooks" / "run_jl_lifecycle.cmd").unlink()
            self.assertEqual(
                client_doctor._hook_status(missing_root)["status"], "launcher_missing"
            )

    def test_report_is_not_ready_when_plugin_is_disabled(self) -> None:
        with mock.patch.object(
            client_doctor,
            "_codex_plugin_state",
            return_value={"status": "disabled", "version": "0.8.5", "enabled": False},
        ), mock.patch.object(client_doctor, "_mcp_status", return_value={"status": "ok"}), mock.patch.object(
            client_doctor,
            "_hook_status",
            return_value={"status": "ok", "trust": "manual_check_required"},
        ), mock.patch.object(client_doctor, "_consent_status", return_value={"status": "granted"}):
            report = client_doctor.build_report(Path("unused"))
        self.assertFalse(report["ok"])
        self.assertEqual(report["next_action"], "repair_plugin_installation")
        self.assertFalse(report["project_source_accessed"])
        self.assertFalse(report["network_accessed"])

    def test_report_is_ready_only_with_current_consent(self) -> None:
        with mock.patch.object(
            client_doctor,
            "_codex_plugin_state",
            return_value={"status": "ok", "version": "0.8.5", "enabled": True},
        ), mock.patch.object(client_doctor, "_mcp_status", return_value={"status": "ok"}), mock.patch.object(
            client_doctor,
            "_hook_status",
            return_value={"status": "ok", "trust": "manual_check_required"},
        ), mock.patch.object(client_doctor, "_consent_status", return_value={"status": "granted"}):
            report = client_doctor.build_report(Path("unused"))
        self.assertTrue(report["ok"])
        self.assertEqual(report["next_action"], "ready")


if __name__ == "__main__":
    unittest.main()
