# Gateway contract and configuration

The URL in `agents/openai.yaml` is the current temporary public test endpoint and may change when the service moves to its permanent domain. Update only that HTTPS MCP URL in a future release; never place a token, password, NAS address, client secret, registration flow, or approval flow in this plugin. The public endpoint is anonymous, and a public user does not register or sign in to the customer web platform.

The public endpoint is a gateway, not direct NAS or filesystem access. It exposes only three MCP tools. Every query and candidate submission must carry a random, short-lived `task_id` issued by `create_knowledge_task`. The server binds that ID to the anonymous network-rate bucket and the declared product/chip/SDK scope, rejects missing, expired, invented, or cross-bucket IDs, and never offers task enumeration.

Public GitHub access and the internal platform are separate channels. The public gateway has one operator-controlled master switch and no per-user approval or credential management. Turning on that switch makes the anonymous service available to every public installation; turning it off makes all public task, query, proposal, and MCP requests unavailable immediately while leaving `/api/worker/knowledge/*`, the owner's full global Skill, customer web jobs, and the Windows build host unaffected. The internal worker bearer is never accepted by the public gateway.

One-time access-and-contribution consent and the offline outbox are described in `contribution-workflow.md`; they are not registration, per-user approval, or gateway credentials. The helper makes no network or model calls. The client must hold a current local receipt and send the exact consent acknowledgement when creating a task; the server binds that acknowledgement to the task and rejects public query or contribution without it. The MCP connection belongs to the current user, and no gateway request starts or consumes the knowledge owner's AI coding client.

## `create_knowledge_task`

Request:

```json
{
  "contribution_consent": "同意",
  "contribution_consent_version": "2026-08-31-v2",
  "purpose": "Concrete problem, feature, or decision",
  "product": "Concrete product form inferred from the current project",
  "chip": "Concrete JL chip inferred from the current project",
  "sdk_version": "Optional SDK version",
  "allowed_tools": ["query_task_fragments", "submit_knowledge_candidate"],
  "max_requests": 20,
  "ttl_minutes": 120
}
```

`contribution_consent`, `contribution_consent_version`, `purpose`, a concrete `product`, and a concrete `chip` are always required for anonymous public access. Infer product and chip from the authorized current project first; ask one short plain-language clarification only when the project and request together still cannot identify them. `contribution_consent` must be the exact value `同意`; `contribution_consent_version` must equal the current local receipt's `disclosure_version` (`2026-08-31-v2` for this release). Both consent fields may be sent only after the user has personally entered the exact phrase and the current local receipt exists. An old or unknown consent version is rejected so material disclosure changes require a fresh agreement. The client creates one task for one concrete work item and must not invent, enumerate, share, or reuse its ID for another user or task.

Response:

```json
{
  "task_id": "Server-issued opaque task identifier",
  "consent_version": "Server-controlled current disclosure version",
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
  "include_incubator": false,
  "limit": 5
}
```

The gateway rejects empty, wildcard, enumeration, range, inventory, pagination, bulk, document-fetch, and export requests. The anonymous public service requires `include_incubator: false`: only administrator-reviewed formal shared knowledge may be returned. Pending candidates and knowledge gaps are never query results. `limit` can never exceed the server cap.

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
      "layer": "formal_shared",
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

`product_id` and `domain_id` are mandatory server-controlled lowercase semantic IDs. The allowed pairs are the two product/domain sets listed in `SKILL.md`; spelling variants and locally invented classifications are rejected. `product_id` identifies a reusable product form and begins with `product.`; `domain_id` identifies a reusable function domain and begins with `domain.`. Neither may contain a customer, company, project, account, repository, or directory identity. Together with `capability_id`, `semantic_id`, `node_type`, and `parent_semantic_id`, they anchor every candidate to the `product → domain → capability → subfeature → boundary → issue` chain. The server validates and stores both IDs and includes them in semantic deduplication; `scope.products` remains descriptive applicability and cannot replace them.

