# Surface quality bar — path map (product overlay)

Product-local **path→surface** map for Finder/Fixer triage. Use **this table
first** when a path matches; otherwise fall back to
[`docs/surface-quality-bar.global.md`](surface-quality-bar.global.md). Rules
(how the bar affects step 5 / nits / dismiss) stay in
[`docs/ai_review_policy.md`](ai_review_policy.md).

Do not hand-edit the synced `.global.md`. Sync of `.global.md` must not
overwrite this file.

## Model (this repo)

Quality is driven by **who can hurt whom**, not by “is it under `middleware/`”.

1. **Operator-facing contracts** — anything an operator supplies or the
   Middleware API relies on as the product boundary: harvest config / config
   models, the harvester CLI entrypoint, the plugin `AsyncGenerator` contract
   (`HarvestedArc | HarvesterError | SkippedRecord`), and upload/reporting into
   the Middleware API. Highest bar: bad config or bad yields must fail clearly;
   no silent garbage ARCs; no silent data loss on upload/report.
2. **Source adapters + mapping internals** — code only reached through (1):
   CSW/OWSLib, sitemaps/HTML/Solr/Regal HTTP, parsers, mappers, `NiceHttpClient`,
   plugin pipelines. Must **not undermine** operator/API contracts (errors as
   yields, bounded memory, valid ARC via ARCtrl). Toward third-party endpoints,
   apply **similar care** on realistic paths (retries/backoff, polite HTTP,
   explicit failure). Everything else on this surface: **documented happy path
   only** — exotic edges → dismiss.
3. **Global rows** (scripts, agent plumbing, docs, vendor skills) — unchanged;
   see `.global.md`.

## Path map

| Surface | Typical paths | Bar (what must work) | Default for exotic edge cases |
| ------- | ------------- | -------------------- | ----------------------------- |
| **Operator-facing contracts** | `middleware/harvester/.../main.py`, `orchestrator.py`, `config.py`, `plugin_base.py`, `upload.py`, `reporting.py`, `healthcheck.py`; repository/plugin `Config` models; operator YAML (`config.yaml` / demo configs) and env overrides via ConfigWrapper | **Full boundary:** valid/invalid config; clear errors/exit; plugin contract honored; upload/report outcomes correct; no silent corruption of what the API receives; tests for failure modes operators/API hit | **Fix** when correct and in this PR |
| **Source adapters + mapping internals** | `middleware/inspire/`, `middleware/linked_data/` (clients, datasets, sitemaps, mappers, pipelines); `middleware/harvester/.../nice_http_client.py`; other harvest-domain code not in the row above | **Uphold** operator/API contracts (yield errors, skip semantics, ARC validity). **Third-party care** on CSW/HTTP/Solr/Regal realistic paths. **Otherwise** documented happy path only | **Dismiss** exotic edges that do not threaten operator/API contracts or third-party integrity. Still **fix** when a default harvest path is wrong |

When a file sits under both ideas, pick the **stricter** surface (usually
operator-facing if it shapes config, CLI, plugin yield, or API upload/report).

## Out of scope here

Agent CLI (`scripts/ai/`), synced Devinfra scripts, vendor skills, mapping
narrative docs (`docs/*_mapping.md`), and pure OpenSpec cadence stay on the
**global** rows — do not restate them unless this product needs a different bar
for a path the global table mis-classifies.

First-party non-vendor skills kept local (e.g. `.agents/skills/config-wrapper/`)
follow the **Docs / agent** happy-path bar unless a change touches runtime
contracts above.
