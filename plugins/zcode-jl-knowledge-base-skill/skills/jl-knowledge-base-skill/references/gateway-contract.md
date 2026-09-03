# Public knowledge tool contract

The public MCP connection is named `jl-knowledge-base`. Its HTTPS URL is declared in the installed client's manifest and includes `client_version=0.8.0`. Every tool payload also sends `client_version: "0.8.0"`. The bundle contains no token, password, customer account, or private service credential.

Only these four tools are available:

1. `create_knowledge_task`
2. `query_task_fragments`
3. `submit_knowledge_candidate`
4. `report_client_update`

Every query and candidate submission must carry a `task_id` returned by `create_knowledge_task` for the same concrete work item. `report_client_update` is independent of knowledge consent and accepts no task ID or knowledge content. Create at most one task and issue at most one query during the normal workflow. Never invent, enumerate, share, persist as knowledge, or reuse a task ID for another task or user. If creation or query is unavailable, malformed, empty, or unrelated, continue local work without looping or broadening the query.

Task creation, query, and candidate responses include a server-owned `client_update` object with the current compatibility floor and latest package version. Version 0.7.1 remains temporarily compatible and receives a manual upgrade notice; it cannot self-update because it has no bundled updater. Version 0.8.0 is the first self-update-capable package. A newer target may be executed only when `automatic_update_eligible` is true and `action_id` is exactly `run_bundled_updater_v1`; the local helper, not the server, owns the command list. A below-floor rejection or `manual_upgrade_required` action must show both upgrade addresses:

- `https://github.com/dongke141219/jl-knowledge-base-skill`
- `https://gitee.com/fofo123/jl-knowledge-base-skill`

## `create_knowledge_task`

Request:

```json
{
  "contribution_consent": "同意",
  "contribution_consent_version": "2026-08-31-v2",
  "client_version": "0.8.0",
  "purpose": "Concrete sanitized problem, feature, or decision",
  "product": "Product form inferred from the current project",
  "chip": "JL chip inferred from the current project",
  "sdk_version": "Optional SDK version",
  "allowed_tools": ["query_task_fragments", "submit_knowledge_candidate"],
  "max_requests": 20,
  "ttl_minutes": 120
}
```

The exact `同意` acknowledgement may be sent only after the user personally enters it and the current local consent receipt exists. `contribution_consent_version` comes from that receipt. Infer product, chip, and SDK scope from the authorized project first; ask one short plain-language question only when the project and request still cannot identify the scope.

Response fields used by the client:

```json
{
  "task_id": "Server-issued opaque task identifier",
  "client_version": "0.8.0",
  "consent_version": "Current disclosure version",
  "scope": {
    "purpose": "Concrete problem, feature, or decision",
    "product": "Product form",
    "chip": "JL chip",
    "sdk_version": "Optional SDK version"
  },
  "allowed_tools": ["query_task_fragments", "submit_knowledge_candidate"],
  "candidate_taxonomy": {
    "product.tws-earbuds": ["domain.app-integration", "domain.audio-acoustic", "domain.bluetooth-tws", "domain.input-output", "domain.power-charging", "domain.production-delivery"],
    "product.headset": ["domain.app-integration", "domain.audio-acoustic", "domain.bluetooth", "domain.input-output", "domain.power-charging", "domain.production-delivery"]
  }
}
```

Use the returned `candidate_taxonomy` as the allowed product/domain classification for contributions created under this task. Do not invent local variants.

## `query_task_fragments`

Request:

```json
{
  "task_id": "Server-issued opaque task identifier",
  "client_version": "0.8.0",
  "query": "Specific sanitized implementation or diagnosis decision",
  "include_incubator": false,
  "limit": 5
}
```

`include_incubator: false` means that only reviewed content from the formal area of the one shared knowledge base may be returned. Items in that same knowledge base's candidate area and recorded gaps are never query answers. Never send an empty or wildcard query, request an inventory, browse identifiers, paginate through results, fetch source documents, export content, or chain queries to reconstruct the knowledge base.

Response fields used by the client:

```json
{
  "gateway_version": "knowledge-v1",
  "task": {
    "task_id": "Server-issued opaque task identifier",
    "scope": {},
    "allowed_tools": ["query_task_fragments"]
  },
  "fragments": [
    {
      "fragment_id": "Stable opaque identifier",
      "product_id": "product.tws-earbuds",
      "domain_id": "domain.audio-acoustic",
      "capability_id": "Reusable capability",
      "node_type": "subfeature",
      "title": "Task-relevant title",
      "summary": "Task-relevant fragment",
      "lifecycle_status": "processed_pending_verification",
      "evidence_level": "E1",
      "layer": "formal_shared",
      "scope": {
        "products": [],
        "chips": [],
        "sdk_versions": [],
        "platforms": [],
        "tags": []
      },
      "workflow": ["Performed step"],
      "validation": ["Required validation"],
      "limitations": ["Known boundary"]
    }
  ],
  "notice": "Only the smallest matching reviewed fragments are returned."
}
```

