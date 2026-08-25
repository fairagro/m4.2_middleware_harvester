## Purpose

Provide a hard, DSL-like RDF access layer so linked-data vocabulary mappers
read graphs only through StableText and ResourceView — never raw rdflib blank
node labels or unstable iteration order — without introducing a YAML mapping DSL.

## ADDED Requirements

### Requirement: StableGraph wrap yields ResourceView for subjects

The system SHALL provide a StableGraph wrapper over an `rdflib.Graph` that
exposes subjects as ResourceView handles. A ResourceView for a blank-node
subject MUST expose no public IRI (IRI is absent / null). Wrap configuration
MAY include label predicates and namespace aliases. Wrap MUST NOT accept
harvest/discovery context (`source_url`, `harvest_source_id`, or equivalent).

#### Scenario: Blank-node subject has no IRI

- **WHEN** a ResourceView is obtained for a blank-node subject
- **THEN** the view MUST NOT expose a usable public IRI string for that subject

#### Scenario: Wrap does not take mapping context

- **WHEN** a graph is wrapped for ResourceView access
- **THEN** the wrap API MUST NOT require or store discovery `source_url` or
  `harvest_source_id`

### Requirement: Literal accessors never return blank-node labels

ResourceView singular and plural literal accessors MUST return only trimmed
literal text (StableText). They MUST NOT stringify blank nodes. Multi-literal
selection MUST drop empty values and prefer language tags in order `en`, then
`de`, then untagged, then other, with deterministic length-then-lexicographic
tie-breaks for singular picks. Plural literal lists MUST be deduplicated and
ordered with a documented stable Unicode policy (casefold-aware).

#### Scenario: Multi-language literals prefer English

- **WHEN** a predicate has empty, `de`, and `en` literals
- **THEN** the singular literal accessor MUST return the non-empty `en` value

#### Scenario: Plural literals are order-stable

- **WHEN** the same logical set of keyword literals is present in two different
  RDF object iteration orders
- **THEN** the plural literal accessor MUST return the same ordered list both times

### Requirement: Resource accessors are deterministic and exclude BNode labels as ids

ResourceView singular and plural resource accessors MUST return only resource
nodes (URIRef or blank), never literals. Default iteration and singular picks
among multiple resources MUST use a deterministic key based on IRI or a
bounded blank-node content signature — NEVER the parser-local blank-node label.
Accessors MAY filter by RDF type.

#### Scenario: Two blank publishers rank without using BNode labels

- **WHEN** a predicate has two blank-node objects that differ only by nested
  content (and blank-node labels differ between parses)
- **THEN** singular and plural resource accessors MUST pick / order using
  content signatures consistently across parses and MUST NOT use blank-node
  labels as sort or identity keys

### Requirement: Labelled nodes skip unlabelled blank nodes

A labelled-node accessor MUST return label text from configured label
predicates (for example `schema:name` or `skos:prefLabel`) plus a stable id
only when the object is a real IRI. Blank nodes without a resolvable label
MUST be omitted. The accessor MUST NEVER use `str(BNode)` as label or id.

#### Scenario: Unlabelled blank node is skipped

- **WHEN** a predicate object is a blank node with no configured label
- **THEN** the labelled-node accessor MUST omit that object

#### Scenario: Labelled blank node keeps label without BNode id

- **WHEN** a blank-node object has a configured label literal
- **THEN** the accessor MUST include that label and MUST NOT set a stable id
  from the blank-node label

### Requirement: DOI helper accepts Literal, IRI, and PropertyValue-shaped nodes

The access layer SHALL provide a DOI extraction helper that accepts a literal
or IRI whose normalized value starts with `10.` (optional `https://doi.org/` /
`http://doi.org/` / `doi:` prefix MAY be stripped). When wrap-time
`term_namespaces` are configured, the helper MUST also accept a
PropertyValue-*shaped* RDF node whose `propertyID` indicates DOI
(identifiers.org DOI URI or contains `doi`, case-insensitive) and whose value
starts with `10.` (Schema.org is the reference vocabulary for that shape). The
helper MUST NOT invent identifiers, MUST NOT return blank-node labels, and MUST
NOT decide ARC Investigation.identifier / Publication / Comment policy — that
remains vocabulary-mapper responsibility.

#### Scenario: PropertyValue DOI is extracted

- **WHEN** an identifier node is a PropertyValue with DOI `propertyID` and
  value `10.3220/253-2025-42` and Schema.org term namespaces are configured
- **THEN** the DOI helper MUST return `10.3220/253-2025-42`

#### Scenario: Blank node without DOI fields yields no DOI

- **WHEN** the node is an unlabelled blank node with no DOI PropertyValue fields
- **THEN** the DOI helper MUST return no DOI

### Requirement: HTTP IRI helper rejects blank nodes

An HTTP IRI helper MUST return only `http` or `https` IRI strings from suitable
nodes and MUST return no value for blank nodes.

#### Scenario: Blank node has no HTTP IRI

- **WHEN** the HTTP IRI helper is applied to a blank node
- **THEN** the result MUST be absent / null

#### Scenario: HTTPS URIRef is returned

- **WHEN** the helper is applied to an `https://` URIRef
- **THEN** the result MUST be that IRI string

### Requirement: Namespace aliases resolve dual Schema.org schemes

The access layer SHALL support resolving the same Schema.org term under both
`http://schema.org/` and `https://schema.org/` in one logical predicate access
so callers need not duplicate lookups.

#### Scenario: Objects under http and https schema.org are both visible

- **WHEN** a Dataset has `name` under `http://schema.org/` and `keywords` under
  `https://schema.org/`
- **THEN** aliased accessors for those terms MUST see the respective objects
  without the caller issuing two separate namespace lookups

### Requirement: Shared test helper detects blank-node labels in harvest output

The system SHALL provide a shared unit-test helper that asserts serialized ARC /
harvest JSON does not embed rdflib blank-node labels (`N` plus 32 hex digits, or
`_:…`) in identifier or comment text positions under test. The helper is for
tests only; production harvest MUST NOT require a runtime hard-fail linter.

#### Scenario: Helper fails when Comment text is a BNode label

- **WHEN** test ARC JSON contains Comment text matching an rdflib blank-node label
- **THEN** the helper MUST fail the assertion
