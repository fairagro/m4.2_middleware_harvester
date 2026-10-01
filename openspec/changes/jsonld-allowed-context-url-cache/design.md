# Design

## Context

See `proposal.md` — Why. Today `JsonLdParser` rejects remote `@context` except a hard-coded Schema.org `@vocab` swap;
`HtmlJsonLdParser` validates against `SCHEMAORG_CONTEXT_ALLOWLIST` then calls `graph.parse`, which can still
network-fetch schema.org. Both parsers already receive `NiceHttpClient | None` and `ParserConfig` (threshold only).
Generic always passes a live client; inline `jsonld` historically allowed `client is null` when no remote context is
needed.

## Goals / Non-Goals

**Goals:**

- One optional allowlisted root context URL on `ParserConfig`, shared by `jsonld` and `html_jsonld`.
- Process-lifetime URL→document cache; polite HTTP only on miss; transitive `@import` from the loaded root also cached.
- Fail closed for payload remote IRIs that are not the configured URL; unset means no remote payload contexts.
- Stop rdflib from performing its own uncached context fetches during parse (custom document loader / pre-inline).

**Non-Goals:**

- Vendored Schema.org trees or API package sharing.
- Multi-URL operator allowlists; TTL/ETag; Publisso config migration in this change.
- Changing Regal `linked_data` dataset behaviour (still rdflib-native fetch until operators move to `generic`).

## Decisions

1. **Field name `allowed_context_url` on `ParserConfig`** — Sibling `parser:` block is already the shared place for
   JSON-LD threshold; one optional `http(s)` URL keeps per-RDI control without plugin-specific fields.
   - Alternative considered: list of URLs — rejected (operator asked for exactly one).

2. **Exact string match for the payload remote IRI** — No http/https or trailing-slash normalisation in v1; operators
   set the IRI that actually appears in payloads (e.g. `https://schema.org/` vs `http://schema.org`).
   - Alternative: normalise Schema.org variants — deferred; can layer later without changing the one-URL model.

3. **Remove Schema.org `@vocab` stub and hard-coded parse-time allowlist** — One mechanism only. Existing Schema.org
   RDIs must set `allowed_context_url`. Bioschemas as a second remote string is not supported unless it arrives via
   `@import` from the configured root.
   - Alternative: keep stub + new URL — rejected (two policies).

4. **Shared loader module under `middleware.parsing`** — e.g. cache dict + async `resolve(url, client)` used before /
   during `graph.parse`. Prefer injecting an rdflib/pyld document loader that serves only from cache and triggers
   async-prefetched documents, or rewrite payload `@context` to the inlined cached object after validating the URL
   match. Choose the approach that reliably covers `@import` inside the root document.
   - Alternative: only rewrite root URL to inline object and hope `@import` is absent — insufficient (issue requires
     caching imports).

5. **HTTP client** — Use the `client` passed into `parse`. When `allowed_context_url` is set and the cache misses,
   `client is None` → `ParserError` / `ValueError`. When unset, `jsonld` may still run with `client is null` (no remote
   resolve). Process-global cache keyed by URL so concurrent workers share hits.

6. **Payload-level `@import`** — If the payload itself contains `@import`, resolve only through the same loader (cached
   fetch). Prefer requiring that any payload remote IRI equals `allowed_context_url`; do not invent a second config key.

7. **Publisso migration** — Follow-up after merge; this change only enables the parser contract.

## Risks / Trade-offs

- [Operator breakage for Schema.org RDIs without the new field] → Update in-repo examples/Helm in the same PR; document
  in `docs/linked_data_to_generic.md`.
- [Trust transitive `@import` from the root URL] → Accepted; same trust as allowing that root.
- [rdflib loader sync vs async] → Prefetch root (+ walk imports if discoverable) under asyncio before sync
  `graph.parse`, or use `asyncio.to_thread` around parse with a sync cache-backed loader that only reads the cache
  (prefetch must populate imports first). Design tests must prove second parse does not HTTP.
- [Mapper-level Schema.org allowlist in `schemaorg-to-arc-mapping` / `jsonld_validation`] → May still apply to mapper
  input expectations; harvest gate is parser config. Avoid double-reject surprises: parse-time hard-coded allowlist
  removed; mapper rules stay until a later cleanup if redundant on graph-only paths.

## Migration Plan

1. Land parser + config + tests.
2. Patch in-repo YAML examples (`allowed_context_url` for Schema.org sources).
3. Operators set the field for production overlays.
4. Separate change: Publisso → `generic` + `jsonld` + FRL context URL.

## Open Questions

None for v1 — field name, stub removal, single URL, process cache, and `@import` caching are locked.
