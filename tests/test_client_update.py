from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "client_update.py"
SPEC = importlib.util.spec_from_file_location("jl_client_update", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
client_update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(client_update)


def completed(command: list[str], code: int = 0, stdout: str = "", stderr: str = ""):
    return subprocess.CompletedProcess(command, code, stdout, stderr)


class ClientUpdateTests(unittest.TestCase):
    def test_rejects_non_allowlisted_action_without_running_any_command(self) -> None:
        output = io.StringIO()
        with mock.patch.object(client_update, "_run_update") as run_update, redirect_stdout(output):
            code = client_update.main(
                ["--client", "codex", "--target", "0.8.1", "--action-id", "run-this-shell"]
            )
        self.assertEqual(code, 2)
        self.assertFalse(run_update.called)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["error_code"], "invalid_update_request")
        self.assertFalse(payload["server_command_executed"])

    def test_codex_uses_only_fixed_refresh_install_and_verification_commands(self) -> None:
        calls: list[list[str]] = []

        def fake_run(command: list[str], *, timeout: int = 180):
            calls.append(command)
            if command[-2:] == ["list", "--json"]:
                return completed(
                    command,
                    stdout=json.dumps(
                        {
                            "installed": [
                                {
                                    "pluginId": client_update.PLUGIN_ID,
                                    "version": "0.8.1",
                                }
                            ]
                        }
                    ),
                )
            return completed(command)

        report = client_update._base_report("codex", "0.8.1")
        with mock.patch.object(client_update, "_find_codex", return_value="codex"), mock.patch.object(
            client_update, "_run", side_effect=fake_run
        ):
            result = client_update._update_codex(report)
        self.assertEqual(result["outcome"], "success")
        self.assertEqual(result["observed_version"], "0.8.1")
        self.assertEqual(
            calls,
            [
                ["codex", "plugin", "marketplace", "upgrade", "jl-knowledge", "--json"],
                ["codex", "plugin", "add", client_update.PLUGIN_ID, "--json"],
                ["codex", "plugin", "list", "--json"],
            ],
        )

    def test_codex_can_repair_refresh_failure_from_existing_snapshot(self) -> None:
        responses = [
            completed(["refresh"], code=1, stderr="temporary network failure"),
            completed(["install"]),
            completed(
                ["list"],
                stdout=json.dumps(
                    {"installed": [{"pluginId": client_update.PLUGIN_ID, "version": "0.8.1"}]}
                ),
            ),
        ]
        report = client_update._base_report("codex", "0.8.1")
        with mock.patch.object(client_update, "_find_codex", return_value="codex"), mock.patch.object(
            client_update, "_run", side_effect=responses
        ):
            result = client_update._update_codex(report)
        self.assertEqual(result["outcome"], "success")
        self.assertTrue(result["repaired"])

    def test_failure_is_reduced_to_an_enum_and_never_returns_raw_output(self) -> None:
        secret_text = "C" + ":\\Customers\\secret\\build.log token=should-not-leak"
        responses = [completed(["refresh"]), completed(["install"], code=1, stderr=secret_text)]
        report = client_update._base_report("codex", "0.8.1")
        with mock.patch.object(client_update, "_find_codex", return_value="codex"), mock.patch.object(
            client_update, "_run", side_effect=responses
        ):
            result = client_update._update_codex(report)
        serialized = json.dumps(client_update._safe_result(result))
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["reason_code"], "install_failed")
        self.assertNotIn("Customers", serialized)
        self.assertNotIn("should-not-leak", serialized)
        self.assertFalse(client_update._safe_result(result)["raw_output_included"])

    def test_zcode_is_reported_as_manual_instead_of_running_an_unknown_cli(self) -> None:
        with mock.patch.object(client_update, "_run") as run_command:
            result = client_update._run_update("zcode", "0.8.1")
        self.assertFalse(run_command.called)
        self.assertEqual(result["outcome"], "manual_required")
        self.assertEqual(result["reason_code"], "unsupported_client")

    def test_same_target_is_attempted_once_during_the_retry_window(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = io.StringIO()
            report = client_update._base_report("codex", "0.8.1")
            report.update(outcome="failed", stage="plugin_install", reason_code="network_error")
            with mock.patch.object(client_update, "_state_dir", return_value=Path(temporary)), mock.patch.object(
                client_update, "_run_update", return_value=report
            ) as run_update, redirect_stdout(output):
                self.assertEqual(
                    client_update.main(
                        [
                            "--client",
                            "codex",
                            "--target",
                            "0.8.1",
                            "--action-id",
                            client_update.ACTION_ID,
                        ]
                    ),
                    0,
                )
                first = json.loads(output.getvalue())
                output.seek(0)
                output.truncate(0)
                self.assertEqual(
                    client_update.main(
                        [
                            "--client",
                            "codex",
                            "--target",
                            "0.8.1",
                            "--action-id",
                            client_update.ACTION_ID,
                        ]
                    ),
                    0,
                )
                second = json.loads(output.getvalue())
            self.assertEqual(run_update.call_count, 1)
            self.assertFalse(first["already_attempted"])
            self.assertTrue(second["already_attempted"])
            self.assertEqual(first["report"], second["report"])


if __name__ == "__main__":
    unittest.main()
