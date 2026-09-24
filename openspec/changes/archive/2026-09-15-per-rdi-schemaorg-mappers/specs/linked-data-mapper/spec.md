## ADDED Requirements

### Requirement: RDI-specific Schema.org behaviour MUST live in a per-RDI mapper

`GeneralSchemaOrgMapper` MUST encode only RDI-agnostic Schema.org rules. It MUST NOT branch on repository identity (host
name, catalog id shape, publisher name, or a configured RDI key), and MUST NOT relax a base contract solely because one
repository violates it.

Behaviour that only one repository needs MUST be implemented in a dedicated mapper that subclasses the shared format
mapper and is registered in a dedicated **overlay registry** keyed by overlay name, separate from the `payload_type`
registry. The overlay MUST override only the extension points it needs and MUST inherit everything else, so that
`RDI mapper = base format mapper + repository-specific overrides` (see `#170`).

Overlays MUST NOT be keyed by `PayloadType`. `payload_type` names the payload **format**; an overlay's payload format is
unchanged by the repository quirks it absorbs, and encoding RDI identity into `PayloadType` would contradict `#140`'s
protocol ≠ payload format decision and misrepresent the eventual `PayloadKind`.

Each overlay MUST declare the payload format it builds on (`BUILDS_ON`, mirroring `#170`'s `builds_on` and `#140`'s
`accepts`), so an overlay paired with an incompatible `payload_type` fails fast rather than mapping with the wrong base.
Configuration binding is specified in `linked-data-harvesting`.

An overlay mapper MUST NOT be created without behaviour to put in it. A rule that applies unchanged to any repository
exposing the same payload shape — for example the harvest-stable `Investigation.identifier` cascade — is RDI-agnostic
and MUST stay in the shared mapper even when a single RDI motivated it.

#### Scenario: Repository-specific rule is selected by the mapper key

- **WHEN** plugin config names an overlay via `mapper` alongside the base `payload_type`
- **THEN** overlay registry resolution MUST return that overlay class, and mapping MUST apply the overlay's rules in
  addition to the shared Schema.org rules

#### Scenario: Overlay declares the format it builds on

- **WHEN** a per-RDI overlay mapper is registered
- **THEN** it MUST declare a `BUILDS_ON` payload format, and pairing it with a different configured `payload_type` MUST
  fail fast at plugin construction

#### Scenario: Shared mapper is unaffected by an overlay's relaxation

- **WHEN** the same graph is mapped by `GeneralSchemaOrgMapper` and by an overlay that relaxes a base fail-closed rule
  for that graph
- **THEN** the shared mapper MUST still fail closed, and only the overlay MUST produce a `HarvestedArc`

#### Scenario: Shared mapper does not branch on repository identity

- **WHEN** the shared Schema.org mapper maps two graphs that differ only in host name, publisher name, or catalog id
  shape
- **THEN** mapping behaviour MUST depend only on the Schema.org terms present, not on which repository the record came
  from

### Requirement: Schema.org title resolution MUST expose a per-RDI extension point

`GeneralSchemaOrgMapper` MUST provide an overridable title-fallback hook that receives the Dataset's `ResourceView` and
the `MappingContext`, and returns either a resolved field carrying the value and the name of the carrier it came from,
or null when no fallback applies. That return type MUST be a named, reusable value object (`ResolvedField`), not a bare
tuple, so additional fallback fields adopt one shape instead of inventing their own conventions. The hook MUST be
callable from the per-call Schema.org run holder without that holder becoming the subclassing surface.

The shared mapper's implementation MUST return null (no fallback beyond `schema:name`). The fail-closed raise, and the
recording of the resolved fallback as an Investigation Comment named `Title Source` plus a WARNING log line, MUST stay
in the shared mapper so every overlay reports provenance identically.

Each mapper MUST declare the title carriers it accepts, and the fail-closed mapping error MUST name exactly those
carriers.

#### Scenario: Base mapper reports only schema:name as a title carrier

- **WHEN** `GeneralSchemaOrgMapper` maps a Dataset with no usable title
- **THEN** the mapping error MUST name `schema:name` and MUST NOT name carriers the shared mapper never reads

#### Scenario: Overlay fallback is recorded as provenance by the shared mapper

