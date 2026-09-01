from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODEX_PACKAGE = ROOT / "plugins" / "codex-jl-knowledge-base-skill"
ZCODE_PACKAGE = ROOT / "plugins" / "zcode-jl-knowledge-base-skill"
MANIFEST = CODEX_PACKAGE / ".codex-plugin" / "plugin.json"
GEMINI_MANIFEST = ROOT / "gemini-extension.json"
GEMINI_CONTEXT = ROOT / "GEMINI.md"
ZCODE_MANIFEST = ZCODE_PACKAGE / ".zcode-plugin" / "plugin.json"
ZCODE_MARKETPLACE = ROOT / "marketplace.json"
ZCODE_IMPLEMENT_COMMAND = ZCODE_PACKAGE / "commands" / "jl-implement.md"
ZCODE_DIAGNOSE_COMMAND = ZCODE_PACKAGE / "commands" / "jl-diagnose.md"
SKILL = CODEX_PACKAGE / "skills" / "jl-knowledge-base-skill" / "SKILL.md"
OPENAI_YAML = SKILL.parent / "agents" / "openai.yaml"
CONTRIBUTION_WORKFLOW = SKILL.parent / "references" / "contribution-workflow.md"
GATEWAY_CONTRACT = SKILL.parent / "references" / "gateway-contract.md"
OUTBOX = CODEX_PACKAGE / "scripts" / "knowledge_outbox.py"
GEMINI_HOOKS = ROOT / "hooks" / "hooks.json"
CODEX_HOOKS = CODEX_PACKAGE / "hooks" / "hooks.json"
ZCODE_HOOKS = ZCODE_PACKAGE / "hooks" / "hooks.json"
HOOK_SCRIPT = CODEX_PACKAGE / "hooks" / "jl_lifecycle.py"
HOOK_NODE_LAUNCHER = CODEX_PACKAGE / "hooks" / "python-launcher.mjs"
HOOK_WINDOWS_LAUNCHER = CODEX_PACKAGE / "hooks" / "run_jl_lifecycle.cmd"
PUBLIC_MCP_URL = "https://convicted-matthew-plates-scientific.trycloudflare.com/knowledge/mcp?client_version=0.7.1"
MCP_NAME = "jl-knowledge-base"
CONSENT_PHRASE = "同意"
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


def distribution_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in ROOT.rglob("*")
        if path.is_file()
        and "tests" not in path.relative_to(ROOT).parts
        and ".git" not in path.relative_to(ROOT).parts
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )


def lifecycle_state_path(state_dir: Path, session_id: str = "test-session") -> Path:
    digest = hashlib.sha256(session_id.encode("utf-8")).hexdigest()[:24]
    return state_dir / f"jl_lifecycle.{digest}.json"


def invoke_lifecycle_hook(state_dir: Path, event: dict[str, object]) -> dict[str, object]:
    payload = {"session_id": "test-session", **event}
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(HOOK_SCRIPT)],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        encoding="utf-8",
        capture_output=True,
        env={**os.environ, "PLUGIN_DATA": str(state_dir)},
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def consent_tool_event(granted: bool, *, grant: bool = False) -> dict[str, object]:
    action = "grant --accept 同意" if grant else "status"
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": f'python "scripts/knowledge_outbox.py" {action}'},
        "tool_response": {
            "exit_code": 0,
            "output": json.dumps({"consent_granted": granted}),
        },
    }


def query_tool_event(
    task_id: str,
    fragments: list[dict[str, object]] | None = None,
    *,
    event_name: str = "PostToolUse",
    gemini_envelope: bool = False,
) -> dict[str, object]:
    payload = {
        "gateway_version": "knowledge-v1",
        "task": {"task_id": task_id},
        "fragments": fragments or [],
    }
    response: dict[str, object]
    if gemini_envelope:
        response = {"llmContent": json.dumps(payload)}
    else:
        response = {"structuredContent": payload}
    return {
        "hook_event_name": event_name,
        "tool_name": f"mcp__{MCP_NAME}__query_task_fragments",
        "tool_input": {"task_id": task_id, "query": "narrow scoped decision"},
        "tool_response": response,
    }


def candidate_tool_event(
    task_id: str, *, event_name: str = "PostToolUse"
) -> dict[str, object]:
    return {
        "hook_event_name": event_name,
        "tool_name": f"mcp__{MCP_NAME}__submit_knowledge_candidate",
        "tool_input": {"task_id": task_id, "candidate": {"candidate_kind": "solution"}},
        "tool_response": {
            "structuredContent": {
                "task_id": task_id,
                "status": "queued_for_review",
                "layer": "candidate_area",
            }
        },
    }


def marker_tool_event(marker: str, *, event_name: str = "PostToolUse") -> dict[str, object]:
    return {
        "hook_event_name": event_name,
        "tool_name": "run_shell_command" if event_name == "AfterTool" else "Bash",
        "tool_input": {
            "command": f'python "scripts/knowledge_outbox.py" mark-outcome --{marker}'
        },
        "tool_response": {
            "exit_code": 0,
            "output": json.dumps({"outcome_marker": marker}),
        },
    }


