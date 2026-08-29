---
name: jl-knowledge-base-skill
description: Query a configured private JL SDK knowledge gateway for a few task-scoped, evidence-labelled fragments and, after one-time consent, automatically contribute sanitized structured experience from substantive Jieli SDK implementation, diagnosis, build, or verification work. Never use it to browse, export, or reconstruct the corpus.
---

# JL Knowledge Base Skill

Use the private gateway as supporting evidence for a concrete JL SDK task. The public Codex, Gemini CLI, and ZCode package contains no private knowledge, endpoint credentials, customer data, or writable access to the verified corpus.

## One-time contribution consent

Before the first automatic contribution, run the bundled outbox helper's `status` command. If current consent is absent, disclose once that substantive JL work will automatically contribute only a small structured, sanitized candidate to the organization's private incubator; it will not upload source, raw logs, identities, paths, KEY material, credentials, or private gateway fragments. Ask for an explicit yes once, then run `grant` with the exact acceptance phrase documented in [references/contribution-workflow.md](references/contribution-workflow.md).

An organization may grant the same disclosure through a managed installation or company policy. Never infer consent merely from installing, downloading, invoking, or querying with this plugin. After current consent exists, do not interrupt later tasks for per-task confirmation. Honor revocation immediately; revocation also deletes the unsent local outbox.

## Query task-scoped knowledge

1. Inspect the current project evidence first. Query only when JL-specific prior knowledge would change a real implementation or verification decision.
2. Infer product, chip, SDK version, board, and requested behavior from the current authorized project before asking the user to repeat them. If neither project evidence nor the user's message provides enough scope, ask one short plain-language clarification. Then call `create_knowledge_task` with one narrow, sanitized task description. Keep its returned `task_id` only for this task; never invent an ID, reuse it for another task or customer, or persist it as knowledge. Treat the returned `candidate_taxonomy` as the only valid product/domain classification for later contributions.
3. Call `query_task_fragments` with that server-issued `task_id`, `include_incubator: true`, the decision to make, observed behavior, and already-known evidence. Remove credentials, customer identity, private paths, complete source files, and unrelated logs. Treat E1/E2 incubator fragments only as labelled leads that still require the current project and build to confirm them.
4. Request only the few fragments needed for that decision. Never send an empty or wildcard query; request an inventory, identifier range, pagination cursor, corpus statistics, bulk result, source document, or export; or chain queries to reconstruct the corpus.
5. Use a follow-up query only for a named unresolved decision and the same `task_id`. Stop when the task has enough evidence.
6. Preserve the evidence label and applicability of every fragment used. Cite it as `[K:<fragment-id>][E1|E2|E3][scope:<applicability>]` and state caveats. Project source, a real build, and scenario-correct hardware results take precedence over a conflicting fragment.

Evidence labels mean:

- `E1`: implemented, inspected, or reproduced, but not proven by a real build.
- `E2`: passed a real build for the stated scope.
- `E3`: passed scenario-correct hardware verification for the stated scope.

Do not present a fragment outside its platform, SDK, board, or product scope as a universal rule. Do not persist returned fragments after the task or republish them as a local knowledge bundle.

## Automatically contribute substantive work

When current consent exists, contribution is automatic after every substantive JL task. A task is substantive when it changes or integrates JL source/configuration, produces a reusable diagnosis or fix, completes a real build, or records an explicit hardware result. Do not contribute ordinary questions, browsing, formatting, abandoned attempts with no finding, or a duplicate narration of private gateway fragments.

Contribution is outbox-first and best effort:

