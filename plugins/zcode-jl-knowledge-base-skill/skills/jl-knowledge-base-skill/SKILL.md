---
name: jl-knowledge-base-skill
description: "Handle natural-language Jieli (JL) SDK implementation and diagnosis end to end: exact one-time consent, scoped shared guidance, local engineering, real-build evidence, and mandatory sanitized closeout. Never browse or reconstruct the corpus."
---

# JL Knowledge Base Skill

This is the only visible JL workflow. A user can naturally ask a JL/Jieli SDK question; do not require a `$` Skill name, fixed command, or repeated chip model. The public Codex, Gemini CLI, and ZCode package contains no private knowledge, endpoint credentials, customer data, or writable access to the verified corpus.

## Unified main workflow

For every concrete JL task, complete this order without handing the user to a second public Skill:

1. Read local instructions and inspect the authorized project before editing. Infer product, chip, SDK version, board, requested behavior, configuration ownership, and build entry from the project where possible. Ask one short plain-language question only when the project and request cannot provide enough scope.
2. Apply the exact one-time consent gate below before any shared call. After current consent, create one narrow server task and query only the few formal fragments that affect a real decision. Every gateway tool call includes `client_version: "0.7.1"`.
3. Trace the local implementation and make the smallest complete change. Respect existing feature gates, board definitions, and Makefile/build scripts. Never invent or fetch a signing KEY, private library, partner asset, credential, or protocol package; never commit, quote, or upload any such material.
4. Run the real project build when the environment permits. Report E1 for inspected/implemented work without a target build, E2 for a passing real build pending hardware, and E3 only for scenario-correct hardware confirmation. A static check or successful build is not hardware proof.
5. Finish with the mandatory evidence-backed one-outcome knowledge closeout below. The bundled Codex hook accepts only the current MCP tool's successful structured result; answer wording, a local queue entry, or a previous task cannot satisfy it. The companion files and hooks only support this main workflow; they are not a user-facing alternate entry.

Project source, a real build, and correct hardware evidence override a conflicting fragment. Preserve each fragment's evidence level, scope, and limitation as `[K:<fragment-id>][E1|E2|E3][scope:<applicability>]`; never persist or republish it.

## Required one-time access and contribution agreement

Before **any** `create_knowledge_task`, `query_task_fragments`, or `submit_knowledge_candidate` call, locate `<bundle-root>/scripts/knowledge_outbox.py` from this installed bundle. Choose the first available `python`, `python3`, or `py -3` command that reports Python 3.10 or newer and use it to run the helper's `status` command. If no suitable interpreter or helper is available, explain that shared knowledge cannot be enabled yet and continue local-only SDK work; never bypass the consent record. If current consent is absent, show this disclosure prominently and stop all shared-knowledge calls for the current turn:

> ### ⚠️ 首次使用确认
>
> 使用本共享知识库，需要同意参加“知识共同成长计划”：系统会把任务中形成的可复用经验，整理成脱敏知识候选并上传审核。这个唯一知识库不只收问题点，也包括能实现的功能、工程实现指南、产品/芯片/SDK 适用范围、边界、问题解法以及编译/实机证据。大家一起贡献，知识库才能越来越全面，后续解决问题也会更快。
>
> 不会上传完整源码、SDK、原理图、UI 文档、固件、原始日志、密码、密钥或客户身份信息。新内容会先进入同一个知识库内的候选区，审核通过并进入正式区后才会提供给其他用户。
>
> 如同意，请输入：**同意**
> 未输入“同意”，不能访问共享知识库。

Only after the user's next explicit answer is exactly `同意` may the client run `grant --accept 同意`. Never infer, translate, auto-fill, or grant consent from installation, invocation, prior intent, an approximate answer, a managed default, or the model's own reasoning. Keep the helper's returned `disclosure_version`; every new knowledge task must send it as `contribution_consent_version`. If the gateway says this Skill is outdated or shared access from the installed version is paused, show its complete message and both direct upgrade URLs without shortening them: `https://github.com/dongke141219/jl-knowledge-base-skill` and `https://gitee.com/fofo123/jl-knowledge-base-skill`. Stop further shared calls until the user updates, restarts the client, begins a new task, sees the current disclosure, and explicitly agrees again. Until current consent exists, the shared gateway is unavailable; local-only SDK inspection, editing, and building may continue.

