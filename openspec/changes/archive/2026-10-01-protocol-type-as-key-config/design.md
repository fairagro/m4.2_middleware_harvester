# Design

## Context

See proposal.md — Why. Today `generic.Config` owns `protocol_type`, `sitemap_url`, `http`, and `page_size` flat beside
plugin orchestration fields. Protocol takes a structural `SupportsSitemapUrl` view so linked_data can pass its own
`Config`. House style for removing `type` + type-named nested redundancy is type-as-key under a parent, with truly
shared fields as siblings of that key.

## Goals / Non-Goals

**Goals:**

- Canonical YAML: `generic.protocol.http` shared; exactly one type key with type-specific settings
- Rename discovery entry to `entry_url` (semantics vary by protocol)
- Concrete Pydantic settings models per protocol type; drop `SupportsSitemapUrl`
- Deprecated flat tree lifts with warning; conflict if both trees disagree

**Non-Goals:**

- Removing the deprecated flat tree (reminder issue)
- Type-as-key for `mapper:` / `parser:` (follow-up issue)
- Changing linked_data operator YAML shape in this change

## Decisions

1. **ProtocolConfig with type-as-key fields** — `ProtocolConfig` holds `http` plus optional `xml` / `mycore_solr`
   type-config models; validator requires exactly one type key. Discriminator is the key name (no parallel `type:`
   field). Alternative rejected: `protocol: { type, … }` flat — keeps shared/type mix and diverges from the agreed
   redundancy removal.

2. **Type config models live with their Protocol** — `XmlProtocolConfig` / `MycoreSolrProtocolConfig` in their Protocol
   modules subclass shared `ProtocolTypeConfig` (no assumed shared fields). `entry_url` is declared only on types that
   need it. Protocol `__init__(config, client)` stores `config`. Plugin config does **not** re-export type-specific
   fields such as `entry_url`.

3. **Deprecated flat lift on generic.Config** — After validation, `protocol` is always set. If only flat fields present,
   warn and build `ProtocolConfig` (`sitemap_url` → type `entry_url`; flat `http`/`page_size` applied where relevant).
   If both present, require agreement (same type + same entry URL + compatible http/page_size) or fail closed; still
   warn. Flat fields marked `deprecated=True`.

4. **No ProtocolConfigView** — linked_data shim builds `MycoreSolrProtocolConfig` from `sitemap_url`/`page_size` instead
   of duck-typing full plugin config.

5. **Plugin/http ownership** — `GenericPlugin` builds `NiceHttpClient` from `config.protocol.http`. Plugin-only fields
   remain on `generic.Config` (`worker_tasks`, `resource_base_url`). JSON-LD parse offload thresholds are independent:
   `protocol.dcat_ap.jsonld_parse_threshold_bytes` for catalog-page discovery and `parser.jsonld_parse_threshold_bytes`
   for PayloadParsers.

6. **source_url / resource base** — Repository `source_url` and `effective_resource_base_url` derive from `protocol`
   type settings `entry_url` after lift.

## Risks / Trade-offs

- [Risk] Operators miss deprecation warnings → Mitigation: reminder issue; keep lift until removed; document both shapes
  in examples.
- [Risk] Adding a protocol type requires a new field on `ProtocolConfig` → Mitigation: accepted closed-schema trade-off;
  registry still validates the selected key.
- [Risk] Flat `http` default previously always present → Mitigation: flat `http` defaults to `None`; defaults live on
  `ProtocolConfig.http`.

## Migration Plan

1. Ship nested `protocol:` + deprecated lift.
2. Migrate example/demo YAML opportunistically to nested form.
3. Later issue removes flat fields and lift path.

## Open Questions

None.
