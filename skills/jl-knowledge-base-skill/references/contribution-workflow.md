# Automatic contribution workflow

The outbox helper is at `scripts/knowledge_outbox.py` in the public bundle. It requires Python 3.10 or newer and uses only the standard library. In the commands below, `<python>` means the first available `python`, `python3`, or `py -3` command that actually reports Python 3.10+. If no suitable interpreter or helper is available, shared knowledge remains disabled and the client continues local-only SDK work; it must not bypass or invent a consent receipt. The helper never connects to a network, invokes Codex or Gemini CLI, reads a project tree, or discovers files. The caller supplies one already-sanitized candidate JSON object.

The helper stores state in the current operating-system user's application-state directory. `JL_KNOWLEDGE_CLIENT_HOME` may override that location for a managed installation or tests. The directory contains only the current consent receipt, counters, bounded hashes of acknowledged candidates, and unsent sanitized candidate envelopes. It contains no endpoint, token, `task_id`, customer identity, source, raw log, KEY, or returned private fragment. Successfully submitted envelopes are deleted after their hash receipt is retained for local duplicate prevention; unsent entries expire after 30 days.

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

Finish all local inspection, editing, and building first. Then prepare a candidate only when the completed task created a genuinely new reusable local engineering conclusion. Ordinary questions, read-only browsing without a new conclusion, query hits/gaps, and restatements of returned fragments require no marker and no candidate.

Write a candidate containing exactly the gateway candidate fields to a private scratch JSON file, or pass it on standard input. Do not use a command-line JSON argument because process listings and shell history can retain it. Enqueue with:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py enqueue --candidate-file <scratch-json> --sanitization-ack STRUCTURED_ONLY_NO_SOURCE_LOG_IDENTITY_PATH_KEY_OR_CREDENTIAL
```

Delete the scratch file immediately after the helper responds. The helper applies the same checks to scalar text, scope lists, workflow/validation/limitation lists, and relation values. It rejects unknown fields, oversized text, multiline/code/log-shaped text, common identity labels, email addresses, IPv4/IPv6 addresses, MAC addresses, hostnames, public or private URLs, local/remote paths, credential assignments, private-key material, invalid lifecycle/evidence pairs, and malformed feature relations. This is a conservative final check, not permission to feed it raw source or logs. The caller must derive and sanitize the structured candidate before invoking it.

The returned 64-character `id` is the SHA-256 of canonical candidate JSON, including its required `product_id` and `domain_id`. Use exactly that value as the MCP submission `idempotency_key`; duplicate local candidates collapse to the same queue entry. If the helper returns `already_uploaded: true`, the same reusable-result fingerprint was previously acknowledged and must not be submitted again.

## Bounded deferred sync

Do not process old pending entries during ordinary question answering or read-only diagnosis. A later dedicated sync opportunity may request up to three due entries:

```text
<python> <bundle-root>/scripts/knowledge_outbox.py ready --limit 3
```

For each entry:

1. Obtain a narrow server-issued task if the current JL task has no suitable live `task_id`. Do not save a task ID in the outbox.
2. Call `submit_knowledge_candidate` with `task_id`, `candidate`, `client_version: "0.8.0"`, and `idempotency_key` equal to the outbox entry `id`.
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

Synchronization retries are best effort and must never roll back, delay, or reopen completed local engineering work or run the owner's AI coding client. Never retry the same item twice in one user turn. A stored candidate is not public knowledge and remains unavailable to queries until the server accepts it into the candidate area and internal review later accepts it into the formal area.

## Bounded task closeout

At the end of a confirmed JL task, keep one bounded outcome: a successful non-empty query is **usage recorded**; a successful empty query is **server gap**; a failed/malformed/unavailable call is **query unavailable**; no shared access is **local only**; and an accepted new reusable result is **solution candidate**. The candidate may replace the query outcome, but later reads, edits, builds, or answer wording do not create another required closeout. The hook may remind the model once if it omitted the consent check or one query, then it allows local completion. Every create, query, and submit payload includes `client_version: "0.8.0"`.

## Candidate shape

Use the exact `candidate` object from `gateway-contract.md`. This normal task workflow submits only `candidate_kind: solution` for a concrete new reusable local finding. A narrow query miss is already recorded as `server gap`; do not submit a duplicate gap candidate merely to complete the workflow. `product_id` and `domain_id` are mandatory server-controlled lowercase semantic IDs such as `product.tws-earbuds` and `domain.app-integration`. Use only a product/domain pair listed in `SKILL.md`; do not invent a spelling variant or new classification locally. They must describe a reusable product form and function domain, never a customer, company, project, account, repository, or directory. Relations, when present, contain only `type` and `target_semantic_id`; the allowed types are `contains`, `depends_on`, `extends`, `alternative`, and `supersedes`. Example:

```json
{"type":"depends_on","target_semantic_id":"audio.anc"}
```

Keep the feature chain generic and reusable. A product, chip, SDK version, platform, macro identifier, observable behavior, compact performed step, and evidence boundary are acceptable. Source excerpts, full configuration blocks, raw compiler output, customer/company/project names, email addresses, IP addresses, MAC addresses, hostnames, URLs, absolute or deep relative paths, archives, KEY files or contents, credentials, returned private fragments, and private protocol payloads are not.