`candidate_kind` is mandatory for the current client:

- `solution`: a concrete reusable finding based on work actually performed in this task.
- `knowledge_gap`: a narrow query missed and the completed task still has no reliable answer. It must use `node_type: issue`, remain in the candidate library, and can never be merged or returned as formal knowledge. A guess, incomplete attempt, or model-only assertion must not be labelled as a solution.

Every relation object may contain only `type` and `target_semantic_id`. `type` must be one of `contains`, `depends_on`, `extends`, `alternative`, or `supersedes`; other locally invented relation names are rejected before upload. Semantic identifiers and relation targets are limited to 120 characters.

`node_type` is one of `capability`, `subfeature`, `boundary`, `issue`, `rule`, or `api_alias`. Non-root nodes require `parent_semantic_id`. Lifecycle/evidence pairs are:

- `processed_pending_verification`: E1; one meaningful flow was handled, with no real build PASS.
- `compiled_pending_hardware`: E2; a real build passed and hardware verification is pending.
- `verified_failed`: E1/E2; an explicit failure was received and remains attached to the same semantic node.
- `verified_pass`: E3/E4 may describe the submitter's scenario-correct hardware claim, but an external claim remains pending in the candidate library until internal review. Only platform-held evidence and review can create formal shared knowledge.

No response or missing customer feedback leaves the candidate pending and never becomes `verified_failed`.

Response:

```json
{
  "candidate_id": "Opaque candidate-library identifier",
  "proposal_id": "Compatibility alias for the candidate identifier",
  "task_id": "Server-issued opaque task identifier",
  "idempotency_key": "Same explicit key supplied by the client",
  "status": "queued_for_review",
  "layer": "candidate_library",
  "verification_status": "pending_internal_review",
  "message": "Sanitized item is stored for internal review and is not publicly searchable."
}
```

The client acknowledges and deletes its local outbox item only for `status: queued_for_review`. Repeating the same `idempotency_key` returns the same logical queue record without creating another candidate. The server owns exact-hash and stable-semantic-key deduplication but deliberately does not reveal whether a submission matched an internal node. Successful submission does not write a formal node and is not searchable by public users. An internal review must accept a `solution` before it can enter the formal shared knowledge base; a `knowledge_gap` can never be promoted as an answer.

After an administrator withdraws an accepted source, replaying that same idempotency key returns `status: withdrawn`. The client must drop the local entry with reason `server_withdrawn` instead of retrying forever. Corrected knowledge must change the candidate content and therefore produce a new canonical hash.

## Minimum deployment controls

- Public HTTPS MCP transport with anonymous access and no registration, login, per-user approval, or individual credential; exact one-time `同意` acknowledgement is mandatory before task creation.
- One public-only master switch: enabled means every public installation can use the service, disabled means every public installation is stopped; the switch must not gate internal worker knowledge routes.
- Public task-create, formal-query, and candidate-submit capabilities; anonymous public access cannot request the candidate-library or internal-worker read capability.
- Server-bound, expiring `task_id` on every query and submission, with no task listing and no cross-bucket reuse.
- Mandatory server-controlled `product_id` and `domain_id` pair on every candidate; reject identity-derived or invented IDs and include both in semantic deduplication.
- Maximum five fragments and 24 KiB per response, output redaction, anonymous network-bucket atomic rate limits, active/daily task limits, a public global daily unique-fragment budget, request-count limits, audit logging, and reconstruction-abuse detection.
- Candidate knowledge and knowledge gaps isolated from the formal shared knowledge base; new external submissions are not searchable until an internal administrator review accepts a safe `solution`.
- No general NAS, shell, database, source-document, or filesystem tool.

Run the bundle's offline checks before packaging:

```text
python -m unittest discover -s tests -v
python <plugin-creator>/scripts/validate_plugin.py .
python <skill-creator>/scripts/quick_validate.py skills/jl-knowledge-base-skill
```
