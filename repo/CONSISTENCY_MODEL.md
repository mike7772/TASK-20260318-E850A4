# Consistency Model

## Strong Consistency (immediate)

- Workflow transitions, finance updates, file uploads, and their audit writes are committed in one Unit-of-Work transaction.
- Idempotent critical write requests return deterministic responses within the TTL window.
- Concurrency conflicts are rejected explicitly (HTTP 409) instead of allowing partial state.

## Eventual Consistency (scheduled convergence)

- Metrics snapshots are computed and backfilled by scheduled jobs.
- Maintenance and garbage collection jobs reconcile filesystem and storage metadata over time.
- Idempotency cleanup removes expired replay records on a schedule.

## Best-Effort Recovery

- Startup filesystem recovery scan attempts to clean orphan/temp files.
- Recovery scan is non-fatal to startup; failures are logged for follow-up.

## Enforcement Boundaries

- All critical business writes use Unit-of-Work transaction boundaries.
- Cross-instance background jobs are protected by distributed DB locks.
- Observability and background cleanup do not weaken transactional guarantees of critical paths.
