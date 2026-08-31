# Automatic contribution workflow

The outbox helper is at `scripts/knowledge_outbox.py` in the public bundle. It requires Python 3.10 or newer and uses only the standard library. In the commands below, `<python>` means the first available `python`, `python3`, or `py -3` command that actually reports Python 3.10+. If no suitable interpreter or helper is available, shared knowledge remains disabled and the client continues local-only SDK work; it must not bypass or invent a consent receipt. The helper never connects to a network, invokes Codex or Gemini CLI, reads a project tree, or discovers files. The caller supplies one already-sanitized candidate JSON object.

The helper stores state in the current operating-system user's application-state directory. `JL_KNOWLEDGE_CLIENT_HOME` may override that location for a managed installation or tests. The directory contains only the current consent receipt, counters, and unsent sanitized candidate envelopes. It contains no endpoint, token, `task_id`, customer identity, source, raw log, KEY, or returned private fragment. Successfully submitted entries are deleted; unsent entries expire after 30 days.

## First shared-knowledge access

Run:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py status
```

If `consent_granted` is false, present the prominent one-time disclosure in `SKILL.md` and stop all shared-knowledge calls. Only after the user personally replies with the exact phrase `同意`, record it with:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py grant --accept 同意
```

Do not translate, auto-fill, infer, or run `grant` merely because the plugin was installed or invoked. Before a current grant exists, do not create, query, or submit a shared-knowledge task. A current grant makes later substantive-task contributions automatic without another prompt.

To withdraw and delete all unsent candidates:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py revoke --confirm REVOKE_AND_DELETE_PENDING_CONTRIBUTIONS
```

## Enqueue before upload

After read-only project inspection or diagnosis, record whether that local work established reusable knowledge. This marker stores no prompt, answer, source, or diagnosis text:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py mark-outcome --reusable
```

or:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py mark-outcome --none
```

Use `--reusable` only when task evidence supports a reusable result; it advances the lifecycle work revision and therefore requires an accepted solution candidate. Use `--none` when inspection produced no reusable local result, so the successful scoped query hit or gap may close the task. Never infer this marker from answer keywords.

Write a candidate containing exactly the gateway candidate fields to a private scratch JSON file, or pass it on standard input. Do not use a command-line JSON argument because process listings and shell history can retain it. Enqueue with:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py enqueue --candidate-file <scratch-json> --sanitization-ack STRUCTURED_ONLY_NO_SOURCE_LOG_IDENTITY_PATH_KEY_OR_CREDENTIAL
```

Delete the scratch file immediately after the helper responds. The helper applies the same checks to scalar text, scope lists, workflow/validation/limitation lists, and relation values. It rejects unknown fields, oversized text, multiline/code/log-shaped text, common identity labels, email addresses, IPv4/IPv6 addresses, MAC addresses, hostnames, public or private URLs, local/remote paths, credential assignments, private-key material, invalid lifecycle/evidence pairs, and malformed feature relations. This is a conservative final check, not permission to feed it raw source or logs. The caller must derive and sanitize the structured candidate before invoking it.

The returned 64-character `id` is the SHA-256 of canonical candidate JSON, including its required `product_id` and `domain_id`. Use exactly that value as the MCP submission `idempotency_key`; duplicate local candidates collapse to the same queue entry.

## Opportunistic background sync

At the start and end of a substantive task, request at most three due entries:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py ready --limit 3
```

For each entry:

1. Obtain a narrow server-issued task if the current JL task has no suitable live `task_id`. Do not save a task ID in the outbox.
2. Call `submit_knowledge_candidate` with `task_id`, `candidate`, `client_version: "0.7.1"`, and `idempotency_key` equal to the outbox entry `id`.
3. Only after `status: queued_for_review`, remove it:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py ack --id <entry-id>
```

4. For an unavailable service, timeout, authentication interruption, or rate limit, retain it with a bounded exponential delay:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py retry --id <entry-id> --reason unavailable
```

Allowed transient reasons are `unavailable`, `rate_limited`, `authentication`, `timeout`, and `other`. Do not store raw server errors. A privacy, schema, or scope rejection is not transient; delete the candidate and, if still useful, derive a fresh sanitized one:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py drop --id <entry-id> --reason privacy_rejected
```

If an identical hash was previously withdrawn by the service, the idempotent response is `status: withdrawn`. Stop retrying that exact knowledge and remove it locally:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py drop --id <entry-id> --reason server_withdrawn
```

Only a genuinely corrected implementation or evidence record should be submitted again; its normalized content will produce a different SHA-256 key.

Synchronization retries are best effort and must never roll back completed local engineering work or run the owner's AI coding client. A stored candidate is not public knowledge and is not a successful closeout: it remains unavailable to queries until the server accepts it into the candidate area of the one shared knowledge base and internal review later accepts it into the formal area.

## Required task closeout

At the end of every substantive JL task with current consent, exactly one state must come from an actual successful MCP result for the current server task. A successful query with one or more formal fragments is **usage recorded**. A successful query with an empty `fragments` list is **server gap**; the server records that scoped miss, so do not submit a duplicate gap just to satisfy the hook. A reusable local finding becomes **solution candidate** only after its sanitized `candidate_kind: solution` is enqueued and the server returns `status: queued_for_review`; this later success replaces the query state. Any project edit, real build, or newly prepared structured finding after that acceptance advances the work revision and requires a fresh solution submission for the latest work. Failed, malformed, withdrawn, cross-task, local-only, or answer-text claims never count. The supported-client lifecycle hook requires a current real closeout rather than trusting answer wording. Every create, query, and submit payload includes `client_version: "0.7.1"`.

## Candidate shape

Use the exact `candidate` object from `gateway-contract.md`. Set `candidate_kind` to `solution` for a concrete reusable finding, or `knowledge_gap` only when a narrow query missed and the completed task still has no reliable answer. A gap records the missing scope for administrators; it is never a solution and can never be served or merged as formal knowledge. `product_id` and `domain_id` are mandatory server-controlled lowercase semantic IDs such as `product.tws-earbuds` and `domain.app-integration`. Use only a product/domain pair listed in `SKILL.md`; do not invent a spelling variant or new classification locally. They must describe a reusable product form and function domain, never a customer, company, project, account, repository, or directory. Relations, when present, contain only `type` and `target_semantic_id`; the allowed types are `contains`, `depends_on`, `extends`, `alternative`, and `supersedes`. Example:

```json
{"type":"depends_on","target_semantic_id":"audio.anc"}
```

Keep the feature chain generic and reusable. A product, chip, SDK version, platform, macro identifier, observable behavior, compact performed step, and evidence boundary are acceptable. Source excerpts, full configuration blocks, raw compiler output, customer/company/project names, email addresses, IP addresses, MAC addresses, hostnames, URLs, absolute or deep relative paths, archives, KEY files or contents, credentials, returned private fragments, and private protocol payloads are not.
