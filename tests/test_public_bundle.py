from __future__ import annotations

import ast
import copy
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
SKILL = ROOT / "skills" / "jl-knowledge-base-skill" / "SKILL.md"
OPENAI_YAML = ROOT / "skills" / "jl-knowledge-base-skill" / "agents" / "openai.yaml"
ENGINEER_SKILL = ROOT / "skills" / "jl-sdk-engineer-core" / "SKILL.md"
ENGINEER_OPENAI_YAML = ROOT / "skills" / "jl-sdk-engineer-core" / "agents" / "openai.yaml"
CONTRIBUTION_WORKFLOW = SKILL.parent / "references" / "contribution-workflow.md"
GATEWAY_CONTRACT = SKILL.parent / "references" / "gateway-contract.md"
OUTBOX = ROOT / "scripts" / "knowledge_outbox.py"
PUBLIC_MCP_URL = "https://convicted-matthew-plates-scientific.trycloudflare.com/knowledge/mcp"
CONSENT_PHRASE = "I_AGREE_TO_AUTOMATIC_SANITIZED_JL_KNOWLEDGE_CONTRIBUTION"
REVOCATION_PHRASE = "REVOKE_AND_DELETE_PENDING_CONTRIBUTIONS"
SANITIZATION_ACK = "STRUCTURED_ONLY_NO_SOURCE_LOG_IDENTITY_PATH_KEY_OR_CREDENTIAL"


def public_text() -> str:
    paths = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.relative_to(ROOT).parts
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


