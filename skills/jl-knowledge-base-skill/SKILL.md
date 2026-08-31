---
name: jl-knowledge-base-skill
description: After required one-time user agreement, query a configured JL SDK knowledge gateway for a few task-scoped, evidence-labelled fragments and automatically contribute sanitized candidate experience or knowledge gaps from substantive Jieli SDK work. Never use it to browse, export, or reconstruct the corpus.
---

# JL Knowledge Base Skill

Use the private gateway as supporting evidence for a concrete JL SDK task. The public Codex, Gemini CLI, and ZCode package contains no private knowledge, endpoint credentials, customer data, or writable access to the verified corpus.

## Required one-time access and contribution agreement

Before **any** `create_knowledge_task`, `query_task_fragments`, or `submit_knowledge_candidate` call, locate `<bundle-root>/scripts/knowledge_outbox.py` from this installed bundle. Choose the first available `python`, `python3`, or `py -3` command that reports Python 3.10 or newer and use it to run the helper's `status` command. If no suitable interpreter or helper is available, explain that shared knowledge cannot be enabled yet and continue local-only SDK work; never bypass the consent record. If current consent is absent, show this disclosure prominently and stop all shared-knowledge calls for the current turn:

> ### ⚠️ 首次使用确认
>
> 使用本共享知识库，需要同意参加“知识共同成长计划”：系统会把任务中形成的可复用经验，整理成脱敏知识候选并上传审核。大家一起贡献，知识库才能越来越全面，后续解决问题也会更快。
>
> 不会上传完整源码、SDK、原理图、UI 文档、固件、原始日志、密码、密钥或客户身份信息。新内容会先进入候选知识库，审核通过后才会提供给其他用户。
>
> 如同意，请输入：**同意**
> 未输入“同意”，不能访问共享知识库。

Only after the user's next explicit answer is exactly `同意` may the client run `grant --accept 同意`. Never infer, translate, auto-fill, or grant consent from installation, invocation, prior intent, an approximate answer, a managed default, or the model's own reasoning. Keep the helper's returned `disclosure_version`; every new knowledge task must send it as `contribution_consent_version`. If the gateway says this Skill is outdated or shared access from the installed version is paused, show its complete message and both direct upgrade URLs without shortening them: `https://github.com/dongke141219/jl-knowledge-base-skill` and `https://gitee.com/fofo123/jl-knowledge-base-skill`. Stop further shared calls until the user updates, restarts the client, begins a new task, sees the current disclosure, and explicitly agrees again. Until current consent exists, the shared gateway is unavailable; local-only SDK inspection, editing, and building may continue.

Current consent covers both task-scoped knowledge access and automatic contribution of sanitized candidates. After it exists, do not interrupt later tasks for per-task confirmation. Honor revocation immediately: revocation deletes the unsent local outbox and disables later shared-knowledge access until the user agrees again.

## Query task-scoped knowledge

1. Inspect the current project evidence first. Query only when JL-specific prior knowledge would change a real implementation or verification decision.
2. Infer product, chip, SDK version, board, and requested behavior from the current authorized project before asking the user to repeat them. If neither project evidence nor the user's message provides enough scope, ask one short plain-language clarification. Then call `create_knowledge_task` with one narrow, sanitized task description, `contribution_consent: "同意"`, and `contribution_consent_version: "2026-08-31-v2"`. Keep its returned `task_id` only for this task; never invent an ID, reuse it for another task or customer, or persist it as knowledge. Treat the returned `candidate_taxonomy` as the only valid product/domain classification for later contributions.
3. Call `query_task_fragments` with that server-issued `task_id`, `include_incubator: false`, the decision to make, observed behavior, and already-known evidence. Remove credentials, customer identity, private paths, complete source files, and unrelated logs. Only administrator-reviewed formal shared knowledge may be returned; candidate-library items and knowledge gaps are not query results.
4. Request only the few fragments needed for that decision. Never send an empty or wildcard query; request an inventory, identifier range, pagination cursor, corpus statistics, bulk result, source document, or export; or chain queries to reconstruct the corpus.
5. Use a follow-up query only for a named unresolved decision and the same `task_id`. Stop when the task has enough evidence.
6. Preserve the evidence label and applicability of every fragment used. Cite it as `[K:<fragment-id>][E1|E2|E3][scope:<applicability>]` and state caveats. Project source, a real build, and scenario-correct hardware results take precedence over a conflicting fragment.

Evidence labels mean:

- `E1`: implemented, inspected, or reproduced, but not proven by a real build.
- `E2`: passed a real build for the stated scope.
- `E3`: passed scenario-correct hardware verification for the stated scope.

Do not present a fragment outside its platform, SDK, board, or product scope as a universal rule. Do not persist returned fragments after the task or republish them as a local knowledge bundle.

## Automatically contribute substantive work

When current consent exists, contribution is automatic after every substantive JL task. A task is substantive when it changes or integrates JL source/configuration, produces a reusable diagnosis or fix, completes a real build, records an explicit hardware result, or reveals a specific shared-knowledge gap. Do not contribute ordinary questions, browsing, formatting, or a duplicate narration of private gateway fragments.

Contribution is outbox-first and best effort:

1. At task start, opportunistically process up to three due outbox entries. Use the anonymous public MCP connection only while the operator's global service switch is enabled; never run or contact the knowledge owner's AI coding client.
2. Finish the user's actual engineering work first. If the work produced a concrete reusable finding, derive the smallest `product -> domain -> capability -> subfeature -> boundary -> issue` chain from evidence created in this task, not from private fragments returned by the gateway, and set `candidate_kind: solution`.
3. If a narrow query returned no relevant fragment and the task still ended without a reliable reusable answer, create one `candidate_kind: knowledge_gap` issue record describing only the missing product/chip/SDK/function scope and the unanswered decision. Never turn a guess or failed attempt into a solution candidate. A knowledge gap is visible to administrators for future work and can never be served as an answer or merged as formal knowledge.
4. Create separate stable-semantic candidates only when independent subfunctions deserve separate reuse. Keep every field short and structured. Strip source text, raw logs, customer/company names, email addresses, IPv4/IPv6 addresses, MAC addresses, hostnames, URLs, local or NAS paths, file archives, KEY material, credentials, tokens, private protocol payloads, and any returned private fragment text.
5. Enqueue each candidate with the outbox helper before attempting the network call. Its canonical SHA-256 is the stable `idempotency_key`; the queue contains no `task_id`, endpoint, credential, source, or raw log.
6. Call `submit_knowledge_candidate` with a consent-bound server-issued `task_id`, the candidate, and that `idempotency_key`. A queued item whose old task expired gets a new narrow task; never persist or reuse the old task ID.
7. Delete the local item only when the server returns `status: queued_for_review`. This means the sanitized item is stored in the candidate library for internal review; it is not searchable by public users and is not part of the formal shared knowledge base.
8. On offline, timeout, operator stop, or rate-limit failure, schedule the local item for bounded exponential retry and leave the engineering result successful. On privacy/schema/scope rejection, remove the unsafe item rather than retrying it unchanged. If the server returns `status: withdrawn` for a previously withdrawn identical hash, drop it as `server_withdrawn`; do not retry the same rejected knowledge forever. A genuinely corrected implementation must produce a changed candidate and a new idempotency hash.

Lifecycle and evidence must match what actually happened:

- A meaningful performed flow without real build PASS is `processed_pending_verification` / `E1`.
- Real build PASS is `compiled_pending_hardware` / `E2`.
- Explicit negative build or hardware evidence is `verified_failed` / `E1` or `E2`; silence is not failure.
- Scenario-correct hardware PASS may be submitted as `verified_pass` / `E3`, but an external claim remains pending in the candidate library until internal review; never describe it as server-verified or immediately reusable.

Every candidate must carry a server-controlled canonical `product_id` and `domain_id` before `capability_id`, `semantic_id`, and `parent_semantic_id`. The initial taxonomy is:

- `product.tws-earbuds`: `domain.input-output`, `domain.power-charging`, `domain.audio-acoustic`, `domain.bluetooth-tws`, `domain.app-integration`, or `domain.production-delivery`.
- `product.headset`: `domain.input-output`, `domain.power-charging`, `domain.audio-acoustic`, `domain.bluetooth`, `domain.app-integration`, or `domain.production-delivery`.

Do not invent spelling variants such as a singular product name or a generic `domain.audio`. A new product or domain must be added to the server taxonomy first. These IDs describe reusable product form and function domain, never a customer, company, project, account, or local directory. The complete classification is `product_id -> domain_id -> capability_id -> semantic_id`, while `node_type` and `parent_semantic_id` extend the chain through subfeature, boundary, and issue nodes. Add a new subfunction or extension to an existing feature chain instead of duplicating the whole feature. The server owns cross-user deduplication and verified promotion.

Read [references/contribution-workflow.md](references/contribution-workflow.md) for the helper commands and retry handshake. Read [references/gateway-contract.md](references/gateway-contract.md) for MCP payloads and server controls.

## Anonymous public and internal-token boundary

The current user's already-running Codex, Gemini CLI, or ZCode session may summarize its own task into a candidate. The outbox helper performs only local JSON validation/storage, and the gateway performs only anonymous rate-limited lookup/deduplication/storage. Neither component starts an AI client, calls a model, has the owner's login, or spends the owner's AI usage. A GitHub or company user therefore uses their own AI account; only workloads deliberately run by the owner's web worker use the owner's configured account.

Public knowledge access requires no registration, login, application, per-user approval, or individual credential, but it does require the user's one-time `同意` contribution agreement. When the operator enables the single GitHub-service switch, every consenting public installation may use the gateway anonymously; when the operator stops it, every public installation must treat the gateway as unavailable and continue with the local engineering shell. Never fall back to an internal worker route, the owner's full global Skill, direct NAS access, or a customer-web-platform account.

## Failure boundaries

- If consent is absent, task creation fails, the operator has stopped public access, or the MCP dependency is unavailable, explain that shared knowledge was not queried and continue from local project evidence. Do not call create/query/submit before consent, and do not call query or submit without a consent-bound server-issued `task_id`.
- A gateway or outbox outage must not block, fail, or roll back the JL engineering task. Preserve a privacy-checked candidate locally only when consent is current, then retry opportunistically on later invocations.
- Do not bypass the public master switch, anonymous rate limits, task limits, or response budgets; do not fall back to direct NAS/file access or launch a remote model worker.
- If a response appears to expose a corpus dump, private path, credential, or unrelated customer data, do not store, contribute, or reproduce it; report the gateway policy failure to the operator.