class PublicBundleTests(unittest.TestCase):
    def test_public_readme_has_direct_upgrade_and_client_adaptation_notice(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "旧版 Skill 的共享知识访问已经暂停",
            "https://github.com/dongke141219/jl-knowledge-base-skill",
            "https://gitee.com/fofo123/jl-knowledge-base-skill",
            "Codex、Gemini CLI 和 ZCode",
            "由作者完成兼容适配后再使用",
            "官方下载入口（内容一致，任选一个即可）",
            "这里只有一个共享知识库",
            "能实现什么功能",
            "工程实现指南",
            "适用产品/芯片/SDK",
            "使用边界",
            "问题原因与解决方法",
            "真实编译和实机验证证据",
            "唯一共享知识库内的候选区",
        ):
            self.assertIn(phrase, readme)
        self.assertNotIn("候选备份区", readme)
        self.assertNotIn("候选知识库", readme)

    def test_manifest_is_distribution_ready(self) -> None:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "jl-knowledge-base-skill")
        self.assertEqual(payload["version"], "0.7.1")
        self.assertEqual(payload["skills"], "./skills/")
        self.assertEqual(payload["mcpServers"], "./.mcp.json")
        self.assertNotIn("hooks", payload)
        mcp = json.loads((CODEX_PACKAGE / ".mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(mcp["mcpServers"][MCP_NAME]["url"], PUBLIC_MCP_URL)
        self.assertTrue(payload["author"]["name"])
        self.assertTrue(payload["interface"]["displayName"])
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        source = marketplace["plugins"][0]["source"]
        self.assertEqual(source["source"], "git-subdir")
        self.assertEqual(source["path"], "plugins/codex-jl-knowledge-base-skill")

    def test_gemini_extension_is_distribution_ready(self) -> None:
        payload = json.loads(GEMINI_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "jl-knowledge-base-skill")
        self.assertEqual(payload["version"], "0.7.1")
        self.assertEqual(payload["contextFileName"], "GEMINI.md")
        server = payload["mcpServers"][MCP_NAME]
        self.assertEqual(server["httpUrl"], PUBLIC_MCP_URL)
        self.assertEqual(
            set(server["includeTools"]),
            {
                "create_knowledge_task",
                "query_task_fragments",
                "submit_knowledge_candidate",
            },
        )
        self.assertNotIn("trust", server)
        self.assertNotIn("headers", server)

        context = GEMINI_CONTEXT.read_text(encoding="utf-8")
        for phrase in (
            "The user does not need to memorize a fixed prompt or always type a chip model",
            "inspect its local configuration",
            "Ask one plain-language clarification",
            "create_knowledge_task",
            "query_task_fragments",
            "three allowlisted knowledge tools",
        ):
            self.assertIn(phrase, context)

        self.assertTrue((ROOT / "commands" / "jl" / "implement.toml").is_file())
        self.assertTrue((ROOT / "commands" / "jl" / "diagnose.toml").is_file())

    def test_zcode_plugin_and_marketplace_are_distribution_ready(self) -> None:
        payload = json.loads(ZCODE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(payload["name"], "jl-knowledge-base-skill")
        self.assertEqual(payload["version"], "0.7.1")
        self.assertEqual(
            payload["commands"],
            ["commands/jl-implement.md", "commands/jl-diagnose.md"],
        )
        self.assertEqual(payload["skills"], "skills")
        self.assertEqual(payload["mcpServers"], ".mcp.json")

        marketplace = json.loads(ZCODE_MARKETPLACE.read_text(encoding="utf-8"))
        self.assertEqual(marketplace["name"], "jl-knowledge")
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], payload["name"])
        self.assertEqual(entry["version"], payload["version"])
        self.assertEqual(entry["source"], "./plugins/zcode-jl-knowledge-base-skill")
        self.assertEqual(entry["category"], "developer-tools")
        self.assertTrue(entry["strict"])

        for command_path in (ZCODE_IMPLEMENT_COMMAND, ZCODE_DIAGNOSE_COMMAND):
            command = command_path.read_text(encoding="utf-8")
            self.assertIn("description:", command)
            self.assertIn("argument-hint:", command)
            self.assertIn("skills: jl-knowledge-base-skill", command)
            self.assertNotIn("jl-sdk-engineer-core", command)
            self.assertIn("$ARGUMENTS", command)
            self.assertIn("芯片", command)
            self.assertIn("不要发起空查询、通配查询或知识库遍历", command)

    def test_skill_declares_scoped_mcp_dependency(self) -> None:
        yaml_text = OPENAI_YAML.read_text(encoding="utf-8")
        self.assertIn('type: "mcp"', yaml_text)
        self.assertIn('transport: "streamable_http"', yaml_text)
        self.assertIn(f'url: "{PUBLIC_MCP_URL}"', yaml_text)
        self.assertIn(f'value: "{MCP_NAME}"', yaml_text)
        self.assertNotIn("jl_private_knowledge", yaml_text)
        skill_text = SKILL.read_text(encoding="utf-8")
        self.assertIn("create_knowledge_task", skill_text)
        self.assertIn("query_task_fragments", skill_text)
        self.assertIn("submit_knowledge_candidate", skill_text)

    def test_single_main_skill_contains_local_engineering_and_shared_boundaries(self) -> None:
        skill_text = SKILL.read_text(encoding="utf-8")
        for phrase in (
            "Makefile",
            "E1",
            "E2",
            "E3",
            "contains no private knowledge",
            "Unified main workflow",
            "Mandatory one-outcome closeout",
            "solution candidate",
            "server gap",
        ):
            self.assertIn(phrase, skill_text)
        self.assertFalse((ROOT / "skills" / "jl-sdk-engineer-core" / "SKILL.md").exists())
        self.assertNotIn("$jl-", distribution_text())

    def test_query_and_submit_require_server_task_id(self) -> None:
        text = public_text()
        self.assertIn("Every query and candidate submission must carry a `task_id`", text)
        self.assertIn("never submit without a valid `task_id`", text)
        self.assertGreaterEqual(text.count('"task_id"'), 4)

    def test_examples_match_gateway_v1_wire_shape(self) -> None:
        contract = (SKILL.parent / "references" / "gateway-contract.md").read_text(encoding="utf-8")
        for field in (
            '"contribution_consent"',
            '"contribution_consent_version"',
            '"client_version": "0.7.1"',
            '"2026-08-31-v2"',
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
            '"candidate_kind"',
            '"status": "queued_for_review"',
            '"verification_status": "pending_internal_review"',
        ):
            self.assertIn(field, contract)
        for obsolete_field in (
            '"task": {\n    "summary"',
            '"dedupe_key"',
            '"candidate_status"',
            '"status": "accepted' + '_to_incubator"',
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
            '"status": "queued_for_review"',
            "Never send an empty or wildcard query",
            "Do not expose a `list`",
            "Required one-time access and contribution agreement",
            "outbox-first",
            "never run or contact the knowledge owner's AI coding client",
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
            "status: queued_for_review",
            "idempotency_key",
            "30 days",
        ):
            self.assertIn(phrase, text)

    def test_supported_clients_explain_consent_runtime_and_adaptation_contact(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        gemini = GEMINI_CONTEXT.read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
        terms = (ROOT / "TERMS.md").read_text(encoding="utf-8")
        contract = GATEWAY_CONTRACT.read_text(encoding="utf-8")

        self.assertIn("Python 3.10", readme)
        self.assertIn("Python 3.10", gemini)
        self.assertIn("Python 3.10", skill)
        self.assertIn("knowledge_outbox.py grant --accept 同意", gemini)
        self.assertIn('client_version: "0.7.1"', gemini)
        self.assertIn("GitHub Issues", readme)
        self.assertIn("Gitee Issues", readme)
        self.assertIn("经作者完成适配的其他客户端", privacy)
        self.assertIn("经作者完成适配的其他客户端", terms)
        self.assertIn("public MCP connection is named `jl-knowledge-base`", contract)
        self.assertNotIn("intentionally non-routable", contract)

    def test_public_access_is_separate_from_customer_platform_and_internal_worker(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        csdn_article = (ROOT / "CSDN文章.md").read_text(encoding="utf-8")
        privacy = (ROOT / "PRIVACY.md").read_text(encoding="utf-8")
        terms = (ROOT / "TERMS.md").read_text(encoding="utf-8")
        skill = SKILL.read_text(encoding="utf-8")
        contract = GATEWAY_CONTRACT.read_text(encoding="utf-8")

        for phrase in (
            "可以做什么",
            "安装",
            "旧版本升级到最新版",
            '$codexExe = Get-ChildItem "$env:LOCALAPPDATA\\OpenAI\\Codex\\bin\\*\\codex.exe"',
            'plugin marketplace upgrade jl-knowledge',
            'plugin add jl-knowledge-base-skill@jl-knowledge',
            'git config --global url."https://gitee.com/fofo123/jl-knowledge-base-skill.git".insteadOf',
            "jl-knowledge-base-skill@jl-knowledge  installed, enabled  0.7.1",
            "Connection was reset",
            "原理图",
            "UI 交互文档",
            "为什么会越用越智能",
            "可能减少 Token 消耗",
            "Gemini CLI 全新安装",
            "gemini extensions install https://github.com/dongke141219/jl-knowledge-base-skill --auto-update",
            "gemini extensions update jl-knowledge-base-skill",
            "ZCode（GLM）全新安装",
            "设置 → 插件",
            "创建 → 添加插件市场",
            "https://github.com/dongke141219/jl-knowledge-base-skill",
            "/jl-implement",
            "/jl-diagnose",
            "ZCode 旧版本升级",
            "不要求用户每次手动填写芯片",
            "不要求注册客户网页账号，不需要登录、申请、等待批准或领取个人凭据",
            "JL Knowledge Base Skill",
            "No customer-platform registration, login, application, approval, or individual credential is required",
            "离线旧包无法收到联网升级提示",
            "`/hooks`",
        ):
            self.assertIn(phrase, readme)

        for phrase in (
            "Codex 全新安装：Windows 请整段复制",
            "Set-Alias CodexDesktop",
            "CodexDesktop plugin marketplace add",
            'git config --global url."https://gitee.com/fofo123/jl-knowledge-base-skill.git".insteadOf',
            "jl-knowledge-base-skill@jl-knowledge  installed, enabled  0.7.1",
            "CodexDesktop 无法识别为 cmdlet",
            "Connection was reset",
            "完全退出",
            "同意",
        ):
            self.assertIn(phrase, csdn_article)
        self.assertNotIn("$", csdn_article)

        self.assertIn("匿名限流", privacy)
        self.assertIn("不要求注册、登录、申请、逐人批准或个人凭据", terms)
        self.assertIn("Public knowledge access requires no registration", skill)
        self.assertIn("Only these three tools are available", contract)
        self.assertNotIn("/api/" + "worker", contract)
        self.assertNotIn("JL_" + "WORKER_TOKEN", contract)
        self.assertNotIn("service" + ".db", contract)
        self.assertNotIn("candidate_" + "library", contract)
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

    def test_hooks_are_cross_platform_privacy_limited_and_close_once(self) -> None:
        codex = json.loads(CODEX_HOOKS.read_text(encoding="utf-8"))
        gemini = json.loads(GEMINI_HOOKS.read_text(encoding="utf-8"))
        zcode = json.loads(ZCODE_HOOKS.read_text(encoding="utf-8"))
        self.assertEqual(set(codex["hooks"]), {"UserPromptSubmit", "PostToolUse", "Stop"})
        self.assertEqual(set(gemini["hooks"]), {"BeforeAgent", "AfterTool", "AfterAgent"})
        self.assertEqual(set(zcode["hooks"]), {"UserPromptSubmit", "PostToolUse", "Stop"})
        for event in codex["hooks"].values():
            handler = event[0]["hooks"][0]
            self.assertEqual(handler["type"], "command")
            self.assertIn("command", handler)
            self.assertIn("commandWindows", handler)
            self.assertIn("PLUGIN_ROOT", handler["command"])
            self.assertIn("PLUGIN_ROOT", handler["commandWindows"])
            self.assertIn("run_jl_lifecycle.cmd", handler["commandWindows"])
            self.assertEqual(handler["timeout"], 5)
        for event in gemini["hooks"].values():
            handler = event[0]["hooks"][0]
            self.assertEqual(handler["type"], "command")
            self.assertIn("${extensionPath}", handler["command"])
            self.assertIn("python-launcher.mjs", handler["command"])
            self.assertEqual(handler["timeout"], 5000)
        for event in zcode["hooks"].values():
            handler = event[0]["hooks"][0]
            self.assertEqual(handler["type"], "process")
            self.assertEqual(handler["command"], "node")
            self.assertIn("${ZCODE_PLUGIN_ROOT}", handler["args"][0])
            self.assertIn("python-launcher.mjs", handler["args"][0])
            self.assertEqual(handler["timeoutMs"], 5000)
        launcher = HOOK_WINDOWS_LAUNCHER.read_text(encoding="utf-8").lower()
        for invocation in (
            'python -x utf8 "%~dp0jl_lifecycle.py"',
            'python3 -x utf8 "%~dp0jl_lifecycle.py"',
            'py -3 -x utf8 "%~dp0jl_lifecycle.py"',
        ):
            self.assertIn(invocation, launcher)
        self.assertIn("sys.version_info >= (3, 10)", launcher)
        self.assertIn("disableDelayedExpansion".lower(), launcher)
        self.assertNotIn("invoke-expression", launcher)
        self.assertNotIn("matcher", codex["hooks"]["PostToolUse"][0])
        self.assertNotIn("matcher", gemini["hooks"]["AfterTool"][0])
        self.assertNotIn("matcher", zcode["hooks"]["PostToolUse"][0])

        script_text = HOOK_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("PLUGIN_DATA", script_text)
        self.assertIn("ZCODE_PLUGIN_DATA", script_text)
        self.assertIn("tool_response", script_text)
        self.assertIn("knowledge_outcome", script_text)
        self.assertIn("queried_task_hash", script_text)
        self.assertIn("work_revision", script_text)
        self.assertIn("candidate_revision", script_text)
        self.assertIn("read_only_outcome", script_text)
        self.assertNotIn("transcript_path", script_text)
        self.assertNotIn("last_assistant_message", script_text)

    def test_hook_requires_exact_consent_but_allows_the_disclosure_turn(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            injected = invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "帮我修复杰理 SDK ANC 无效"},
            )
            self.assertIn(
                "unified bundled workflow",
                injected["hookSpecificOutput"]["additionalContext"],
            )

            invoke_lifecycle_hook(state_dir, consent_tool_event(False))
            disclosure_stop = invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "Stop", "last_assistant_message": "请输入同意。"},
            )
            self.assertNotIn("decision", disclosure_stop)

            agreement = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "UserPromptSubmit", "prompt": "同意"}
            )
            self.assertIn(
                "grant --accept", agreement["hookSpecificOutput"]["additionalContext"]
            )
            first_stop = invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"})
            second_stop = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "Stop", "stop_hook_active": True}
            )
            self.assertEqual(first_stop["decision"], "block")
            self.assertEqual(second_stop["decision"], "block")

            invoke_lifecycle_hook(state_dir, consent_tool_event(True, grant=True))
            keywords_only = invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "Stop",
                    "stop_hook_active": True,
                    "last_assistant_message": (
                        "usage recorded; solution candidate; server gap; knowledge closeout"
                    ),
                },
            )
            self.assertEqual(keywords_only["decision"], "block")

            state = json.loads(
                lifecycle_state_path(state_dir).read_text(encoding="utf-8")
            )
            self.assertEqual(
                set(state),
                {
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
                },
            )
            self.assertTrue(state["consent_granted"])
            self.assertIsNone(state["knowledge_outcome"])
            self.assertNotIn("帮我修复", json.dumps(state, ensure_ascii=False))

    def test_hook_records_successful_query_result_without_retaining_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "排查 AC701N ANC 切换问题"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))

            task_id = "task-private-value-must-not-be-stored"
            private_fragment_text = "private fragment text must not be stored"
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "mcp__jl-knowledge-base__query_task_fragments",
                    "tool_input": {"task_id": task_id, "query": "ANC mode decision"},
                    "tool_response": {
                        "isError": False,
                        "structuredContent": {
                            "gateway_version": "knowledge-v1",
                            "task": {"task_id": task_id},
                            "fragments": [
                                {"fragment_id": "opaque", "summary": private_fragment_text}
                            ],
                        },
                    },
                },
            )
            closed = invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "Stop", "last_assistant_message": "已完成当前工作。"},
            )
            self.assertNotIn("decision", closed)

            state_text = lifecycle_state_path(state_dir).read_text(encoding="utf-8")
            state = json.loads(state_text)
            self.assertEqual(state["knowledge_outcome"], "usage_recorded")
            self.assertFalse(state["jl_task_active"])
            self.assertEqual(len(state["queried_task_hash"]), 64)
            self.assertNotIn(task_id, state_text)
            self.assertNotIn(private_fragment_text, state_text)

    def test_hook_reuses_one_time_consent_for_a_later_natural_language_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "排查 AC701N ANC 切换问题"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True, grant=True))
            first_task_id = "first-task"
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "mcp__server__query_task_fragments",
                    "tool_input": {"task_id": first_task_id},
                    "tool_response": {
                        "structuredContent": {
                            "task": {"task_id": first_task_id},
                            "fragments": [],
                        }
                    },
                },
            )
            self.assertNotIn(
                "decision",
                invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"}),
            )

            second_prompt = invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "再帮我处理杰理耳机通透模式底噪",
                },
            )
            self.assertIn(
                "never ask for a $Skill name",
                second_prompt["hookSpecificOutput"]["additionalContext"],
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            state = json.loads(
                lifecycle_state_path(state_dir).read_text(encoding="utf-8")
            )
            self.assertTrue(state["consent_granted"])
            self.assertFalse(state["agreement_reply_seen"])
            self.assertIsNone(state["knowledge_outcome"])

    def test_hook_does_not_reuse_an_outcome_from_a_different_server_task(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            state_path = lifecycle_state_path(state_dir)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "排查杰理 TWS 配对问题"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            for task_id, fragments in (
                ("first-task", [{"fragment_id": "one"}]),
                ("second-task", []),
            ):
                invoke_lifecycle_hook(
                    state_dir,
                    {
                        "hook_event_name": "PostToolUse",
                        "tool_name": "mcp__server__query_task_fragments",
                        "tool_input": {"task_id": task_id},
                        "tool_response": {
                            "structuredContent": {
                                "task": {"task_id": task_id},
                                "fragments": fragments,
                            }
                        },
                    },
                )
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["knowledge_outcome"], "server_gap")
            self.assertEqual(
                state["queried_task_hash"],
                hashlib.sha256(b"second-task").hexdigest(),
            )

    def test_hook_no_hit_becomes_gap_and_queued_solution_replaces_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            state_path = lifecycle_state_path(state_dir)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "帮我查杰理 TWS ANC 异常"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            task_id = "current-task-id"
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "mcp__server__query_task_fragments",
                    "tool_input": {"task_id": task_id, "query": "specific ANC failure"},
                    "tool_response": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(
                                    {
                                        "gateway_version": "knowledge-v1",
                                        "task": {"task_id": task_id},
                                        "fragments": [],
                                    }
                                ),
                            }
                        ]
                    },
                },
            )
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["knowledge_outcome"],
                "server_gap",
            )

            candidate = {"candidate_kind": "solution"}
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "mcp__server__submit_knowledge_candidate",
                    "tool_input": {"task_id": "different-task", "candidate": candidate},
                    "tool_response": {
                        "structuredContent": {
                            "task_id": "different-task",
                            "status": "queued_for_review",
                        }
                    },
                },
            )
            self.assertEqual(
                json.loads(state_path.read_text(encoding="utf-8"))["knowledge_outcome"],
                "server_gap",
            )
            for status, expected in (
                ("withdrawn", "server_gap"),
                ("queued_for_review", "solution_candidate"),
            ):
                invoke_lifecycle_hook(
                    state_dir,
                    {
                        "hook_event_name": "PostToolUse",
                        "tool_name": "mcp__server__submit_knowledge_candidate",
                        "tool_input": {"task_id": task_id, "candidate": candidate},
                        "tool_response": {
                            "structuredContent": {"task_id": task_id, "status": status}
                        },
                    },
                )
                self.assertEqual(
                    json.loads(state_path.read_text(encoding="utf-8"))[
                        "knowledge_outcome"
                    ],
                    expected,
                )

            closed = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "Stop", "stop_hook_active": True}
            )
            self.assertNotIn("decision", closed)

    def test_hook_rejects_failed_malformed_and_cross_task_tool_results(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "排查杰理 SDK 问题"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            for response in (
                {"isError": True, "structuredContent": {"fragments": []}},
                {"structuredContent": {"ok": False, "fragments": []}},
                {"structuredContent": {"task": {"task_id": "other"}, "fragments": []}},
            ):
                invoke_lifecycle_hook(
                    state_dir,
                    {
                        "hook_event_name": "PostToolUse",
                        "tool_name": "mcp__server__query_task_fragments",
                        "tool_input": {"task_id": "expected"},
                        "tool_response": response,
                    },
                )
            first_stop = invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"})
            second_stop = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "Stop", "stop_hook_active": True}
            )
            self.assertEqual(first_stop["decision"], "block")
            self.assertEqual(second_stop["decision"], "block")
            state = json.loads(
                lifecycle_state_path(state_dir).read_text(encoding="utf-8")
            )
            self.assertIsNone(state["knowledge_outcome"])

    def test_root_and_client_package_shared_files_are_identical(self) -> None:
        individual = (
            ".mcp.json",
            "PRIVACY.md",
            "TERMS.md",
            "LICENSE",
            "hooks/jl_lifecycle.py",
            "hooks/python-launcher.mjs",
            "hooks/run_jl_lifecycle.cmd",
        )
        for package in (CODEX_PACKAGE, ZCODE_PACKAGE):
            for relative in individual:
                self.assertEqual(
                    (ROOT / relative).read_bytes(),
                    (package / relative).read_bytes(),
                    msg=f"public client package is stale: {package.name}/{relative}",
                )
        for directory in ("commands", "skills", "scripts"):
            root_files = {
                path.relative_to(ROOT / directory)
                for path in (ROOT / directory).rglob("*")
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
            }
            for package in (CODEX_PACKAGE, ZCODE_PACKAGE):
                package_files = {
                    path.relative_to(package / directory)
                    for path in (package / directory).rglob("*")
                    if path.is_file()
                    and "__pycache__" not in path.parts
                    and path.suffix != ".pyc"
                }
                self.assertEqual(
                    root_files,
                    package_files,
                    msg=f"file set mismatch: {package.name}/{directory}",
                )
                for relative in root_files:
                    self.assertEqual(
                        (ROOT / directory / relative).read_bytes(),
                        (package / directory / relative).read_bytes(),
                        msg=f"public client package is stale: {package.name}/{directory}/{relative}",
                    )
        self.assertTrue(MANIFEST.is_file())
        self.assertFalse((CODEX_PACKAGE / ".zcode-plugin" / "plugin.json").exists())
        self.assertTrue(ZCODE_MANIFEST.is_file())
        self.assertFalse((ZCODE_PACKAGE / ".codex-plugin" / "plugin.json").exists())
        self.assertFalse((ROOT / ".codex-plugin" / "plugin.json").exists())
        self.assertFalse((ROOT / ".zcode-plugin" / "plugin.json").exists())

    def test_release_has_one_version_name_and_candidate_area(self) -> None:
        text = distribution_text()
        self.assertNotIn("0.7.0", text)
        self.assertNotIn("candidate_" + "library", text)
        self.assertNotIn("jl-private-knowledge", text.replace("jl-private-knowledge-client", ""))
        self.assertIn('"layer": "candidate_area"', text)
        for path in (
            ROOT / ".mcp.json",
            CODEX_PACKAGE / ".mcp.json",
            ZCODE_PACKAGE / ".mcp.json",
        ):
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(set(payload["mcpServers"]), {MCP_NAME})
        self.assertEqual(
            json.loads(MANIFEST.read_text(encoding="utf-8"))["version"],
            "0.7.1",
        )
        self.assertEqual(
            json.loads(ZCODE_MANIFEST.read_text(encoding="utf-8"))["version"],
            "0.7.1",
        )

    def test_node_python_launcher_handles_chinese_space_and_exclamation_path(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node.js is required by the Gemini and ZCode hook packages")
        with tempfile.TemporaryDirectory() as temporary:
            special_root = Path(temporary) / "中文 space !" / "hooks"
            special_root.mkdir(parents=True)
            shutil.copy2(HOOK_NODE_LAUNCHER, special_root / HOOK_NODE_LAUNCHER.name)
            shutil.copy2(HOOK_SCRIPT, special_root / HOOK_SCRIPT.name)
            state_dir = Path(temporary) / "state 中文 !"
            result = subprocess.run(
                [str(node), str(special_root / HOOK_NODE_LAUNCHER.name)],
                input=json.dumps(
                    {
                        "session_id": "launcher-session",
                        "hook_event_name": "BeforeAgent",
                        "prompt": "帮我排查 AC701N ANC 问题",
                    },
                    ensure_ascii=False,
                ),
                text=True,
                encoding="utf-8",
                capture_output=True,
                env={**os.environ, "PLUGIN_DATA": str(state_dir)},
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            output = json.loads(result.stdout)
            self.assertEqual(
                output["hookSpecificOutput"]["hookEventName"], "BeforeAgent"
            )
            self.assertTrue(lifecycle_state_path(state_dir, "launcher-session").is_file())

    def test_hook_edit_and_build_revisions_require_fresh_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "修改杰理 ANC 并编译"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            task_id = "revision-task"
            invoke_lifecycle_hook(
                state_dir,
                query_tool_event(task_id, [{"fragment_id": "one"}]),
            )
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "apply_patch",
                    "tool_input": {"patch": "not persisted by the hook"},
                    "tool_response": {"ok": True},
                },
            )
            blocked = invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"})
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("latest work revision", blocked["reason"])

            invoke_lifecycle_hook(state_dir, candidate_tool_event(task_id))
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": "make all"},
                    "tool_response": {"exit_code": 0, "output": "success"},
                },
            )
            stale = invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"})
            self.assertEqual(stale["decision"], "block")
            invoke_lifecycle_hook(state_dir, candidate_tool_event(task_id))
            closed = invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"})
            self.assertNotIn("decision", closed)

    def test_read_only_reusable_marker_requires_solution_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "查 AC701N ANC 为什么无效"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            task_id = "diagnosis-task"
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Read",
                    "tool_input": {"file_path": "not persisted"},
                    "tool_response": {"content": "not persisted"},
                },
            )
            invoke_lifecycle_hook(state_dir, query_tool_event(task_id))
            missing_marker = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "Stop"}
            )
            self.assertEqual(missing_marker["decision"], "block")
            self.assertIn("mark-outcome", missing_marker["reason"])

            invoke_lifecycle_hook(state_dir, marker_tool_event("reusable"))
            missing_candidate = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "Stop"}
            )
            self.assertEqual(missing_candidate["decision"], "block")
            self.assertIn("fresh sanitized solution candidate", missing_candidate["reason"])
            invoke_lifecycle_hook(state_dir, candidate_tool_event(task_id))
            closed = invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"})
            self.assertNotIn("decision", closed)

    def test_read_only_none_marker_allows_query_closeout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "查杰理 SDK 是否有已知结论"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "PostToolUse",
                    "tool_name": "Grep",
                    "tool_input": {"pattern": "feature"},
                    "tool_response": {"content": "no reusable result"},
                },
            )
            invoke_lifecycle_hook(state_dir, query_tool_event("none-marker-task"))
            invoke_lifecycle_hook(state_dir, marker_tool_event("none"))
            closed = invoke_lifecycle_hook(state_dir, {"hook_event_name": "Stop"})
            self.assertNotIn("decision", closed)

    def test_supplemental_prompt_keeps_current_task_revision_and_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "UserPromptSubmit", "prompt": "排查杰理 TWS 配对"},
            )
            invoke_lifecycle_hook(state_dir, consent_tool_event(True))
            invoke_lifecycle_hook(
                state_dir,
                query_tool_event("supplemental-task", [{"fragment_id": "one"}]),
            )
            before = json.loads(lifecycle_state_path(state_dir).read_text(encoding="utf-8"))
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "再补充看一下这个杰理配对边界",
                },
            )
            after = json.loads(lifecycle_state_path(state_dir).read_text(encoding="utf-8"))
            self.assertEqual(before, after)

    def test_lifecycle_state_is_isolated_by_client_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            invoke_lifecycle_hook(
                state_dir,
                {
                    "session_id": "session-a",
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "排查 AC701N ANC",
                },
            )
            invoke_lifecycle_hook(
                state_dir,
                {
                    "session_id": "session-b",
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "处理杰理 TWS 配对",
                },
            )
            invoke_lifecycle_hook(
                state_dir,
                {"session_id": "session-a", **consent_tool_event(True)},
            )
            invoke_lifecycle_hook(
                state_dir,
                {
                    "session_id": "session-a",
                    **query_tool_event("session-a-task", [{"fragment_id": "one"}]),
                },
            )
            state_a = json.loads(
                lifecycle_state_path(state_dir, "session-a").read_text(encoding="utf-8")
            )
            state_b = json.loads(
                lifecycle_state_path(state_dir, "session-b").read_text(encoding="utf-8")
            )
            self.assertEqual(state_a["knowledge_outcome"], "usage_recorded")
            self.assertIsNone(state_b["knowledge_outcome"])
            self.assertFalse(state_b["consent_checked"])

    def test_gemini_event_names_and_llm_content_envelope_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            started = invoke_lifecycle_hook(
                state_dir,
                {"hook_event_name": "BeforeAgent", "prompt": "排查 AC701N ANC"},
            )
            self.assertEqual(
                started["hookSpecificOutput"]["hookEventName"], "BeforeAgent"
            )
            invoke_lifecycle_hook(
                state_dir,
                {
                    "hook_event_name": "AfterTool",
                    "tool_name": "run_shell_command",
                    "tool_input": {"command": "python scripts/knowledge_outbox.py status"},
                    "tool_response": {
                        "llmContent": json.dumps({"consent_granted": True})
                    },
                },
            )
            denied = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "AfterAgent"}
            )
            self.assertEqual(denied["decision"], "deny")
            invoke_lifecycle_hook(
                state_dir,
                query_tool_event(
                    "gemini-task",
                    [{"fragment_id": "one"}],
                    event_name="AfterTool",
                    gemini_envelope=True,
                ),
            )
            closed = invoke_lifecycle_hook(
                state_dir, {"hook_event_name": "AfterAgent"}
            )
            self.assertNotIn("decision", closed)


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
        command = [
            sys.executable,
            "-X",
            "utf8",
            str(OUTBOX),
            "--state-dir",
            str(self.state_dir),
            *arguments,
        ]
        result = subprocess.run(
            command,
            input=json.dumps(candidate, ensure_ascii=False) if candidate is not None else None,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected_code, msg=result.stderr or result.stdout)
        output = result.stdout if result.returncode == 0 else result.stderr
        return json.loads(output)

    @staticmethod
    def candidate() -> dict[str, object]:
        return {
            "candidate_kind": "solution",
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

    def test_structured_outcome_marker_requires_consent_and_stores_no_answer(self) -> None:
        rejected = self.run_outbox("mark-outcome", "--reusable", expected_code=2)
        self.assertIn("consent", str(rejected["error"]).lower())
        self.grant()
        reusable = self.run_outbox("mark-outcome", "--reusable")
        none = self.run_outbox("mark-outcome", "--none")
        self.assertTrue(reusable["ok"])
        self.assertTrue(none["ok"])
        self.assertEqual(reusable["outcome_marker"], "reusable")
        self.assertEqual(none["outcome_marker"], "none")
        persisted = "\n".join(
            path.read_text(encoding="utf-8")
            for path in self.state_dir.rglob("*")
            if path.is_file()
        )
        self.assertNotIn("reusable", persisted)
        self.assertNotIn("none", persisted)

    def test_requires_one_time_consent_then_deduplicates_stably(self) -> None:
        status = self.run_outbox("status")
        self.assertFalse(status["consent_granted"])
        self.assertFalse(status["shared_knowledge_access_enabled"])
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

        approximate = self.run_outbox(
            "grant", "--accept", "我同意", expected_code=2
        )
        self.assertIn("同意", str(approximate["error"]))
        self.assertFalse(self.run_outbox("status")["consent_granted"])

        self.grant()
        self.assertTrue(self.run_outbox("status")["shared_knowledge_access_enabled"])
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
        self.assertEqual(entry["candidate"]["candidate_kind"], "solution")
        self.assertNotIn("task_id", entry)

    def test_knowledge_gap_is_stored_only_as_an_unverified_issue(self) -> None:
        self.grant()
        gap = self.candidate()
        gap.update(
            {
                "candidate_kind": "knowledge_gap",
                "semantic_id": "issue.anc-fade-delay-missing",
                "node_type": "issue",
                "title": "ANC fade delay knowledge gap",
                "summary": "No reliable reusable answer was established for the scoped ANC fade delay decision.",
                "lifecycle_status": "processed_pending_verification",
                "evidence_level": "E1",
            }
        )
        queued = self.enqueue(gap)
        self.assertTrue(queued["queued"])
        entry = self.run_outbox("ready", "--limit", "3")["entries"][0]
        self.assertEqual(entry["candidate"]["candidate_kind"], "knowledge_gap")

        invalid = copy.deepcopy(gap)
        invalid["evidence_level"] = "E2"
        response = self.run_outbox(
            "enqueue",
            "--candidate-file",
            "-",
            "--sanitization-ack",
            SANITIZATION_ACK,
            candidate=invalid,
            expected_code=2,
        )
        self.assertIn("knowledge_gap", str(response["error"]))

    def test_candidate_kind_is_required_instead_of_silently_assuming_solution(self) -> None:
        self.grant()
        candidate = self.candidate()
        del candidate["candidate_kind"]
        response = self.run_outbox(
            "enqueue",
            "--candidate-file",
            "-",
            "--sanitization-ack",
            SANITIZATION_ACK,
            candidate=candidate,
            expected_code=2,
        )
        self.assertIn("candidate_kind", str(response["error"]))

    def test_relation_type_must_match_the_gateway_enum(self) -> None:
        self.grant()
        candidate = self.candidate()
        candidate["relations"] = [
            {"type": "related_to", "target_semantic_id": "capability.anc-transparency"}
        ]
        response = self.run_outbox(
            "enqueue",
            "--candidate-file",
            "-",
            "--sanitization-ack",
            SANITIZATION_ACK,
            candidate=candidate,
            expected_code=2,
        )
        self.assertIn("depends_on", str(response["error"]))

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
