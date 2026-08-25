## Context

See proposal.md for motivation (issue #138). Today `GeneralSchemaOrgMapper`
embeds a large private RDF-hygiene block (`_obj` / `_str` / `_strs`, language
policy, BNode content signatures, DOI / PropertyValue, http/https Schema.org
aliases). `RegalMapper` still uses `graph.value` and weaker string helpers.
Discovery context is passed as loose `map_graph(..., source_url=, harvest_source_id=)`
kwargs. This change introduces a shared access layer and migrates Schema.org
onto it in one reviewable unit; Regal only updates the ABC signature.

## Goals / Non-Goals

**Goals:**

- Ship `stable_graph.py` with ResourceView accessors that match current Schema.org
  hygiene semantics (lift-first, not a speculative ideal DSL).
- Migrate `GeneralSchemaOrgMapper` to views; delete duplicated private helpers.
- Introduce `MappingContext` on the mapper ABC; plugin constructs it from discovery.
- Keep identifier cascade and publisher-invert policy in the Schema.org mapper,
  composing `doi()` / `http_iri()` / resource accessors.
- New capability spec `stable-graph`; thin requirement deltas on mapper + harvesting.

**Non-Goals:**

- Regal ResourceView migration (follow-up).
- YAML mapping DSL, skolemization, runtime harvest linter.
- Putting MappingContext into `StableGraph.wrap`.
- Encoding ARC identifier cascade or publisher Comment rules inside stable-graph.

## Decisions

1. **Phase cut = API + Schema.org together; Regal later**
   — Reasoning: Schema.org already *is* the reference implementation of the
   proposed API. An API-only PR risks designing accessors in a vacuum and leaves
   dead code until migration. Existing Schema.org unit tests are the
   behaviour-preservation gate. Regal migration will fix remaining footguns and
   must stay a separate change.
   — Alternatives considered: strict issue Phase 1 (API only); mega-PR including
   Regal.

2. **Spec-Home = new `stable-graph` + thin mapper/harvesting deltas**
   — Reasoning: ResourceView is shared infrastructure (like `nice-http-client`),
   not ARC field mapping. MappingContext belongs on the mapper ABC / plugin
   contract, not in the RDF access capability — keeps `stable-graph` free of
   harvest identity.
   — Alternatives considered: fold everything into `linked-data-mapper`; put
   MappingContext requirements inside `stable-graph`.

3. **MappingContext on `map_graph`, never on StableGraph.wrap**
   — Reasoning: `source_url` / `harvest_source_id` are discovery context for
   identifier planning and assay URL fallback — layer B / mapper policy. No
   ResourceView accessor needs them. Wrapping them into StableGraph would couple
   RDF hygiene to harvest identity and force Regal to carry unused context in the
   access layer.
   — Alternatives considered: kwargs forever; context field on wrap.

4. **Soft API: lift Schema.org semantics first**
   — Reasoning: Today's `_str` / `_obj` / `_strs` policies are battle-tested.
   Prefer mechanical preserve (same language ranks, BNode signatures, dual
   schema.org namespaces). Tighten literal-vs-resource purity call-site by
   call-site where it does not change harvest output; do not invent a third
   policy during extract.
   — Alternatives considered: redesign accessors first, then adapt Schema.org.

5. **Identifier cascade + publisher invert stay mapper-local; `doi()` is a graph brick**
   — Cascade order (harvest context → graph URL → DOI) and
   publisher-preferring-resources-over-literals are Schema.org ARC policies
   (inverted vs default literal preference). Issue #138 keeps cascade out of the
   API but lists `doi()` with PropertyValue as a brick: reading a DOI from
   Literal / IRI / PropertyValue-*shaped* RDF is still StableGraph concern when
   `term_namespaces` are configured; deciding Investigation.identifier vs
   Publication vs Alternate Identifier stays mapper-local.
   — Alternatives considered: PropertyValue only in mapper; full
   `resolve_investigation_id` inside the API.

6. **Module layout**
   — `linked_data_mapper/stable_graph.py` for types + wrap; `MappingContext` lives
   next to the ABC (`linked_data_mapper.py` or a tiny sibling module) so harvesting
   / ABC do not import RDF accessors to build context.
   — Keep `person_contacts.py` as-is.

7. **StableGraph is call-scoped (no `self._stable`)**
   — The plugin maps with one shared mapper via `asyncio.to_thread`. Storing the
   wrap on the instance would cross-talk. ABC passes `stable` into `_map_graph`;
   Schema.org may use a per-call `_SchemaOrgRun`, but a `_*Run` class is not
   mandatory for every vocabulary. Concurrent `map_graph` unit tests guard this.
   — Alternatives considered: `contextvars` / `threading.local()`; serialize mapping.

## Risks / Trade-offs

- **[Risk] Behaviour drift during Schema.org migrate** → Mitigation: treat
  existing `test_mapper.py` / `test_mapper_identifier.py` as acceptance; add
  focused ResourceView unit tests before deleting private helpers.
- **[Risk] `doi()` PropertyValue shape couples access to Schema.org-like RDF** →
  Mitigation: gate on configured `term_namespaces`; document as shaped-node brick,
  not Investigation.identifier policy; Regal can omit namespaces or ignore `doi()`.
- **[Risk] ABC signature break churns Regal + all tests** → Mitigation: thin
  adapter in Regal (`_ = context`); update call sites mechanically; no Regal
  behaviour change in this PR.
- **[Trade-off] Larger than prior single-mapper stability PRs** → Accepted:
  extract without a consumer is riskier than one medium Schema.org+API change.

## Migration Plan

1. Add `stable_graph.py` + API unit tests (no mapper behaviour change yet, or
   behind parallel helpers).
2. Introduce `MappingContext`; update ABC, plugin, Regal signature, tests.
3. Point Schema.org call sites at ResourceView; delete private hygiene block.
4. Run linked_data unit tests + ruff; confirm no Regal logic changes beyond
   signature.
5. Follow-up change: Regal onto ResourceView / `unknown_texts` / `labelled`.

Rollback: revert the change branch; no config or API-server migration.

## Open Questions

None that block implementation; PropertyValue-in-`doi()` and soft-lift defaults
are decided above.
