## Why

Issue #19 (connection reuse half) asked whether CSW harvesting should pool one `requests.Session` per worker thread
instead of opening a new TCP + TLS connection for every OWSLib call. PR #347 prototyped and implemented option 2 from
that issue: rebind `owslib.util.requests` to a thread-local pooled session, measured against a real endpoint
(`atlas.thuenen.de`, pycsw, 151 records) at 17 → 1 connections, ~17% faster (≈7.1s → ≈5.5-5.7s).

Review on #347 (automated review plus @Zalfsten) questioned whether that win is worth the complexity — CSW batches many
datasets per request, unlike the schema.org path's one-request-per-dataset pattern, so the absolute time at stake was
disputed. Checking this repo's actual configuration confirms the skepticism, and goes further: the only
currently-working production CSW source, `bonares` (`dev_environment/config.all-rdis.yaml`), returns **~27 records**,
not 151. CSW page size is server-capped (as documented in `openspec/specs/csw-harvesting/design.md` decision 6, measured
on `atlas.thuenen.de` at `MaxRecordDefault = 10`), so at a similar cap `bonares` costs roughly 3 pages today — about 4
connections, not 17. Pooling those into 1 saves on the order of **0.2-0.3 seconds**, once, on a `0 2 * * *` daily cron
run (`concurrencyPolicy: Forbid` — no concurrent runs to compound the cost). `csw_thread_pool_size`'s own design
rationale (`openspec/specs/csw-threadpool/design.md` decision 4) assumes "`<10` concurrent CSW repositories" as the
expected scale, consistent with this being a small, low-volume path today.

Issue #19 itself listed this exact outcome as option 4 ("accept and document... defensible — 17% of a 7-second harvest
is not a production pain today") and flagged the one condition under which option 4 loses: a real endpoint with a large
record count under a small page cap (its own example: "a 100k-record endpoint capped at 10/page means 10,000
handshakes"). That is not what this project harvests today. Given that, the process-wide monkeypatch of
`owslib.util.requests` (a new thread-local-session module, a per-executor registry, a shim class) is complexity this
repo's own principles argue against building ahead of need (`openspec/principles.md`: "do not invent harvester-wide
generic frameworks until a second plugin needs the same mechanism").

## What Changes

- No code change. PR #347 is closed without merging; `middleware/inspire/http_pooling.py` and its `csw_client.py` wiring
  never land on `main`.
- Record the decision (option 4) as a new design decision in the `csw-harvesting` capability, alongside the existing
  `MaxRecordDefault` finding (decision 6), so the next person investigating CSW connection overhead finds the
  measurement, the production-scale numbers, and the reasoning without re-deriving them.
- Close issue #19's connection-reuse half, referencing this decision.

## Capabilities

### New Capabilities

- (none — skip_specs: true)

### Modified Capabilities

- (none — decision record only, no requirement or behaviour change)

## Impact

- **Code**: none.
- **Docs**: `openspec/specs/csw-harvesting/design.md` gains one decision recording the pooling evaluation and its
  outcome.
- **Process**: issue #19 (pooling half) closed as won't-fix; PR #347 closed unmerged.
