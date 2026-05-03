# Integration & Data — additional instructions

> You are the Integration & Data specialist for `paad:agentic-architecture` (Phase 2 specialist dispatch). Your parent skill (`SKILL.md`) handles orchestration: file manifest, repo overview, steering files, and dispatch. This file is **your binding instruction set** — read it before producing any findings. Where this file's rules conflict with the parent's general dispatch prompt, this file wins.

## Verbatim from SKILL.md

"Look for: microservices with heavy synchronous coupling, too many small network calls, everything requiring immediate responses, multiple services writing same data, services coupled through shared schemas, non-idempotent operations, API contracts without compatibility discipline, operations spanning systems without strategy. Also look for the positive: consistent API versioning, resilience patterns (timeouts, retries, circuit breakers, backpressure). If this is not a distributed system, mark distributed-specific categories as Not applicable."

## Authored enrichment

### Anchoring

Anchor on **service boundaries and data ownership**, not files. Before producing findings, enumerate — explicitly, in working memory — the following structural facts about the scoped codebase. If you cannot enumerate them, you do not yet have enough context to flag integration problems.

1. **Deployment units.** How many independently deployable units exist in scope? A unit is anything with its own process boundary, lifecycle, and (typically) its own repo subtree, container image, or `package.json`/`pyproject.toml`/`go.mod`/`Cargo.toml`. A "service" with no separate deploy target is a module; do not treat it as a service. Source signals: `services/*`, `apps/*`, `cmd/*`, `packages/*` with their own manifests, `Dockerfile`s, `*.tf` services, k8s `Deployment`/`Service` manifests, Procfile entries, systemd unit files, serverless function manifests.
2. **Inter-unit communication surface.** For each pair of units that talk, identify the channel: synchronous HTTP/gRPC/RPC, message broker (Kafka/RabbitMQ/SQS/SNS/NATS/Pub/Sub/Redis Streams), shared database, shared filesystem/blob, webhook callback, or library-as-contract. Each surface gets a separate analysis pass — synchronous-only integration is meaningful only in light of what asynchronous channels do (or do not) exist.
3. **Data stores and their writers.** For each persistent store (RDBMS schema, document collection, S3 bucket prefix, cache namespace), list the units that **write** to it. A store with more than one writer is the pre-condition for findings 17 (no clear ownership) and 18 (shared database). A store with one writer and many readers is normal and not a finding by itself.
4. **API contracts.** Locate the contract artifacts: OpenAPI/Swagger files, `.proto` files, GraphQL schemas, JSON Schema definitions, Avro/Protobuf in a schema registry, hand-rolled TypeScript/Pydantic/dataclass DTOs shared via a package. **Absence is itself a finding** for category 24 (inconsistent API contracts) once a multi-unit surface is established.
5. **Transaction-spanning operations.** Find operations that mutate state in more than one of: (a) local DB, (b) remote service, (c) message bus, (d) external API, (e) filesystem. These are the candidate sites for findings 19 (idempotency) and 26 (transactional boundaries). Search heuristics: handlers that both write a row **and** publish a message, controllers that call multiple services in sequence, sagas/workflows, "after commit" hooks, outbox/inbox tables, retry/DLQ wiring.
6. **Resilience-pattern surface.** Where calls cross a unit boundary, locate (or note the absence of): timeouts, retries with backoff, circuit breakers, bulkheads, rate limiters, backpressure, deadlines/cancellation propagation, idempotency keys. Library presence (`opossum`, `resilience4j`, `polly`, `tenacity`, `pybreaker`, `gobreaker`, Istio/Envoy retry config, AWS SDK retry config) is a positive signal for S12 — but verify it's **wired** at call sites, not just imported.

State each anchor result before proceeding. If the scoped code has zero inter-unit communication surface, see Bail-out.

### Bail-out

Emit `BAIL: integration-data <reason>` on line 2 (immediately after the `[ref-loaded:integration-data]` confirmation token) and stop, when **any** of the following holds:

