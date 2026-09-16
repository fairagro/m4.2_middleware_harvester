## Context

See `proposal.md` for motivation (`#227`, follow-up from `#221`). Today
`LinkedDataMapper.registry` is keyed by `PayloadType` and holds exactly one
mapper per *vocabulary* (`schema_org_general` → `GeneralSchemaOrgMapper`,
`regal_general` → `RegalMapper`). Schema.org mapping runs through a per-call
frozen `_SchemaOrgRun(mapper, stable)` holder, because the plugin maps
concurrently via `asyncio.to_thread` on one shared mapper instance
(`linked-data-mapper`: "StableGraph MUST be call-scoped").

The only RDI-specific rule in the shared mapper is `#164`'s title fallback in
`_SchemaOrgRun._resolve_dataset_title`. An audit of `#125` found no e!DAL-PGP
code to move: `grep -rni 'edal\|pgp' middleware/linked_data/src/` returns
nothing, and both `#125` commits touch tests only.

## Goals / Non-Goals

**Goals:**

- One extension point on `GeneralSchemaOrgMapper` that an RDI overlay overrides.
- Base mapper fails closed on missing `schema:name` again.
- OpenAgrar overlay registered under its own `payload_type`.
- Per-mapper test modules; base tests keep base behaviour.

**Non-Goals:**

- `#170` docs layout / `builds_on` metadata.
- `#140` payload-layer move.
- Overlays for e!DAL-PGP, Regal, or INSPIRE.
- Any change to the identifier cascade or `#148`.

## Decisions

1. **Composition = subclass the format mapper, registered in a dedicated overlay
   registry keyed by name, selected by a new `mapper:` config field**
   — Reasoning: `#170` states the model directly —
   `RDI mapper = base format mapper + repository-specific overrides` — and
   subclassing plus the existing `from_config` machinery expresses it with no new
   mapping logic. The *key* matters more than the mechanism: `payload_type` names
   the payload **format**, and OpenAgrar's format is plain Schema.org — only its
   completeness differs. Adding `schema_org_openagrar` would encode RDI identity
   into the format enum, contradicting `#140`'s founding decision (protocol ≠
   payload format), leaving `#140`'s `accepts` compatibility check nothing sane
   to validate, and churning operator-visible YAML that `#140` would then have to
   migrate again. A separate `mapper:` key keeps the two axes independent and is
   the shape `#140` already proposes, so `#140` can adopt or rename it instead of
   undoing it. Selection stays explicit and non-guessing
   (`linked-data-harvesting`: do not infer source formats), and an operator can
   fall back to the base mapper by deleting one line.
   — Alternatives considered: (a) a new `PayloadType` value — smallest diff, but
   see above; rejected on `#140` collision and YAML migration cost; (b)
   composition/delegation with an injected `RdiPolicy` object — more indirection
   than two known overlays justify, and it still needs a registry keyed by
   something that is not `payload_type`; (c) keep one mapper and branch on an
   `rdi` config field — exactly the pattern `#227` exists to remove; (d) wait for
   `#140` to land the `mapper:` key — leaves the base contract silently weakened
   for every Schema.org RDI in the meantime.

1b. **Overlays declare `BUILDS_ON`; mismatches fail fast at construction**
   — Reasoning: Two independent config keys can be paired incoherently
   (`mapper: openagrar` with a Regal `payload_type`). Declaring the base format
   on the overlay turns that into a startup error instead of a confusing mapping
   failure per record, and adopts `#170`'s `builds_on` vocabulary and `#140`'s
   `accepts` role in the one place that already knows the answer.
   — Alternatives considered: validate in the Pydantic `Config` (the config layer
   would have to import the mapper registry — wrong direction); no validation
   (fails per record, far from the cause).

2. **Extension point is a public method on the mapper, not on `_SchemaOrgRun`**
   — Reasoning: `_SchemaOrgRun` is per-call state (`stable` + `mapper`) and is
   deliberately *not* the subclassing surface — the spec explicitly says a
   `_*Run` class per vocabulary is not required. Overriding on the mapper keeps
   the overlay free of run-holder plumbing. The hook is public
   (`resolve_title_fallback`, not `_resolve_title_fallback`) because
   `_SchemaOrgRun` calls it across object boundaries, like the existing
   `to_identifier_slug` / `sanitize_identifier` / `pick_canonical_doi` calls —
   a protected call there would be a pylint `protected-access` violation.
   — Alternatives considered: make `_SchemaOrgRun` itself overridable per RDI
   (couples overlays to call-scoped internals); pass a callback into the run
   holder (same effect, less discoverable).

3. **Hook signature `(ResourceView, MappingContext) -> ResolvedField | None`**
   — Reasoning: The overlay needs graph access for the subject *and* the
   out-of-graph page-title hint, but nothing else; handing it the raw `Node` +
   `StableGraph` would re-expose RDF hygiene the access layer exists to hide.
   Returning value + carrier keeps the `Title Source` provenance comment in the
   base — provenance is not RDI-specific, only the *chain* is. `None` means "no
   fallback", so the base owns the fail-closed raise exactly once. `ResolvedField`
   is a named frozen dataclass rather than a bare `tuple[str, str]` because the
   realistic next quirks are the same shape for description, date, and license;
   three ad-hoc tuple conventions would be three chances to swap the elements.
   — Alternatives considered: bare `str | None` with the base labelling it
   `"fallback"` (loses which carrier won, which is the point of the comment); a
   `tuple[str, str]` (positionally ambiguous, and every future field re-decides).

