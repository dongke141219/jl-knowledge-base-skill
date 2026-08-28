# Gateway contract and configuration

The checked-in URL in `agents/openai.yaml` is intentionally non-routable. Before distributing an installable build, replace only that URL with the organization-controlled HTTPS MCP endpoint. The public endpoint is anonymous: never place a token, password, NAS address, client secret, registration flow, or approval flow in this plugin. A GitHub user does not register or sign in to the customer web platform.

The public endpoint is a gateway, not direct NAS or filesystem access. It exposes only three MCP tools. Every query and candidate submission must carry a random, short-lived `task_id` issued by `create_knowledge_task`. The server binds that ID to the anonymous network-rate bucket and the declared product/chip/SDK scope, rejects missing, expired, invented, or cross-bucket IDs, and never offers task enumeration.

Public GitHub access and the internal platform are separate channels. The public gateway has one operator-controlled master switch and no per-user approval or credential management. Turning on that switch makes the anonymous service available to every public installation; turning it off makes all public task, query, proposal, and MCP requests unavailable immediately while leaving `/api/worker/knowledge/*`, the owner's full global Skill, customer web jobs, and the Windows build host unaffected. The internal worker bearer is never accepted by the public gateway.

One-time contribution consent and the offline outbox are local client concerns described in `contribution-workflow.md`; they are not registration, approval, or gateway credentials. The helper makes no network or model calls. The MCP connection belongs to the current user, and no gateway request starts or consumes the knowledge owner's Codex CLI.

## `create_knowledge_task`

Request:

```json
{
  "purpose": "Concrete problem, feature, or decision",
  "product": "Optional product form",
  "chip": "Optional chip",
  "sdk_version": "Optional SDK version",
  "allowed_tools": ["query_task_fragments", "submit_knowledge_candidate"],
  "max_requests": 20,
  "ttl_minutes": 120
}
```

`purpose` and a concrete `chip` are always required for anonymous public access. The client creates one task for one concrete work item and must not invent, enumerate, share, or reuse its ID for another user or task.

Response:

```json
{
  "task_id": "Server-issued opaque task identifier",
  "scope": {
    "purpose": "Concrete problem, feature, or decision",
    "product": "Optional product form",
    "chip": "Optional chip",
    "sdk_version": "Optional SDK version"
  },
  "allowed_tools": ["query_task_fragments", "submit_knowledge_candidate"],
  "remaining_requests": 20,
  "expires_at": "Server-controlled expiry timestamp",
  "candidate_taxonomy": {
    "product.headset": ["domain.app-integration", "domain.audio-acoustic", "domain.bluetooth", "domain.input-output", "domain.power-charging", "domain.production-delivery"],
    "product.tws-earbuds": ["domain.app-integration", "domain.audio-acoustic", "domain.bluetooth-tws", "domain.input-output", "domain.power-charging", "domain.production-delivery"]
  }
}
```

Use the returned `candidate_taxonomy` as the authoritative classification for contributions created under the task. It is a small classification skeleton, not a knowledge-corpus listing. External clients must send one of the returned canonical IDs exactly; historical aliases, spelling variants, and locally invented classifications are rejected so they cannot split the chain.

## `query_task_fragments`

Request:

```json
{
  "task_id": "Server-issued opaque task identifier",
  "query": "Specific sanitized question or decision",
  "include_incubator": true,
  "limit": 5
}
```

The gateway rejects empty, wildcard, enumeration, range, inventory, pagination, bulk, document-fetch, and export requests. The anonymous public service permits `include_incubator: true` so E1/E2 experience can be returned with its evidence label and limitations. `limit` can never exceed the server cap.

Response:

```json
{
  "gateway_version": "knowledge-v1",
  "task": {
    "task_id": "Server-issued opaque task identifier",
    "scope": {},
    "allowed_tools": ["query_task_fragments"],
    "remaining_requests": 19,
    "expires_at": "Server-controlled expiry timestamp"
  },
  "fragments": [
    {
      "fragment_id": "Stable opaque identifier",
      "product_id": "product.tws-earbuds",
      "domain_id": "domain.app-integration",
      "capability_id": "Reusable parent capability",
      "node_type": "subfeature",
      "title": "Task-relevant title",
      "summary": "Task-relevant knowledge fragment",
      "lifecycle_status": "processed_pending_verification",
      "evidence_level": "E1",
      "layer": "incubator",
      "scope": {
        "products": [],
        "chips": [],
        "sdk_versions": [],
        "platforms": [],
        "tags": []
      },
      "parent_chain": [{"node_type": "capability", "title": "Parent"}],
      "relations": [],
      "workflow": ["Performed step"],
      "validation": ["Required validation"],
      "limitations": ["Known boundary"]
    }
  ],
  "notice": "Only the smallest matching task fragments are returned."
}
```