1. At task start, opportunistically process up to three due outbox entries. Use the anonymous public MCP connection only while the operator's global service switch is enabled; never run or contact the knowledge owner's AI coding client.
2. Finish the user's actual engineering work first. Derive the smallest reusable `product -> domain -> capability -> subfeature -> boundary -> issue` chain from evidence created in this task, not from private fragments returned by the gateway.
3. Create one or more stable-semantic candidates when independent subfunctions deserve separate reuse. Keep every field short and structured. Strip source text, raw logs, customer/company names, email addresses, IPv4/IPv6 addresses, MAC addresses, hostnames, URLs, local or NAS paths, file archives, KEY material, credentials, tokens, private protocol payloads, and any returned private fragment text.
4. Enqueue each candidate with the outbox helper before attempting the network call. Its canonical SHA-256 is the stable `idempotency_key`; the queue contains no `task_id`, endpoint, credential, source, or raw log.
5. Call `submit_knowledge_candidate` with a server-issued `task_id`, the candidate, and that `idempotency_key`. A queued item whose old task expired gets a new narrow task; never persist or reuse the old task ID.
6. Delete the local item only when the server returns `status: accepted_to_incubator`. This means the sanitized candidate is immediately searchable in the unverified incubator; it does not mean the claim is verified or part of the approved corpus.
7. On offline, timeout, operator stop, or rate-limit failure, schedule the local item for bounded exponential retry and leave the engineering result successful. On privacy/schema/scope rejection, remove the unsafe item rather than retrying it unchanged. If the server returns `status: withdrawn` for a previously withdrawn identical hash, drop it as `server_withdrawn`; do not retry the same rejected knowledge forever. A genuinely corrected implementation must produce a changed candidate and a new idempotency hash.

Lifecycle and evidence must match what actually happened:

- A meaningful performed flow without real build PASS is `processed_pending_verification` / `E1`.
- Real build PASS is `compiled_pending_hardware` / `E2`.
- Explicit negative build or hardware evidence is `verified_failed` / `E1` or `E2`; silence is not failure.
- Scenario-correct hardware PASS may be submitted as `verified_pass` / `E3`, but the server downgrades an external claim to unverified `E1` in the incubator; never describe it as server-verified.

Every candidate must carry a server-controlled canonical `product_id` and `domain_id` before `capability_id`, `semantic_id`, and `parent_semantic_id`. The initial taxonomy is:

- `product.tws-earbuds`: `domain.input-output`, `domain.power-charging`, `domain.audio-acoustic`, `domain.bluetooth-tws`, `domain.app-integration`, or `domain.production-delivery`.
- `product.headset`: `domain.input-output`, `domain.power-charging`, `domain.audio-acoustic`, `domain.bluetooth`, `domain.app-integration`, or `domain.production-delivery`.

Do not invent spelling variants such as a singular product name or a generic `domain.audio`. A new product or domain must be added to the server taxonomy first. These IDs describe reusable product form and function domain, never a customer, company, project, account, or local directory. The complete classification is `product_id -> domain_id -> capability_id -> semantic_id`, while `node_type` and `parent_semantic_id` extend the chain through subfeature, boundary, and issue nodes. Add a new subfunction or extension to an existing feature chain instead of duplicating the whole feature. The server owns cross-user deduplication and verified promotion.

Read [references/contribution-workflow.md](references/contribution-workflow.md) for the helper commands and retry handshake. Read [references/gateway-contract.md](references/gateway-contract.md) for MCP payloads and server controls.

## Anonymous public and internal-token boundary

The current user's already-running Codex, Gemini CLI, or ZCode session may summarize its own task into a candidate. The outbox helper performs only local JSON validation/storage, and the gateway performs only anonymous rate-limited lookup/deduplication/storage. Neither component starts an AI client, calls a model, has the owner's login, or spends the owner's AI usage. A GitHub or company user therefore uses their own AI account; only workloads deliberately run by the owner's web worker use the owner's configured account.

Public knowledge access requires no registration, login, application, approval, or individual credential. When the operator enables the single GitHub-service switch, every public installation may use the gateway anonymously; when the operator stops it, every public installation must treat the gateway as unavailable and continue with the local engineering shell. Never fall back to an internal worker route, the owner's full global Skill, direct NAS access, or a customer-web-platform account.

## Failure boundaries

- If task creation fails, the operator has stopped public access, or the MCP dependency is unavailable or still uses the non-routable placeholder, explain that private knowledge was not queried and continue from local project evidence. Do not call query or submit without a server-issued `task_id`.
- A gateway or outbox outage must not block, fail, or roll back the JL engineering task. Preserve a privacy-checked candidate locally only when consent is current, then retry opportunistically on later invocations.
- Do not bypass the public master switch, anonymous rate limits, task limits, or response budgets; do not fall back to direct NAS/file access or launch a remote model worker.
- If a response appears to expose a corpus dump, private path, credential, or unrelated customer data, do not store, contribute, or reproduce it; report the gateway policy failure to the operator.
