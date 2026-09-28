## Context

See proposal.md for the full history: issue #19 measured the connection-setup cost (decision 6 in
`openspec/specs/csw-harvesting/design.md`), PR #347 then implemented and measured a thread-local pooled-session shim (17
→ 1 connections, ~17% faster on a 151-record benchmark endpoint), and review questioned whether that generalizes to what
this project actually harvests. This decision records the answer to that question and the outcome.

## Goals / Non-Goals

**Goals:**

- Record why connection pooling for CSW was evaluated, prototyped, and not adopted, so it is not re-investigated from
  scratch, and so it can be picked back up cheaply if the premise changes.

**Non-Goals:**

- Changing any CSW harvesting behaviour. This decision has no code impact.

## Decisions

7. **Connection pooling for CSW (issue #19, PR #347) is not adopted — production CSW volume does not justify it today.**
   The 17 → 1 connections / ~17% measurement is real, but it was taken against `atlas.thuenen.de` (151 records), a
   one-off external benchmark endpoint used to investigate the issue — not a deployed repository. The only
   currently-working production CSW source, `bonares` (`dev_environment/config.all-rdis.yaml`), returns ~27 records. At
   a page cap similar to the one measured on `atlas.thuenen.de` (`MaxRecordDefault = 10`, decision 6), that is ~3 pages
   — about 4 connections today, not 17 — so pooling them into 1 saves on the order of 0.2-0.3 seconds, once, on a daily
   cron harvest (`0 2 * * *`, `concurrencyPolicy: Forbid`, so no concurrent runs compound the cost).
   `csw_thread_pool_size`'s own design rationale (`openspec/specs/csw-threadpool/design.md` decision 4) assumes "`<10`
   concurrent CSW repositories" as the expected scale, consistent with CSW being a low-volume path in this project
   today. A sub-second, once-daily saving does not justify a process-wide monkeypatch of `owslib.util.requests`
   (thread-local session factory, per-executor registry, request-shim class) — the kind of speculative infrastructure
   `openspec/principles.md` argues against building ahead of need.

   _Revisit if:_ a CSW repository with a materially larger record count (the issue's own illustrative case: a
   100k-record endpoint capped at a small page size) is ever onboarded, at which point the handshake count — and the
   case for pooling — scales with page count, not with this decision's current assumptions. PR #347's implementation
   (`middleware/inspire/http_pooling.py` on branch `feat/pool-csw-http-sessions-19`) and its measurement remain
   available as a starting point; the review on that PR (2026-09-28) also found three gaps worth fixing if it is
   revived: `connect()` and the paged `GetRecords` fetch run as separate executor jobs and can land on different worker
   threads when `csw_thread_pool_size > 1` (so even that implementation only pools within one paging sequence, not the
   whole harvest); `close_pooled` does not clear the thread-local after closing a session; and the synchronous
   `connect()` / `get_records()` paths bypass registration entirely, so their sessions are never closed.

## Risks / Trade-offs

- **Stale if scale changes silently.** Nothing enforces revisiting this decision when a large-volume CSW repository is
  added — it depends on whoever configures the new repository noticing the record count and page cap. Mitigated by this
  decision naming the exact revisit condition and pointing at the existing implementation, so the next investigation
  starts from measured numbers instead of zero.

## Migration Plan

None — no code or config changes.