The client must preserve `lifecycle_status`, `evidence_level`, `layer`, scope, and limitations. It must not persist fragments after the task or chain queries to reconstruct the corpus. The server omits source documents, private paths, full semantic keys, identities, and credentials. Do not expose a `list`, `browse`, `get_document`, or `export` tool.

## `submit_knowledge_candidate`

Request:

```json
{
  "task_id": "Server-issued opaque task identifier",
  "idempotency_key": "Canonical candidate SHA-256 returned by the local outbox",
  "candidate": {
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

`product_id` and `domain_id` are mandatory server-controlled lowercase semantic IDs. The allowed pairs are the two product/domain sets listed in `SKILL.md`; spelling variants and locally invented classifications are rejected. `product_id` identifies a reusable product form and begins with `product.`; `domain_id` identifies a reusable function domain and begins with `domain.`. Neither may contain a customer, company, project, account, repository, or directory identity. Together with `capability_id`, `semantic_id`, `node_type`, and `parent_semantic_id`, they anchor every candidate to the `product → domain → capability → subfeature → boundary → issue` chain. The server validates and stores both IDs and includes them in semantic deduplication; `scope.products` remains descriptive applicability and cannot replace them.

`node_type` is one of `capability`, `subfeature`, `boundary`, `issue`, `rule`, or `api_alias`. Non-root nodes require `parent_semantic_id`. Lifecycle/evidence pairs are:

- `processed_pending_verification`: E1; one meaningful flow was handled, with no real build PASS.
- `compiled_pending_hardware`: E2; a real build passed and hardware verification is pending.
- `verified_failed`: E1/E2; an explicit failure was received and remains attached to the same semantic node.
- `verified_pass`: E3/E4 may describe the submitter's scenario-correct hardware claim, but the server downgrades any external E3/E4 submission to unverified E1 in the incubator. Only platform-held evidence and promotion can create verified knowledge.

No response or missing customer feedback leaves the candidate pending and never becomes `verified_failed`.

Response:

```json
{
  "candidate_id": "Opaque incubator candidate identifier",
  "proposal_id": "Compatibility alias for the candidate identifier",
  "task_id": "Server-issued opaque task identifier",
  "idempotency_key": "Same explicit key supplied by the client",
  "status": "accepted_to_incubator",
  "layer": "incubator",
  "verification_status": "unverified",
  "message": "Sanitized candidate is available in the unverified incubator."
}
```

The client acknowledges and deletes its local outbox item only for `status: accepted_to_incubator`. Repeating the same `idempotency_key` returns the same logical acceptance without creating another knowledge node. The server owns exact-hash and stable-semantic-key deduplication but deliberately does not reveal whether a submission matched an internal node. Successful submission is immediately searchable only as unverified incubator knowledge; it never writes or promotes verified knowledge directly. Platform-held evidence and promotion are still required for the verified layer.

After an administrator withdraws an accepted source, replaying that same idempotency key returns `status: withdrawn`. The client must drop the local entry with reason `server_withdrawn` instead of retrying forever. Corrected knowledge must change the candidate content and therefore produce a new canonical hash.

## Minimum deployment controls

- Public HTTPS MCP transport with anonymous access and no registration, login, approval, or individual credential.
- One public-only master switch: enabled means every public installation can use the service, disabled means every public installation is stopped; the switch must not gate internal worker knowledge routes.
- Public task-create, verified-query, and candidate-submit capabilities; anonymous public access cannot request the internal incubator-read capability.
- Server-bound, expiring `task_id` on every query and submission, with no task listing and no cross-bucket reuse.
- Mandatory server-controlled `product_id` and `domain_id` pair on every candidate; reject identity-derived or invented IDs and include both in semantic deduplication.
- Maximum five fragments and 24 KiB per response, output redaction, anonymous network-bucket atomic rate limits, active/daily task limits, a public global daily unique-fragment budget, request-count limits, audit logging, and reconstruction-abuse detection.
- Verified knowledge isolated from the automatically searchable unverified incubator and promoted only with platform-held evidence and administrator policy.
- No general NAS, shell, database, source-document, or filesystem tool.

Run the bundle's offline checks before packaging:

```text
python -m unittest discover -s tests -v
python <plugin-creator>/scripts/validate_plugin.py .
python <skill-creator>/scripts/quick_validate.py skills/jl-knowledge-base-skill
```
