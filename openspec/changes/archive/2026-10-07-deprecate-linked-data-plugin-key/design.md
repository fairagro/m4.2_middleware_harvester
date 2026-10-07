# Design

## Context

See proposal.md — Why. Today `RepositoryConfig` already warns for nested legacy fields (`payload_type`,
`sitemap_type: mycore_solr`) but not for choosing the `linked_data` plugin key itself. In-repo Publisso examples still
use `linked_data` + `regal_jsonld` even though `docs/linked_data_to_generic.md` documents the `generic` +
`parser.type: jsonld` + `allowed_context_url` path.

## Goals / Non-Goals

**Goals:**

- One clear operator signal when any `linked_data:` repository is loaded
- Canonical in-repo examples prefer `generic` for Regal/Publisso
- Spec deltas so archive folds deprecation into main specs

**Non-Goals:**

- Hard-delete of `linked_data` package / orchestrator branch
- Migrating out-of-repo ops overlays
- Changing Regal mapping semantics

## Decisions

1. **Warn on the plugin key in `RepositoryConfig`, not inside LinkedDataPlugin** — Same pattern as
   `_LEGACY_LINKED_DATA_MYCORE_SOLR_MSG` / payload_type: config load is the operator-facing surface; one warning per
   repository entry that sets `linked_data` is enough. Alternative considered: warn only inside the plugin `run()` —
   rejected because operators validating config without harvesting would never see it.

2. **Warn even when a more specific nested warning also fires** — e.g. mycore_solr under linked_data may emit both
   plugin-key and sitemap-type warnings. Prefer explicit signals over suppressing. Alternative: suppress plugin-key
   warning when a nested one fires — rejected as easy to miss the “whole key is deprecated” message.

3. **Publisso YAML flip uses shared `jsonld` parser + `allowed_context_url`** — Matches documented migration; no new
   `regal_jsonld` PayloadParser. Keep `respect_robots_txt: false` under `protocol.http`.

4. **Hard cut stays out of this PR** — Tracked as remaining #296 acceptance / follow-up after operators migrate; related
   #395/#396 stay separate.

## Risks / Trade-offs

- [Dual warnings for mycore_solr] → Acceptable noise; copy should stay short.
- [Publisso flip breaks if remote context pin wrong] → Use documented FRL context IRI; covered by existing jsonld tests
  patterns; smoke via unit config validate if available.
- [Operators ignore warning] → Hard cut later forces migration; changelog note in tasks.

## Migration Plan

1. Ship warning + example YAML flip.
2. Operators migrate out-of-repo configs when they next touch values.
3. Separate PR removes plugin key after dependency shims / remaining RDIs are on `generic`.
