---
type: Reference
title: "Pitfalls catalog"
description: "A planning-time foresight checklist: pitfall categories (data, concurrency, API, auth, errors, performance, testing, frontend, ops, process) to skim so the few that apply land in the feature's pitfalls.md."
timestamp: 2026-06-07
tags: [plan, reference]
---

# Pitfalls catalog

A foresight checklist. During planning, skim these categories and pull the few that genuinely apply to the
current feature into `.wi/features/<slug>/pitfalls.md`, each with the *specific* way it could bite here and the
task that prevents it. The aim is cheap foresight, not a generic risk essay. Skip whole categories that
don't apply.

## Data & persistence
- Irreversible migration run before code is ready; no back-out path.
- Migration that locks a large table / long downtime.
- Nullable vs default mismatch; silent data loss on column change.
- Reads/writes split across old and new schema during deploy.
- Missing index on a new hot query path.

## Concurrency & state
- Race between check and write (TOCTOU); needs a transaction or lock.
- Non-idempotent handler retried by a queue/webhook → duplicates.
- Shared mutable state across requests/threads/async tasks.
- Ordering assumptions that don't hold under parallelism.

## API & compatibility
- Breaking change to a public endpoint/signature with existing callers.
- Response shape change that older clients can't parse.
- Versioning/deprecation path not planned.
- Pagination/limits ignored → unbounded payloads.

## Auth & security
- New endpoint missing authz checks.
- Secrets in code/logs; PII logged.
- Injection (SQL/template/shell) via unvalidated input.
- SSRF/path traversal on user-supplied URLs/paths.
- Permission check on the wrong layer (UI hides it, API doesn't enforce it).

## Errors & resilience
- Failure path untested; exception swallowed.
- External call with no timeout/retry/circuit-breaker.
- Partial failure leaves inconsistent state (no transaction/rollback).
- User-facing error leaks internals.

## Performance
- N+1 query introduced by a convenient ORM access.
- Work done per-item that should be batched.
- Unbounded memory (loading a whole table/file).
- Synchronous call on a hot path that should be async/queued.

## Testing gaps
- New behavior with no failing-test-first; only happy path covered.
- Test asserts implementation detail, not behavior → brittle.
- Flaky test from time/order/network dependence.
- A test weakened/deleted just to go green.

## Frontend (if applicable)
- State not handled: loading, empty, error, no-permission.
- Accessibility regressions (focus, labels, contrast, keyboard).
- Layout breaks at small widths; no responsive check.
- Unkeyed lists / re-render storms; stale cache after mutation.

## Ops & rollout
- No feature flag for a risky change; all-or-nothing deploy.
- Config/env var needed in prod but undocumented.
- Logs/metrics missing for the new path → blind in production.
- Back-out plan absent.

## Process
- Scope creep mid-build (plan and code diverge silently).
- Touching files outside the feature's stated scope.
- Committing generated files, large blobs, or secrets.