Current consent covers both task-scoped knowledge access and automatic contribution of sanitized candidates. After it exists, do not interrupt later tasks for per-task confirmation. Honor revocation immediately: revocation deletes the unsent local outbox and disables later shared-knowledge access until the user agrees again.

## Query task-scoped knowledge

1. Inspect the current project evidence first. Query only when JL-specific prior knowledge would change a real implementation or verification decision. A concrete question such as “can this feature be implemented on this chip/SDK, and how?” is a valid narrow query: request the matching capability and engineering-guide fragments for that scope, never an inventory of everything the knowledge base contains.
2. Infer product, chip, SDK version, board, and requested behavior from the current authorized project before asking the user to repeat them. If neither project evidence nor the user's message provides enough scope, ask one short plain-language clarification. Then call `create_knowledge_task` with one narrow, sanitized task description, `contribution_consent: "同意"`, `contribution_consent_version: "2026-08-31-v2"`, and `client_version: "0.7.1"`. Keep its returned `task_id` only for this task; never invent an ID, reuse it for another task or customer, or persist it as knowledge. Treat the returned `candidate_taxonomy` as the only valid product/domain classification for later contributions.
3. Call `query_task_fragments` with that server-issued `task_id`, `include_incubator: false`, `client_version: "0.7.1"`, the decision to make, observed behavior, and already-known evidence. Remove credentials, customer identity, private paths, complete source files, and unrelated logs. Only administrator-reviewed content from the formal area of the one shared knowledge base may be returned; items in its candidate area and knowledge gaps are not query results.
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
2. Finish the user's actual engineering work first. After a read-only local inspection or diagnosis, always run `knowledge_outbox.py mark-outcome --reusable` when it established a reusable result, or `knowledge_outbox.py mark-outcome --none` when it did not. This structured marker contains no answer text. Never choose from keywords in the final response. A reusable marker advances the work revision and must be followed by an accepted solution candidate before closeout.
3. If the work produced a concrete reusable finding, derive the smallest `product -> domain -> capability -> subfeature -> boundary -> issue` chain from evidence created in this task, not from private fragments returned by the gateway, and set `candidate_kind: solution`.
4. If a successful narrow query returned no relevant fragment, the server records that scoped miss as a knowledge gap. Do not invent a solution or submit a duplicate gap merely to satisfy the lifecycle hook. A gap is visible to administrators for future work and can never be served as an answer or merged as formal knowledge.
5. Create separate stable-semantic candidates only when independent subfunctions deserve separate reuse. Keep every field short and structured. Strip source text, raw logs, customer/company names, email addresses, IPv4/IPv6 addresses, MAC addresses, hostnames, URLs, local or remote storage paths, file archives, KEY material, credentials, tokens, private protocol payloads, and any returned private fragment text.
6. Enqueue each candidate with the outbox helper before attempting the network call. Its canonical SHA-256 is the stable `idempotency_key`; the queue contains no `task_id`, endpoint, credential, source, or raw log.
7. Call `submit_knowledge_candidate` with a consent-bound server-issued `task_id`, the candidate, that `idempotency_key`, and `client_version: "0.7.1"`. A queued item whose old task expired gets a new narrow task; never persist or reuse the old task ID.
8. Delete the local item only when the server returns `status: queued_for_review`. This means the sanitized item is stored in the candidate area of the one shared knowledge base for internal review; it is not searchable by public users and has not entered the formal area.
9. On offline, timeout, operator stop, or rate-limit failure, schedule the local item for bounded exponential retry and leave the engineering result intact. This local retry is not a successful closeout: a consented task remains open until an actual task-scoped query succeeds, and a reusable solution remains `solution_candidate` only after the server returns `status: queued_for_review`. On privacy/schema/scope rejection, remove the unsafe item rather than retrying it unchanged. If the server returns `status: withdrawn` for a previously withdrawn identical hash, drop it as `server_withdrawn`; do not retry the same rejected knowledge forever. A genuinely corrected implementation must produce a changed candidate and a new idempotency hash.

Lifecycle and evidence must match what actually happened:

