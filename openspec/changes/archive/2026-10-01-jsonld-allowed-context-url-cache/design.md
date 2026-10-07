# Design

## Context

See `proposal.md` — Why. Today `JsonLdParser` rejects remote `@context` except a hard-coded Schema.org `@vocab` swap;
`HtmlJsonLdParser` validates against `SCHEMAORG_CONTEXT_ALLOWLIST` then calls `graph.parse`, which can still
network-fetch schema.org. Both parsers already receive `NiceHttpClient | None` and `ParserConfig` (threshold only).
Generic always passes a live client; inline `jsonld` historically allowed `client is null` when no remote context is
needed.

## Goals / Non-Goals

**Goals:**

- One optional pinned root context URL on `ParserConfig`, shared by `jsonld` and `html_jsonld`.
- Process-lifetime URL→document cache; polite HTTP only on miss; transitive `@import` from the loaded root also cached.
- When the field is set, fail closed for payload remote IRIs that are not that exact URL.
- When unset, still fetch absolute http(s) remotes via the same cache, with a one-time warning per URL (legacy configs).
- Stop rdflib from performing its own uncached context fetches during parse (custom document loader / pre-inline).

**Non-Goals:**

- Vendored Schema.org trees or API package sharing.
- Multi-URL operator allowlists; TTL/ETag; Publisso config migration in this change.
- Changing Regal `linked_data` dataset behaviour (still rdflib-native fetch until operators move to `generic`).

## Decisions

1. **Field name `allowed_context_url` on `ParserConfig`** — Sibling `parser:` block is already the shared place for
   JSON-LD threshold; one optional `http(s)` URL keeps per-RDI control without plugin-specific fields.
   - Alternative considered: list of URLs — rejected (operator asked for exactly one).

2. **Exact string match when the field is set** — No http/https or trailing-slash normalisation in v1; operators set the
   IRI that actually appears in payloads (e.g. `https://schema.org/` vs `http://schema.org`).
   - Alternative: normalise Schema.org variants — deferred; can layer later without changing the one-URL model.

3. **Unset = fetch; warn on ParserConfig (compat)** — Removing the Schema.org `@vocab` stub must not break operator
   overlays that omit the new field. Absolute http(s) remotes are fetched through the shared loader. `ParserConfig` logs
   a `logger.warning` at validation when `jsonld` / `html_jsonld` omit `allowed_context_url` (same pattern as other
   legacy config warnings). Relative / non-http(s) still fail closed.
   - Alternative: reject when unset — rejected (breaks existing configs).
   - Alternative: warn per fetched URL in the loader — rejected (prefer config-time warning).

4. **Remove Schema.org `@vocab` stub and hard-coded parse-time allowlist** — One mechanism only. Prefer pinning via
   `allowed_context_url`. Bioschemas as a second remote string on the payload is not supported when the field is set
   unless it arrives via `@import` from the configured root.
   - Alternative: keep stub + new URL — rejected (two policies).

5. **Shared loader module under `middleware.parsing`** — Cache dict + async resolve used before `graph.parse`. Prefer
   rewriting payload `@context` to the inlined cached object after validating policy. Choose the approach that reliably
   covers `@import` inside the root document.

6. **HTTP client** — Use the `client` passed into `parse`. Whenever a remote context must be resolved (pinned or
   unpinned compat path) and the cache misses, `client is None` → `ParserError`. When there is no remote context,
   `jsonld` may still run with `client is null`. Process-global cache keyed by URL so concurrent workers share hits.

7. **Payload-level `@import`** — Resolve only through the same loader (cached fetch). When `allowed_context_url` is set,
   any payload remote IRI must equal that URL; do not invent a second config key.

8. **Publisso migration** — Follow-up after merge; this change only enables the parser contract.

## Risks / Trade-offs

- [Unpinned remotes trust any absolute http(s) URL] → Accepted for compat; warning + recommend pinning. Operators who
  set the field get fail-closed exact match.
- [Trust transitive `@import` from the root URL] → Accepted; same trust as allowing that root.
- [rdflib loader sync vs async] → Prefetch root (+ walk imports) under asyncio before sync `graph.parse`. Design tests
  must prove second parse does not HTTP.
- [Mapper-level Schema.org allowlist] → Harvest gate is parser config; mapper rules stay until a later cleanup if
  redundant on graph-only paths.

## Migration Plan

1. Land parser + config + tests (compat warning path included).
2. Patch in-repo YAML examples (`allowed_context_url` for Schema.org sources) as the recommended shape.
3. Operators pin the field on production overlays when convenient (warnings until then).
4. Separate change: Publisso → `generic` + `jsonld` + FRL context URL.

## Open Questions

None — field name, stub removal, single URL, process cache, `@import` caching, and unset=warn+fetch are locked.