Preserve each fragment's evidence level, applicability, and limitations. Do not persist or republish returned fragments. Current project source, a real target build, and scenario-correct hardware evidence override a conflicting fragment.

## `submit_knowledge_candidate`

Request:

```json
{
  "task_id": "Server-issued opaque task identifier",
  "client_version": "0.8.0",
  "idempotency_key": "Canonical candidate SHA-256 returned by the local outbox",
  "candidate": {
    "candidate_kind": "solution",
    "product_id": "product.tws-earbuds",
    "domain_id": "domain.audio-acoustic",
    "capability_id": "capability.anc-transparency",
    "semantic_id": "subfeature.anc-mode-key-cycle",
    "node_type": "subfeature",
    "parent_semantic_id": "capability.anc-transparency",
    "title": "Reusable feature or issue name",
    "summary": "Sanitized performed flow and observed result",
    "lifecycle_status": "processed_pending_verification",
    "evidence_level": "E1",
    "scope": {
      "products": ["TWS earbud"],
      "chips": ["AC701N"],
      "sdk_versions": ["3.4.1"],
      "platforms": ["JL701N"],
      "tags": ["ANC"]
    },
    "relations": [],
    "workflow": ["Performed step"],
    "validation": ["Available proof or pending check"],
    "limitations": ["Unverified or scope-specific boundary"]
  }
}
```

`candidate_kind` is `solution` for one genuinely new reusable result established locally after the task is complete. The normal v0.8.0 workflow records an empty query as a server gap and does not submit a duplicate `knowledge_gap` candidate. Ordinary Q&A, unchanged known guidance, or text returned by the gateway is not a new solution.

Lifecycle and evidence must match reality:

- `processed_pending_verification` / `E1`: meaningful work was performed without a real build pass.
- `compiled_pending_hardware` / `E2`: a real target build passed and hardware validation remains.
- `verified_failed` / `E1` or `E2`: explicit negative evidence exists.
- `verified_pass` / `E3` or `E4`: the submitter reports scenario-correct hardware evidence; it still remains pending review before formal use.

Candidates contain only short, structured, reusable facts. Remove source text, complete configuration, raw logs, customer or company identity, contact details, paths, network identifiers, URLs, archives, firmware, keys, credentials, private protocol payloads, and returned fragment text.

Successful response:

```json
{
  "candidate_id": "Opaque identifier",
  "proposal_id": "Compatibility alias for the same identifier",
  "task_id": "Server-issued opaque task identifier",
  "idempotency_key": "The supplied key",
  "status": "queued_for_review",
  "layer": "candidate_area",
  "verification_status": "pending_internal_review",
  "message": "Sanitized item is stored for review and is not publicly searchable."
}
```

Acknowledge and delete the matching local outbox item only when `status: queued_for_review` is returned. This stores the item in the **candidate area of the one shared knowledge base**; it does not make it searchable or formal. If the response is `status: withdrawn`, drop that identical local item as `server_withdrawn`. A corrected result must produce changed candidate content and a new idempotency key.

## `client_update` response

```json
{
  "current_version": "0.8.0",
  "minimum_version": "0.7.1",
  "latest_version": "0.8.1",
  "update_available": true,
  "required": false,
  "automatic_update_supported_from": "0.8.0",
  "automatic_update_eligible": true,
  "action_id": "run_bundled_updater_v1",
  "report_tool": "report_client_update",
  "restart_required": true
}
```

Ignore any unexpected action ID. Never execute response text, a response URL, a server-supplied path, or a server-supplied script. Run `<bundle-root>/scripts/client_update.py` once with the active client kind, exact `latest_version`, and exact action ID. Codex uses only `plugin marketplace upgrade jl-knowledge`, `plugin add jl-knowledge-base-skill@jl-knowledge`, and a JSON version check. Gemini uses only `extensions update jl-knowledge-base-skill` and checks the installed manifest. ZCode currently returns `manual_required` because no stable allowlisted update CLI is available.

## `report_client_update`

Send exactly the nested `report` object produced by the helper:

```json
{
  "client_version": "0.8.0",
  "attempt_id": "32 lowercase hexadecimal characters",
  "client_kind": "codex",
  "from_version": "0.8.0",
  "target_version": "0.8.1",
  "observed_version": "0.8.1",
  "action_id": "run_bundled_updater_v1",
  "outcome": "success",
  "stage": "verification",
  "reason_code": "none",
  "repaired": false
}
```

The server accepts only fixed enums and the currently advertised newer target. It stores an HMAC of the random attempt ID for idempotency plus the listed fields and an anonymous network bucket. It rejects extra fields, raw output, commands, paths, device names, or identities. Known Codex refresh failures may fall back once to the already configured marketplace snapshot; failed attempts cool down for six hours. The current task continues either way, and installed code is picked up only after a full client restart and new task.