- A meaningful performed flow without real build PASS is `processed_pending_verification` / `E1`.
- Real build PASS is `compiled_pending_hardware` / `E2`.
- Explicit negative build or hardware evidence is `verified_failed` / `E1` or `E2`; silence is not failure.
- Scenario-correct hardware PASS may be submitted as `verified_pass` / `E3`, but an external claim remains pending in the candidate area of the one shared knowledge base until internal review; never describe it as server-verified or immediately reusable.

Every candidate must carry a server-controlled canonical `product_id` and `domain_id` before `capability_id`, `semantic_id`, and `parent_semantic_id`. The initial taxonomy is:

- `product.tws-earbuds`: `domain.input-output`, `domain.power-charging`, `domain.audio-acoustic`, `domain.bluetooth-tws`, `domain.app-integration`, or `domain.production-delivery`.
- `product.headset`: `domain.input-output`, `domain.power-charging`, `domain.audio-acoustic`, `domain.bluetooth`, `domain.app-integration`, or `domain.production-delivery`.

Do not invent spelling variants such as a singular product name or a generic `domain.audio`. A new product or domain must be added to the server taxonomy first. These IDs describe reusable product form and function domain, never a customer, company, project, account, or local directory. The complete classification is `product_id -> domain_id -> capability_id -> semantic_id`, while `node_type` and `parent_semantic_id` extend the chain through subfeature, boundary, and issue nodes. Add a new subfunction or extension to an existing feature chain instead of duplicating the whole feature. The server owns cross-user deduplication and verified promotion.

Read [references/contribution-workflow.md](references/contribution-workflow.md) for the helper commands and retry handshake. Read [references/gateway-contract.md](references/gateway-contract.md) for MCP payloads and server controls.

## Mandatory one-outcome closeout

Every substantive JL task with current consent must reach exactly one of these states through the current task's actual successful MCP result before the final answer. The lifecycle state is one enum, so a later successful solution submission replaces the provisional query outcome instead of creating a second closeout. Any project edit, real build, or newly structured reusable finding after the accepted solution advances the work revision and requires a fresh solution submission before closeout. Merely writing any of these words in the answer does nothing:

- **usage recorded**: the current task's successful `query_task_fragments` result contains at least one scoped formal fragment. This is the final state only when no reusable local solution is later queued.
- **server gap**: the current task's successful `query_task_fragments` result contains an empty `fragments` list. The server records the scoped miss; do not fabricate or duplicate a gap candidate.
- **solution candidate**: after the current task has queried, local work produced a concrete reusable finding and `submit_knowledge_candidate` for its sanitized `candidate_kind: solution` returned `status: queued_for_review`. This successful result replaces `usage_recorded` or `server_gap` as the single final state.

Choose `solution candidate` over the query outcome when local evidence produced a reusable result. Failed, malformed, withdrawn, cross-task, or merely queued-locally operations do not count. The Codex `Stop` hook keeps blocking after current consent until one actual closeout exists, including after a previous continuation; there is no second-stop bypass. When consent is absent or revoked, shared knowledge stays unavailable and local-only SDK work may continue without pretending a shared closeout ran.

## Public client boundary

The current user's already-running Codex, Gemini CLI, or ZCode session may summarize its own task into a candidate. The outbox helper performs only local JSON validation/storage, and the shared service performs lookup and contribution handling. Neither component starts an AI client, calls a model, has the author's login, or spends the author's AI usage. Each user works through their own AI client, account, model, subscription, and quota.

Public knowledge access requires no registration, login, application, per-user approval, or individual credential, but it does require the user's one-time `同意` contribution agreement. If the shared service is unavailable, continue from authorized local project evidence. Never fall back to a customer-web-platform account, direct storage access, another private service, or a non-public interface.

## Failure boundaries

- If consent is absent, task creation fails, the operator has stopped public access, or the MCP dependency is unavailable, explain that shared knowledge was not queried and continue from local project evidence. Do not call create/query/submit before consent, and do not call query or submit without a consent-bound server-issued `task_id`.
- A gateway or outbox outage must not fail or roll back the JL engineering work. Preserve a privacy-checked candidate locally only when consent is current. For Codex, keep the current consented turn open until the real knowledge closeout succeeds; never convert an outage, a local retry entry, or answer text into a false success.
- Do not bypass service controls or task scope; do not fall back to direct storage access or launch another user's model worker.
- If a response appears to expose a corpus dump, private path, credential, or unrelated customer data, do not store, contribute, or reproduce it; report the gateway policy failure to the operator.