4. **`TITLE_SOURCES` class attribute for the error message**
   — Reasoning: The fail-closed error must name what was actually tried, or it
   misleads operators debugging a skipped record. Deriving the message from a
   class attribute keeps the raise in the base while staying accurate per
   mapper, and doubles as the overlay's documented chain.
   — Alternatives considered: overlay raises its own error (duplicates the
   fail-closed rule in every overlay); generic message listing all carriers any
   mapper might use (the `#164` status quo — it tells an e!DAL operator the
   mapper looked at `headline`, which it did not).

5. **No `EdalPgpSchemaOrgMapper`**
   — Reasoning: `#125` has no RDI-specific code. Its fix is the harvest-stable
   identifier cascade, whose own spec scenarios are written against OpenAgrar
   payloads — it is RDI-agnostic by construction and never branches on repository
   identity. An empty subclass would be a speculative seam, which `principles.md`
   rules out ("do not invent … until a second plugin needs the same mechanism").
   Adding one later costs one enum value and one config line.
   — Alternatives considered: create it anyway as a home for future e!DAL
   quirks (rejected: YAGNI, plus it implies to readers that e!DAL needs
   special handling when the 336-record live verification on `#125` shows it
   does not).

5b. **Instance-scoped `_stable_wrap` and one namespace source, now**
   — Reasoning: These are the two cheap halves of the *dialect* axis
   (Bioschemas / AgriSchema), which is orthogonal to the RDI axis this change
   opens. `StableGraphPolicy.term_namespaces` is already a tuple that every
   `ResourceView.schema_*` accessor iterates, so the access layer needs nothing —
   but `_stable_wrap` being a `@staticmethod` means a mapper's namespace set can
   only ever come from a hardcoded class body, never from config or a profile.
   That is the single hardest piece to retrofit because it lives on the ABC, and
   it gets harder with every mapper added. `map_graph` already calls
   `self._stable_wrap(graph)`, so the conversion is call-site compatible.
   Collapsing `SCHEMA_URIS` into `SCHEMA_ORG_NAMESPACES` removes the second
   namespace list; today a dialect addition that updates one and not the other
   yields a graph whose terms resolve but whose `Dataset` subjects do not — a
   silent, confusing failure.
   — Alternatives considered: defer both to a dialect change (rejected: ABC
   churn compounds, and the fix is a signature change with no behaviour change);
   also move the `@context` allowlist now (deferred: it lives in the dataset
   layer and needs a mapper→dataset thread, so it is a follow-up issue, not
   silent scope creep); build the full `SchemaOrgProfile` now (YAGNI — no dialect
   has landed, and the profile is pure addition once one does).

6. **OpenAgrar config migration is explicit, not aliased**
   — Reasoning: Operators must opt in by adding `mapper: openagrar`. A silent
   alias (e.g. auto-selecting the overlay when the host looks like OpenAgrar)
   would reintroduce RDI guessing at the config layer, which
   `linked-data-harvesting` forbids ("do not infer source formats
   automatically").
   — Alternatives considered: make the OpenAgrar overlay the default for
   `schema_org_general` (spreads the quirk to every RDI again, i.e. the bug being
   fixed).

## Risks / Trade-offs

- **[Risk] An OpenAgrar deployment is left without `mapper: openagrar`** → the
  ~13 of 910 records that omit `schema:name` start failing closed again
  (record-level `HarvesterError`, no silent garbage, rest of the harvest
  unaffected). Mitigation: config change shipped in the same PR; called out in
  `proposal.md` Impact and in the PR body.
- **[Risk] Two selection paths (`payload_type` and `mapper`) confuse operators**
  → Mitigation: `mapper` is optional and additive, the field description states
  it selects an RDI overlay on top of `payload_type`, and an incompatible pair
  fails fast at construction with both values named.
- **[Risk] Instance `_stable_wrap` touches the ABC and both existing mappers** →
  Mitigation: signature-only change with no behaviour change; the existing Regal
  stability, Schema.org identifier, and concurrent-`map_graph` cross-talk guards
  all exercise it.
- **[Risk] Overlay drifts from the base as the base evolves** → Mitigation: the
  overlay overrides exactly one method and inherits everything else; a base
  signature change breaks it at type-check time (`mypy` / `@override`).
- **[Trade-off] One overlay class per RDI** does not compose: an RDI needing two
  overlays' behaviour has no answer but duplication. Accepted while overlays are
  few; the declarative `SchemaOrgProfile` is the planned answer if it recurs.
- **[Trade-off] `TITLE_SOURCES` is documentation-as-code** and can fall out of
  sync with the override. Mitigation: overlay tests assert the error text lists
  the carriers it actually tries.

## Migration Plan

1. Land the seam changes first (instance `_stable_wrap`, single namespace source,
   `ResolvedField`, overlay registry + `mapper` config) with no behaviour change;
   full suite green proves the refactor is inert.
2. Land the hook + base fail-closed restore + overlay mapper together (the base
   change alone would regress OpenAgrar).
3. Ship the `helm/harvester/values.yaml` OpenAgrar `mapper:` line in the same PR.
4. After deploy, confirm the OpenAgrar harvest still maps the `schema:name`-less
   records (non-zero `Title Source` comments) and that e!DAL's record count is
   unchanged.

## Open Questions

None blocking.

- Whether `#170` later reshapes these overlays into
  `docs/mappers/rdi/openagrar_schemaorg.md` + generated code is tracked on
  `#170`; this change deliberately does not pre-empt that format, but does adopt
  its `builds_on` vocabulary.
- Whether `#140` lands `mapper:` as a plain string or a nested block
  (`{type, profile}`). This change uses a string; the overlay registry sits one
  indirection behind it, so either shape resolves to the same class.
- Whether `#177`'s RDF-first direction eventually replaces overlay classes with
  `.rq` artifacts. Nothing here forecloses it — an overlay could later delegate
  to a SPARQL CONSTRUCT — but nothing anticipates it either.