- **WHEN** an overlay mapper's hook returns a resolved field
- **THEN** the resulting Investigation MUST carry a Comment named `Title Source` whose text is that field's carrier
  name, and the mapper MUST emit a WARNING log line identifying the Dataset, the carrier, and the resolved title

#### Scenario: Overlay hook returning null falls through to the shared raise

- **WHEN** an overlay mapper's hook finds no usable fallback
- **THEN** `map_graph` MUST fail closed with the shared mapper's mapping error and MUST NOT return a `HarvestedArc`

### Requirement: StableGraph wrap policy MUST be instance-scoped and single-sourced

`LinkedDataMapper._stable_wrap` MUST be an instance method, not a static method, so a mapper's wrap policy — in
particular its `term_namespaces` — can derive from the mapper instance rather than only from a hardcoded class body.
This keeps the vocabulary-extension requirement in `schemaorg-to-arc-mapping` ("mappers declare supported extension
namespaces … without code changes to the shared RDF access layer") reachable from configuration or a profile object
later, without changing the ABC again.

A Schema.org mapper MUST have exactly one source of truth for its term namespaces. The namespace tuple used for
`rdf:type` Dataset subject selection MUST be the same tuple passed to `StableGraph.wrap`, so adding a vocabulary
extension is a single edit and cannot leave term access and type detection disagreeing.

#### Scenario: Wrap policy can vary per mapper instance

- **WHEN** `map_graph` wraps a graph
- **THEN** it MUST call the wrap through the mapper instance, and a subclass or instance carrying different term
  namespaces MUST see those namespaces in the resulting `StableGraph` policy

#### Scenario: Dataset subject selection and term access share one namespace set

- **WHEN** a Schema.org mapper declares its term namespaces
- **THEN** Dataset `rdf:type` selection and `ResourceView` term accessors MUST both use that set, with no second
  namespace list maintained in parallel

#### Scenario: Existing Schema.org and Regal behaviour is unchanged

- **WHEN** the existing Schema.org and Regal unit suites run after the wrap policy becomes instance-scoped
- **THEN** they MUST pass unchanged, including the concurrent `map_graph` cross-talk guards

## MODIFIED Requirements

### Requirement: Schema.org Dataset MUST have a non-empty schema:name

`GeneralSchemaOrgMapper` MUST require a non-empty Dataset `schema:name` (after trim) for Investigation / Study / Assay
titles and for Study/Assay identifier slugs. It MUST NOT invent display titles such as `Untitled` / `Untitled Dataset`
and MUST NOT invent Study/Assay identifier fallbacks such as `untitled` / `dataset`. When `schema:name` is missing or
blank, or sanitizes to an empty slug, `map_graph` MUST fail closed with a mapping error (no `HarvestedArc`). The shared
helper `to_identifier_slug` MUST return null for blank input or an empty sanitized slug; Schema.org MUST treat that as a
mapping error. `Investigation.identifier` resolution remains the harvest-stable cascade and MUST NOT use the title slug.

A per-RDI overlay mapper MAY accept an alternative title carrier for its own `payload_type` by overriding the
title-fallback hook, but MUST NOT weaken this requirement for `GeneralSchemaOrgMapper` itself, MUST NOT invent a display
title absent from the payload, and MUST record which carrier was used. Overlay titles are subject to the same slug rule:
a resolved title that sanitizes to an empty Study/Assay slug MUST still fail closed.

#### Scenario: Dataset without schema:name fails mapping

- **WHEN** a Schema.org Dataset graph has no non-empty `schema:name` (and otherwise would be mappable)
- **THEN** `map_graph` MUST raise a mapping error and MUST NOT return a HarvestedArc

#### Scenario: Dataset with schema:name maps titles from that name

- **WHEN** a Schema.org Dataset graph has `schema:name` `Example Dataset`
- **THEN** Investigation, Study, and Assay titles MUST be `Example Dataset` and Study/Assay identifiers MUST be the slug
  of that name

#### Scenario: Overlay title still drives Study and Assay identifier slugs

- **WHEN** an overlay mapper resolves a title from a fallback carrier
- **THEN** Investigation, Study, and Assay titles MUST be that resolved title and Study/Assay identifiers MUST be the
  slug of it, exactly as for `schema:name`