class PublicBundleTests(unittest.TestCase):
    def test_manifest_is_distribution_ready(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], ROOT.name)
        self.assertRegex(
            payload["version"], r"^\d+\.\d+\.\d+(?:\+codex\.\d{14})?$"
        )
        self.assertEqual(payload["skills"], "./skills/")
        self.assertEqual(payload["mcpServers"], "./.mcp.json")
        mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(mcp["mcpServers"]["jl_private_knowledge"]["url"], PUBLIC_MCP_URL)
        self.assertTrue(payload["author"]["name"])
        self.assertTrue(payload["interface"]["displayName"])

    def test_skill_declares_scoped_mcp_dependency(self) -> None:
        yaml_text = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn('type: "mcp"', yaml_text)
        self.assertIn('transport: "streamable_http"', yaml_text)
        self.assertIn(f'url: "{PUBLIC_MCP_URL}"', yaml_text)
        skill_text = SKILL.read_text(encoding="utf-8")
        self.assertIn("create_knowledge_task", skill_text)
        self.assertIn("query_task_fragments", skill_text)
        self.assertIn("submit_knowledge_candidate", skill_text)

    def test_public_engineering_shell_is_self_contained_but_knowledge_free(self) -> None:
        skill_text = ENGINEER_SKILL.read_text(encoding="utf-8")
        agent_text = ENGINEER_OPENAI_YAML.read_text(encoding="utf-8")
        for phrase in (
            "$jl-knowledge-base-skill",
            "Makefile",
            "E1",
            "E2",
            "E3",
            "current user's Codex/AI account",
            "contains no private corpus",
        ):
            self.assertIn(phrase, skill_text)
        self.assertIn("$jl-sdk-engineer-core", agent_text)
        self.assertFalse((ENGINEER_SKILL.parent / "assets").exists())
        self.assertFalse((ENGINEER_SKILL.parent / "references" / "knowledge-base").exists())

    def test_query_and_submit_require_server_task_id(self) -> None:
        text = public_text()
        self.assertIn("Every query and candidate submission must carry a `task_id`", text)
        self.assertIn("never submit without a valid `task_id`", text)
        self.assertGreaterEqual(text.count('"task_id"'), 4)

    def test_examples_match_gateway_v1_wire_shape(self) -> None:
        contract = (SKILL.parent / "references" / "gateway-contract.md").read_text(encoding="utf-8")
        for field in (
            '"purpose"',
            '"allowed_tools"',
            '"max_requests"',
            '"ttl_minutes"',
            '"include_incubator"',
            '"limit"',
            '"capability_id"',
            '"semantic_id"',
            '"lifecycle_status"',
            '"idempotency_key"',
            '"candidate_id"',
            '"product_id"',
            '"domain_id"',
            '"candidate_taxonomy"',
            '"status": "accepted_to_incubator"',
            '"verification_status": "unverified"',
        ):
            self.assertIn(field, contract)
        for obsolete_field in (
            '"task": {\n    "summary"',
            '"dedupe_key"',
            '"candidate_status"',
            '"status": "' + "queued" + '_for_review"',
        ):
            self.assertNotIn(obsolete_field, contract)

    def test_bundle_contains_no_private_endpoint_or_literal_secret(self) -> None:
        text = public_text()
        private_ipv4 = re.compile(
            r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|"
            r"172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
        )
        absolute_windows_path = re.compile(r"\b[A-Za-z]:\\")
        literal_secret = re.compile(
            r"(?i)(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)"
            r"\s*[:=]\s*[\"'][^\"']+[\"']"
        )
        self.assertIsNone(private_ipv4.search(text))
        self.assertIsNone(absolute_windows_path.search(text))
        self.assertIsNone(literal_secret.search(text))

    def test_privacy_and_growth_invariants_are_explicit(self) -> None:
        text = public_text()
        for phrase in (
            "processed_pending_verification",
            "compiled_pending_hardware",
            "verified_failed",
            "verified_pass",
            "parent_semantic_id",
            "semantic_id",
            '"status": "accepted_to_incubator"',
            "Never send an empty or wildcard query",
            "Do not expose a `list`",
            "one-time consent",
            "outbox-first",
            "never run or contact the knowledge owner's Codex CLI",
            "product → domain → capability → subfeature → boundary → issue",
        ):
            self.assertIn(phrase, text)
        obsolete_statuses = (
            "handled" + "_pending_validation",
            "validation" + "_failed",
        )
        for obsolete in obsolete_statuses:
            self.assertNotIn(obsolete, text)

    def test_outbox_has_no_network_or_model_execution_dependency(self) -> None:
        tree = ast.parse(OUTBOX.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
        for forbidden in ("http", "urllib", "requests", "httpx", "openai", "socket", "subprocess"):
            self.assertNotIn(forbidden, imported_roots)
        script_text = OUTBOX.read_text(encoding="utf-8").lower()
        self.assertNotIn("codex" + " exec", script_text)

    def test_contribution_workflow_documents_one_time_and_automatic_behavior(self) -> None:
        text = CONTRIBUTION_WORKFLOW.read_text(encoding="utf-8")
        for phrase in (
            CONSENT_PHRASE,
            REVOCATION_PHRASE,
            SANITIZATION_ACK,
            "ready --limit 3",
            "status: accepted_to_incubator",
            "idempotency_key",
            "30 days",
        ):
            self.assertIn(phrase, text)

    def test_public_access_is_separate_from_customer_platform_and_internal_worker(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
        terms = (ROOT / "TERMS.md").read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        contract = GATEWAY_CONTRACT.read_text(encoding="utf-8")

        for phrase in (
            "可以做什么",
            "安装",
            "不需要注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据",
            "JL Knowledge Base Skill",
            "No customer-platform registration, login, application, approval, or individual credential is required",
        ):
            self.assertIn(phrase, readme)

        self.assertIn("匿名限流", privacy)
        self.assertIn("不要求注册、登录、申请、批准或个人凭据", terms)
        self.assertIn("Public knowledge access requires no registration", skill)
        self.assertIn("/api/worker/knowledge/*", contract)
        self.assertIn("one operator-controlled master switch", contract)
        for internal_detail in (
            "GitHub 版总开关",
            "内部 worker",
            "Windows 编译主机",
            "客户网页任务",
            "维护者可统一开启",
        ):
            self.assertNotIn(internal_detail, readme + privacy + terms)
        for obsolete in (
            "安装 Plugin 不会自动获得知识库访问资格",
            "独立安装凭据",
            "public installation credential",
            "per-installation authentication",
        ):
            self.assertNotIn(obsolete, readme + privacy + terms + skill + contract)


class OutboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temporary.name) / "state"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_outbox(
        self,
        *arguments: str,
        candidate: dict[str, object] | None = None,
        expected_code: int = 0,
    ) -> dict[str, object]:
        command = [sys.executable, str(OUTBOX), "--state-dir", str(self.state_dir), *arguments]
        result = subprocess.run(
            command,
            input=json.dumps(candidate, ensure_ascii=False) if candidate is not None else None,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected_code, msg=result.stderr or result.stdout)
        output = result.stdout if result.returncode == 0 else result.stderr
        return json.loads(output)

    @staticmethod
    def candidate() -> dict[str, object]:
        return {
            "product_id": "product.tws-earbuds",
            "domain_id": "domain.audio-acoustic",
            "capability_id": "capability.anc-transparency",
            "semantic_id": "subfeature.anc-mode-key-cycle",
            "node_type": "subfeature",
            "parent_semantic_id": "capability.anc-transparency",
            "title": "ANC mode key cycle",
            "summary": "Mapped a reusable ANC mode cycle and preserved the platform default when disabled.",
            "lifecycle_status": "compiled_pending_hardware",
            "evidence_level": "E2",
            "scope": {
                "products": ["TWS earbud"],
                "chips": ["AC701N"],
                "sdk_versions": ["3.4.1"],
                "platforms": ["JL701N"],
                "tags": ["ANC"],
            },
            "relations": [{"type": "depends_on", "target_semantic_id": "capability.anc-transparency"}],
            "workflow": ["Mapped the mode transition before building the target configuration."],
            "validation": ["A real target build passed; hardware behavior remains pending."],
            "limitations": ["Applies only to the stated chip and SDK scope."],
        }

    def grant(self) -> None:
        response = self.run_outbox("grant", "--accept", CONSENT_PHRASE)
        self.assertTrue(response["consent_granted"])

    def enqueue(self, candidate: dict[str, object] | None = None) -> dict[str, object]:
        return self.run_outbox(
            "enqueue",
            "--candidate-file",
            "-",
            "--sanitization-ack",
            SANITIZATION_ACK,
            candidate=candidate or self.candidate(),
        )

    def test_requires_one_time_consent_then_deduplicates_stably(self) -> None:
        status = self.run_outbox("status")
        self.assertFalse(status["consent_granted"])
        rejected = self.run_outbox(
            "enqueue",
            "--candidate-file",
            "-",
            "--sanitization-ack",
            SANITIZATION_ACK,
            candidate=self.candidate(),
            expected_code=2,
        )
        self.assertIn("consent", str(rejected["error"]).lower())

        self.grant()
        first = self.enqueue()
        second = self.enqueue()
        self.assertEqual(first["id"], second["id"])
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])

        ready = self.run_outbox("ready", "--limit", "3")
        self.assertEqual(len(ready["entries"]), 1)
        entry = ready["entries"][0]
        self.assertEqual(entry["id"], first["id"])
        self.assertEqual(entry["candidate"]["product_id"], "product.tws-earbuds")
        self.assertEqual(entry["candidate"]["domain_id"], "domain.audio-acoustic")
        self.assertNotIn("task_id", entry)

    def test_product_and_domain_are_required_stable_generic_ids(self) -> None:
        self.grant()
        for missing_field in ("product_id", "domain_id"):
            candidate = self.candidate()
            del candidate[missing_field]
            response = self.run_outbox(
                "enqueue",
                "--candidate-file",
                "-",
                "--sanitization-ack",
                SANITIZATION_ACK,
                candidate=candidate,
                expected_code=2,
            )
            self.assertIn(missing_field, str(response["error"]))

        invalid_values = (
            ("product_id", "product.CustomerProject"),
            ("product_id", "customer.tws-earbud"),
            ("product_id", "product.tws-earbud"),
            ("domain_id", "domain.ClientFeature"),
            ("domain_id", "project.app-integration"),
            ("domain_id", "domain.audio"),
            ("domain_id", "domain.bluetooth"),
        )
        for field, value in invalid_values:
            candidate = self.candidate()
            candidate[field] = value
            response = self.run_outbox(
                "enqueue",
                "--candidate-file",
                "-",
                "--sanitization-ack",
                SANITIZATION_ACK,
                candidate=candidate,
                expected_code=2,
            )
            self.assertIn(field, str(response["error"]))
        self.assertEqual(self.run_outbox("status")["pending_count"], 0)

    def test_classification_is_part_of_stable_idempotency_key(self) -> None:
        self.grant()
        first = self.enqueue()
        changed = self.candidate()
        changed["domain_id"] = "domain.app-integration"
        second = self.enqueue(changed)
        self.assertNotEqual(first["idempotency_key"], second["idempotency_key"])

    def test_transient_retry_keeps_entry_and_ack_deletes_it(self) -> None:
        self.grant()
        queued = self.enqueue()
        retried = self.run_outbox("retry", "--id", str(queued["id"]), "--reason", "unavailable")
        self.assertEqual(retried["attempt_count"], 1)
        self.assertEqual(retried["retry_after_seconds"], 60)
        self.assertEqual(self.run_outbox("status")["pending_count"], 1)

        acknowledged = self.run_outbox("ack", "--id", str(queued["id"]))
        self.assertTrue(acknowledged["acknowledged"])
        self.assertEqual(self.run_outbox("status")["pending_count"], 0)

    def test_server_withdrawn_is_a_permanent_drop_reason(self) -> None:
        self.grant()
        queued = self.enqueue()
        dropped = self.run_outbox(
            "drop", "--id", str(queued["id"]), "--reason", "server_withdrawn"
        )
        self.assertTrue(dropped["dropped"])
        self.assertEqual(dropped["reason"], "server_withdrawn")
        self.assertEqual(self.run_outbox("status")["pending_count"], 0)

    def test_revocation_deletes_pending_and_requires_new_consent(self) -> None:
        self.grant()
        self.enqueue()
        revoked = self.run_outbox("revoke", "--confirm", REVOCATION_PHRASE)
        self.assertEqual(revoked["pending_deleted"], 1)
        status = self.run_outbox("status")
        self.assertFalse(status["consent_granted"])
        self.assertEqual(status["pending_count"], 0)

    def test_privacy_guard_rejects_paths_logs_keys_credentials_and_unknown_fields(self) -> None:
        self.grant()
        candidates: list[dict[str, object]] = []

        with_path = copy.deepcopy(self.candidate())
        with_path["summary"] = "Changed " + "Q" + ":\\private\\board.c"
        candidates.append(with_path)

        with_embedded_path = copy.deepcopy(self.candidate())
        with_embedded_path["summary"] = "path=" + "C" + ":\\Users\\Example\\client.c"
        candidates.append(with_embedded_path)

        with_parenthesized_path = copy.deepcopy(self.candidate())
        with_parenthesized_path["summary"] = "Checked (" + "D" + ":\\secret\\key.bin)"
        candidates.append(with_parenthesized_path)

        with_log = copy.deepcopy(self.candidate())
        with_log["summary"] = "Traceback " + "(most recent call last)" + ": build failed"
        candidates.append(with_log)

        with_key = copy.deepcopy(self.candidate())
        with_key["summary"] = "Used signing." + "key" + " from the build input"
        candidates.append(with_key)

        with_credential = copy.deepcopy(self.candidate())
        credential_name = "pass" + "word"
        with_credential["summary"] = credential_name + "=" + "not-a-real-value"
        candidates.append(with_credential)

        with_source = copy.deepcopy(self.candidate())
        with_source["summary"] = "if (enabled) { apply_mode(); }"
        candidates.append(with_source)

        with_payload = copy.deepcopy(self.candidate())
        with_payload["summary"] = "Captured value " + ("Ab3_" * 16)
        candidates.append(with_payload)

        with_phone = copy.deepcopy(self.candidate())
        with_phone["summary"] = "Contact " + "138" + "0013" + "8000"
        candidates.append(with_phone)

        with_formatted_phone = copy.deepcopy(self.candidate())
        with_formatted_phone["summary"] = "Contact +" + "86 138-0013-8000"
        candidates.append(with_formatted_phone)

        with_unknown = copy.deepcopy(self.candidate())
        with_unknown["customer_name"] = "example"
        candidates.append(with_unknown)

        for candidate in candidates:
            response = self.run_outbox(
                "enqueue",
                "--candidate-file",
                "-",
                "--sanitization-ack",
                SANITIZATION_ACK,
                candidate=candidate,
                expected_code=2,
            )
            self.assertFalse(response["ok"])
        self.assertEqual(self.run_outbox("status")["pending_count"], 0)

    def test_privacy_guard_rejects_network_identifiers_in_scalars_lists_and_relations(self) -> None:
        self.grant()
        candidates: list[dict[str, object]] = []

        with_email = copy.deepcopy(self.candidate())
        with_email["summary"] = "Contact " + "engineer" + "@" + "example.com"
        candidates.append(with_email)

        with_local_email = copy.deepcopy(self.candidate())
        with_local_email["summary"] = "Contact " + "builder" + "@" + "localhost"
        candidates.append(with_local_email)

        with_ipv4 = copy.deepcopy(self.candidate())
        with_ipv4["scope"]["tags"].append("192" + ".168.10.25")
        candidates.append(with_ipv4)

        with_ipv6 = copy.deepcopy(self.candidate())
        with_ipv6["relations"].append(
            {"type": "observed_on", "target_semantic_id": "2001" + ":db8::1"}
        )
        candidates.append(with_ipv6)

        with_scoped_ipv6 = copy.deepcopy(self.candidate())
        with_scoped_ipv6["validation"].append("Observed on [fe80" + "::1%eth0]")
        candidates.append(with_scoped_ipv6)

        with_mac = copy.deepcopy(self.candidate())
        with_mac["workflow"].append("Observed adapter " + ":".join(["AA", "BB", "CC", "DD", "EE", "FF"]))
        candidates.append(with_mac)

        with_dotted_mac = copy.deepcopy(self.candidate())
        with_dotted_mac["workflow"].append("Observed adapter " + ".".join(["AABB", "CCDD", "EEFF"]))
        candidates.append(with_dotted_mac)

        with_hostname = copy.deepcopy(self.candidate())
        with_hostname["limitations"].append("Only reproduced on " + "builder.example.com")
        candidates.append(with_hostname)

        with_bare_hostname = copy.deepcopy(self.candidate())
        with_bare_hostname["title"] = "Result from " + "BUILD-WORKER-07"
        candidates.append(with_bare_hostname)

        with_localhost = copy.deepcopy(self.candidate())
        with_localhost["title"] = "Result from local" + "host"
        candidates.append(with_localhost)

        with_url = copy.deepcopy(self.candidate())
        with_url["validation"].append("See " + "https" + "://example.com/private/result")
        candidates.append(with_url)

        with_generic_url = copy.deepcopy(self.candidate())
        with_generic_url["validation"].append("See " + "custom" + "://private-host/item")
        candidates.append(with_generic_url)

        for candidate in candidates:
            response = self.run_outbox(
                "enqueue",
                "--candidate-file",
                "-",
                "--sanitization-ack",
                SANITIZATION_ACK,
                candidate=candidate,
                expected_code=2,
            )
            self.assertFalse(response["ok"])
        self.assertEqual(self.run_outbox("status")["pending_count"], 0)


if __name__ == "__main__":
    unittest.main()