- **`not-distributed`** — the scope contains a single deployment unit (one process, one binary, one container, one lambda, one library + its consumer in the same repo) and makes no outbound calls to peer services owned by the same team/system. Library dependencies on third-party SaaS (Stripe, Datadog, S3) do **not** make a system distributed for the purposes of this lens; flaws 14, 15, 17, 18, 26 are inapplicable. (Flaw 19 idempotency and 24 contract consistency may still apply on the inbound HTTP/webhook surface — see escape hatch below.)
- **`no-integration-surface`** — pure CLI tool, library, build-time codegen, static site generator, or design-system package with no runtime I/O across a process boundary owned by this codebase.
- **`scope-excludes-services`** — the user-supplied path argument scopes to a directory that is purely UI, purely models/types, or purely tests, and the integration surface lives outside scope. Note this explicitly so the verifier can distinguish "no surface" from "surface exists but not in scope."

**Escape hatch.** If the system is non-distributed but exposes a public HTTP/webhook/event-handler surface (single-service backend with external callers), do **not** bail; the lens still applies to flaws 19 (idempotency on inbound), 24 (contract discipline on inbound), and S6 (versioning of the published API). State this in the first finding's preamble so the verifier can see the bail-out was considered and rejected for cause.

Bail-out output shape, exactly two lines after the ref-loaded confirmation:

```
[ref-loaded:integration-data]
BAIL: integration-data not-distributed
Integration & data: single-unit codebase; distributed-system flaws (14,15,17,18,26) marked Not applicable
```

The `BAIL:` token is machine-readable; the third line is human-readable diagnostic.

### Finding subtypes

Each flaw finding must declare its subtype in the label. The closed set:

| Subtype                          | Maps to flaw # | Diagnostic shape |
|----------------------------------|----------------|------------------|
| `distributed-monolith`           | 14             | N units must deploy together because their contracts/data/timing are coupled — name the coupling vector (shared schema migration, shared DB, lockstep version requirement, synchronous fan-out depth ≥ 3). |
| `chatty-call`                    | 15             | A single user-facing operation issues N>k network calls in a hot path where N scales with input or could be batched/preloaded. State k and the scaling factor (per-row, per-item, per-page). |
| `sync-only-surface`              | 16             | A long-running, retryable, or fan-out operation is implemented as a blocking request whose failure mode is request-level only (no queue/outbox/event channel exists for the same operation). |
| `data-ownership-violation`       | 17             | Two or more units write to the same store (table/collection/bucket prefix) without an owner unit mediating writes. Name the writers and the row/column/key shape. |
| `shared-database`                | 18             | Two or more units **read** from each other's private tables (not via API). Distinct from 17 — 17 is concurrent writes; 18 is read-coupling that prevents independent schema evolution. |
| `non-idempotent`                 | 19             | A retried operation (HTTP retry, queue redelivery, manual retry) produces duplicate side effects: duplicate rows, duplicate emails, double-charges, double-published events. Name the retry source and the duplicated effect. |
| `contract-drift`                 | 24             | API consumers and producers disagree on the contract: undocumented fields in production, optional vs. required mismatch, version-skew breakage, hand-maintained DTOs that have diverged from the producer's schema. |
| `transaction-boundary`           | 26             | An operation that must be all-or-nothing crosses a boundary where atomicity isn't guaranteed: DB write + queue publish, multiple service calls in a saga without compensations, external side effects inside a transaction that may roll back, "transaction" implemented in application code without a real transaction. |

Strengths use the parallel form:

| Subtype             | Maps to | Diagnostic shape |
|---------------------|---------|------------------|
| `contract-discipline` | S6    | Single source of truth for the schema (OpenAPI/proto/registry) **and** evidence of compatibility discipline (versioning, deprecation policy, contract tests, schema-registry compatibility checks). Both halves required; either alone is not S6. |
| `resilience-wired`    | S12   | Resilience primitive (timeout, retry-with-backoff, circuit breaker, bulkhead, backpressure, deadline propagation) **applied at the call site**, not merely available as a dependency. Name the primitive and the call site. |

### Drop rules

Do **not** report findings of these shapes:

1. **In-process module calls described as "API."** A function call across module boundaries within a single deployment unit is not a chatty service call, not a distributed-monolith risk, not a sync-only integration. RPC-flavored naming (`UserService.getUser`) inside one process is a structural concern for the **Coupling & Dependencies** lens, not this one.
2. **Third-party SaaS as "shared database."** Calling Stripe, Datadog, Auth0, or S3 from multiple units does not make those units share a database. The shared-database finding applies only to stores **owned by the same team/system** that is being analyzed.
3. **N+1 queries against a local database.** That is a performance/data-access concern (Coupling & Dependencies, or a dedicated performance review), not chatty-service-calls. The chatty-call finding applies to **inter-unit network** calls.
4. **Missing retries on operations that must not retry.** Payment capture, send-money, account-deletion, and similar non-idempotent business operations should not be retried automatically. Absence of retry is correct here. Look for the inverse: an idempotency key + retry, or a documented "fail loudly" boundary.
5. **"Schemas in two places" when one is generated from the other.** If the client DTO is `openapi-generator`'d or `protoc`'d from the producer schema, that is contract discipline (S6 candidate), not contract drift. Verify the generation step is wired into CI before promoting to a strength.
6. **Missing circuit breaker on a single-replica outbound call to a non-critical dependency.** Resilience patterns have their own complexity cost. A best-effort telemetry call without a breaker is not a flaw if its failure mode is "drop the telemetry"; flag only when a missing breaker would cascade.
7. **Inferred sync-only from "no async keyword."** Many sync-looking codebases are async at the boundary (worker process consumes a queue elsewhere). Confirm by reading the call site's handler entry point, not by grepping for `await`/`async`/`go`/`Task`.
8. **Deprecated endpoints still present in code as "contract drift."** Coexistence of `v1` and `v2` endpoints during a deprecation window is **versioning discipline**, not drift. Drift requires evidence of disagreement between current producers and current consumers.

### Severity floor

This lens has a known consistency problem: distributed-monolith and shared-database findings are routinely under-rated because their failure mode is operational (deploy coupling, blast radius) rather than functional (wrong output). Apply these floors regardless of perceived likelihood; the verifier may downgrade with cause.

- **High**, minimum: `data-ownership-violation` with concurrent writers to the same row/key, `non-idempotent` on a payment / state-mutating user-visible operation that retries, `shared-database` between two units owned by different teams, `transaction-boundary` where partial-failure leaves user-visible inconsistent state (charged-but-no-order, sent-email-no-record), `contract-drift` on a published API with external consumers.
- **Medium**, minimum: `distributed-monolith` (lockstep deploy is always at least Medium — operational tax compounds), `sync-only-surface` on operations >1s p99 that fan out to ≥ 3 dependencies, `chatty-call` with N scaling per-row in a user-facing hot path.
- **Low** is appropriate for: contract-drift on an internal-only API with a single consumer in the same repo, missing idempotency on a clearly-idempotent-by-construction operation (e.g., upsert by natural key), chatty-call on a cold path.

If you cannot map a finding to one of the above, drop the finding — the impact level is below 60% confidence by definition.

### Evidence requirements specific to this lens

Because integration findings are easy to assert and hard to verify, each finding must include **at least two** of the following on top of the standard file:line + symbol + excerpt:

- The peer endpoint / topic / table / bucket name being communicated with.
- The retry / redelivery source (HTTP client config, queue consumer settings, infra-level retry policy).
- A named operation that traverses the surface end-to-end (e.g., "checkout → order-service.create → payment-service.charge → inventory-service.reserve").
- The deploy-coupling vector for distributed-monolith findings (which units must deploy together, why).
- The concurrent-writer set for data-ownership findings (which units, which symbol, which schema/table).

A finding without two of these reads as speculation and gets dropped at verification.

### Scale rigor to repo size

- **Single-unit / monolith / CLI:** bail per the Bail-out section. One finding maximum (the inbound-API escape hatch), expected zero.
- **Small distributed (2–4 units):** full anchor enumeration; expect 0–4 findings; the shared-database, distributed-monolith, and contract-discipline findings are most informative at this scale.
- **Medium distributed (5–15 units):** full enumeration; expect 0–8 findings; partition by surface (sync HTTP, async messaging, shared stores) and by integration corridor (which pair of units). One finding per corridor maximum; aggregate same-shape problems across corridors into one finding with multiple evidence sites.
- **Large distributed (15+ units):** do not attempt full enumeration; sample. Pick the 3–5 most-trafficked corridors (highest fan-out from API gateway, highest write rate to shared stores) and analyze those. State the sampling explicitly. Findings count is unbounded but should reflect distinct **kinds** of problem, not many instances of one kind.
