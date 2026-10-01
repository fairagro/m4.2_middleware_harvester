# Design

## Context

See proposal.md — Why. After PR #385, `MycoreSolrSitemap` is a thin adapter over `MycoreSolrProtocol`; discovery
behaviour already lives under generic. Flat `generic` `protocol_type` / `sitemap_url` already warn and lift; the
linked_data mycore path does not. This change lands on top of that shim (rebase onto #385 or merge after it).

## Goals / Non-Goals

**Goals:**

- One clear operator-facing warning when `linked_data.sitemap_type: mycore_solr` is configured
- Specs and example YAML steer toward nested `generic.protocol.mycore_solr`
- Tests lock the warning without changing harvest outcomes

**Non-Goals:**

- Removing `SitemapType.mycore_solr` or the shim (hard-cut follow-up)
- Changing Protocol/Solr pagination behaviour
- Auto-migrating YAML or lifting linked_data configs into generic at runtime
- Deprecating other linked_data sitemap types (`xml`, `regal_find`)

## Decisions

### 1. Warn at repository config validation (not only in the sitemap class)

**Choice:** Emit `logger.warning` from a `RepositoryConfig` (or linked_data `Config`) model validator when
`linked_data.sitemap_type == mycore_solr`, mirroring the existing `payload_type` deprecation pattern in
`harvester.config`.

**Why:** Fires once per config load at startup, before any harvest I/O; matches the established operator signal for
linked_data legacy fields; unit-testable via `caplog` without constructing HTTP clients.

**Alternatives considered:**

- Warn only in `MycoreSolrSitemap.__init__` — also fine, but runs later and couples the signal to plugin construction;
  less consistent with `payload_type`
- `Field(deprecated=True)` on an enum member — Pydantic does not deprecate individual `StrEnum` values cleanly; a
  validator + description text is clearer

### 2. Warning copy points at nested generic + siblings

**Choice:** Use the issue draft (or equivalent):

`linked_data.sitemap_type: mycore_solr is deprecated; use generic.protocol.mycore_solr (with sibling parser/mapper) instead. Support for the linked_data shim will be removed in a future release.`

**Why:** Names the replacement keys operators must set; avoids implying that flat `protocol_type: mycore_solr` is the
migration target.

### 3. Docs / example YAML

**Choice:** In `config_example.yaml`, replace the commented OpenAgrar `linked_data` + `mycore_solr` block with a nested
`generic.protocol.mycore_solr` example (keep robots note). Optionally leave a one-line comment that the linked_data form
still works but is deprecated.

**Why:** Examples are the primary migration nudge alongside the log line.

### 4. Hard-cut follow-up

**Choice:** Open a separate GitHub Task (severity/cost as appropriate) to remove `SitemapType.mycore_solr` registration
and the shim after operators migrate — same shape as #383 for flat generic.

**Why:** Keeps this change cheap and reversible; hard removal needs its own rollout window.

## Risks / Trade-offs

- [Depends on #385] → Rebase/apply only after the thin shim exists; otherwise the warning would deprecate a
  still-canonical linked_data implementation
- [Log noise in multi-repo configs] → One warning per repository entry that still uses the path; acceptable for a
  migration signal
- [Operators ignore warnings] → Follow-up hard cut + example YAML; no auto-migration in this change

## Migration Plan

1. Land after #385 (or on top of it)
2. Deploy: warning-only; no config rewrite required
3. Operators migrate OpenAgrar-style entries to nested generic when convenient
4. Later release: hard-cut issue removes the enum value / shim

## Open Questions

None — warning site and copy are fixed by the decisions above; hard-cut timing stays on the follow-up issue.
