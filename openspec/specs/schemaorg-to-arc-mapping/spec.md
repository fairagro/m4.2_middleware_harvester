# Schema.org to ARC Mapping

## Purpose

Transforms a Schema.org RDF graph (parsed from JSON-LD embedded in HTML pages or
inline in API responses) into ARC investigation components (ISA). The graph may
contain one or more `schema:Dataset` entities, optionally nested within
`schema:DataCatalog`, with associated `schema:DataDownload` distributions.

**Authoritative Mapping Source:** [docs/schemaorg_mapping.md](../../../docs/schemaorg_mapping.md)
defines the conceptual mapping rules. This spec captures the implementation
contract.

**Skill Reference:** Agents must load `.agents/skills/arctrl/SKILL.md` when writing or
modifying code that constructs `ArcInvestigation`, `ArcStudy`, or `ArcAssay` objects.

## Requirements

### Requirement: Map each Schema.org Dataset to exactly one Investigation

The system SHALL map each `schema:Dataset` entity in the input graph to exactly
one `Investigation` with title, description, contacts, publications, ontology
annotations, and investigation comments as defined in the authoritative mapping
source.

#### Scenario: Single Dataset per graph

- **GIVEN** an RDF graph containing exactly one `schema:Dataset` subject with
  `schema:name` "Soil Moisture Time Series 2023"
- **WHEN** the mapper processes the graph
- **THEN** exactly one `Investigation` is produced with title
  "Soil Moisture Time Series 2023"

#### Scenario: Multiple Dataset entities on one page

- **GIVEN** an RDF graph containing two `schema:Dataset` subjects: Dataset A
  (`schema:name` "Dataset Alpha", `@id`
  "https://example.org/dataset/alpha") and Dataset B (`schema:name`
  "Dataset Beta", `@id` "https://example.org/dataset/beta")
- **WHEN** the mapper processes the graph
- **THEN** two mapping outputs are produced, one per Dataset, each with its
  own `Investigation.identifier` derived from its respective `@id` or discovered
  page URL
- **AND** the outputs are yielded in deterministic subject order
  (`StableGraph.subjects_of_types` / sort key), independent of RDF triple
  insertion order

#### Scenario: Dataset nested in DataCatalog

- **GIVEN** an RDF graph with a `schema:DataCatalog` subject that has
  `schema:hasPart` pointing to two `schema:Dataset` subjects
- **WHEN** the mapper processes the graph
- **THEN** two mapping outputs are produced (one per Dataset); the DataCatalog
  itself does not produce an Investigation

### Requirement: Reject graphs with no mappable Dataset

The system SHALL reject (mapping error) RDF graphs that contain no
`schema:Dataset` subject (in either `http://schema.org/` or
`https://schema.org/` namespace).

#### Scenario: Empty graph

- **GIVEN** an RDF graph with no triples
- **WHEN** the mapper processes the graph
- **THEN** a mapping error is raised

#### Scenario: Only DataCatalog, no Dataset

- **GIVEN** an RDF graph containing only a `schema:DataCatalog` with no
  `schema:hasPart` linking to any `schema:Dataset`
- **WHEN** the mapper processes the graph
- **THEN** a mapping error is raised

### Requirement: Validate @context before mapping

The system SHALL extract `@context` from the raw JSON-LD payload before RDF
parsing, accept known Schema.org and extension context IRIs (HTTP and HTTPS
variants), and reject unknown remote context IRIs with a mapping error.
`@import` and nested remote `@context` loads MUST be absolute allowlisted
`http(s)` IRIs (relative imports are rejected). Absolute `http(s)` `@vocab`
values MUST be allowlisted; relative `@vocab` MAY be accepted (IRI expansion
only). Namespace aliasing of `http://schema.org/` and `https://schema.org/`
terms happens during RDF access via `StableGraph`, not by rewriting the
`@context` string.

#### Scenario: Standard Schema.org HTTPS context

- **GIVEN** a JSON-LD payload with `"@context": "https://schema.org/"`
- **WHEN** the mapper processes the payload
- **THEN** parsing proceeds; all `schema:` terms resolve to
  `https://schema.org/`

#### Scenario: Standard Schema.org HTTP context

- **GIVEN** a JSON-LD payload with `"@context": "http://schema.org/"`
- **WHEN** the mapper processes the payload
- **THEN** parsing proceeds; HTTP and HTTPS Schema.org namespaces are treated
  as aliases via `StableGraph`

#### Scenario: Mixed http/https in same graph

- **GIVEN** a JSON-LD payload where some terms use `http://schema.org/` and
  others `https://schema.org/`
- **WHEN** the mapper processes the payload
- **THEN** both namespaces are treated as aliases; term accessors return values
  from both without duplication

#### Scenario: Known extension context (Bioschemas)

- **GIVEN** a JSON-LD payload with
  `"@context": ["https://schema.org/", {"bioschemas": "https://bioschemas.org/"}]`
  and a `bioschemas:Sample` entity
- **WHEN** the mapper processes the payload
- **THEN** parsing proceeds; extension terms are available for mapping

#### Scenario: Unknown context

- **GIVEN** a JSON-LD payload with
  `"@context": "https://unknown-vocabulary.example.org/"`
- **WHEN** the mapper processes the payload
- **THEN** a mapping error is raised before RDF parsing

#### Scenario: Relative @import rejected

- **GIVEN** a JSON-LD payload with a dict `@context` containing
  `"@import": "./remote-context.jsonld"`
- **WHEN** the mapper processes the payload
- **THEN** a mapping error is raised before RDF parsing

### Requirement: Support vocabulary extensions via declared extension namespaces

The system SHALL allow mappers to declare supported extension namespaces (beyond
core Schema.org) that participate in term aliasing and access without code
changes to the shared RDF access layer.

#### Scenario: Mapper declares Bioschemas extension

- **GIVEN** a mapper configured with Bioschemas extension namespace
- **WHEN** the mapper processes a graph containing `bioschemas:Sample` entities
- **THEN** type checks and term accessors for "Sample" and "identifier" find
  the Bioschemas predicates

### Requirement: Investigation.identifier follows a documented, deterministic cascade

The system SHALL assign `Investigation.identifier` using the following precedence
(highest first), and the chosen identifier MUST be stable across harvests of the
same logical dataset:

1. Harvest-source catalog identifier when supplied by discovery (e.g., MyCoRe
   Solr `id`) — only when the graph contains a single `schema:Dataset`
2. Sanitized discovered page URL when supplied by discovery — only when the
   graph contains a single `schema:Dataset`
3. Canonical HTTP(S) IRI from `schema:url` → `schema:sameAs` → subject `@id`
   (lexicographic minimum, casefold)
4. Canonical DOI from `schema:identifier` (including `schema:PropertyValue` with
   `propertyID` containing "doi") — only when no higher-precedence identifier
   exists

When a graph contains multiple `schema:Dataset` entities, steps 1–2 are skipped
so each Investigation uses that Dataset's own graph URI or DOI (steps 3–4).

DOIs (including all extracted DOIs) MUST appear in `Publication` and/or
`Investigation` Comments; they MUST NOT become the primary
`Investigation.identifier` when a harvest-source identifier (1 or 2) is
available.

#### Scenario: Catalog identifier from discovery

- **GIVEN** a discovered record with catalog identifier "12345" and the graph
  contains a DOI "10.1234/example"
- **WHEN** the mapper assigns the identifier
- **THEN** `Investigation.identifier` = "12345"; the DOI appears in a
  Publication

#### Scenario: Discovered page URL only

- **GIVEN** a discovered record with page URL
  "https://repo.example.org/dataset/abc" (no catalog identifier), graph subject
  `@id` = "https://repo.example.org/dataset/abc#this"
- **WHEN** the mapper assigns the identifier
- **THEN** `Investigation.identifier` = sanitized
  "https://repo.example.org/dataset/abc"

#### Scenario: No discovery context, graph has URL and DOI

- **GIVEN** no discovery context, graph subject has `schema:url`
  "https://data.example.org/ds/1" and DOI "10.5678/ds1"
- **WHEN** the mapper assigns the identifier
- **THEN** `Investigation.identifier` = sanitized
  "https://data.example.org/ds/1"; DOI appears in Publication

#### Scenario: No discovery context, graph has only DOI

- **GIVEN** no discovery context, graph subject has only a DOI
  "10.9999/only-doi" in `schema:identifier`
- **WHEN** the mapper assigns the identifier
- **THEN** `Investigation.identifier` = "10.9999/only-doi" (DOI used as last
  resort)

#### Scenario: Two harvests of same logical dataset yield same identifier

- **GIVEN** the same logical dataset harvested twice with identical discovery
  catalog identifier
- **WHEN** both harvests are mapped
- **THEN** both produce identical `Investigation.identifier` values

### Requirement: Study Data Collection protocol uses keywords, not description

When `schema:keywords` are present, the system SHALL add a single-row Study
protocol table named "Data Collection" with a Keywords parameter. Dataset
`schema:description` SHALL map only to `Investigation.Description` and
`Study.Description` — it MUST NOT be emitted as a Data Collection parameter
(abstract text is not a per-process factor and would duplicate Study fields).

#### Scenario: Keywords create Data Collection protocol

- **GIVEN** a Dataset with `schema:keywords` "soil, moisture" and a non-empty
  `schema:description`
- **WHEN** the mapper builds the Study
- **THEN** a "Data Collection" table exists with a Keywords parameter, and the
  description appears on Investigation/Study only (not as a protocol parameter)

#### Scenario: Description alone does not create Data Collection

- **GIVEN** a Dataset with `schema:description` but no `schema:keywords`
- **WHEN** the mapper builds the Study
- **THEN** no "Data Collection" protocol table is created

### Requirement: Handle schema:DataDownload distributions as comments

The system SHALL map each `schema:DataDownload` linked via
`schema:distribution` on the Dataset that has a non-empty `contentUrl` into
distribution metadata comments (not additional Assay output columns). Multiple
Measurement output columns per row are not ARCtrl-compatible; the Assay
Measurement table keeps a single landing-page `Output [URI]` and records file
access as comments.

For each eligible distribution the system SHALL:

1. Append an Investigation comment named `"Distribution"` with label
   `encodingFormat: contentUrl` when `encodingFormat` is present, otherwise
   just `contentUrl`.
2. Include the same labels in one Measurement table comment column named
   `"Distribution"`, joined with `"; "` when multiple distributions exist.

Entries without `contentUrl` MUST be skipped.

#### Scenario: Dataset with single DataDownload

- **GIVEN** a Dataset with `schema:distribution` → `schema:DataDownload` having
  `contentUrl` "https://repo.example.org/data/file.csv" and `encodingFormat`
  "text/csv"
- **WHEN** the mapper creates Investigation and Assay
- **THEN** Investigation has a `"Distribution"` comment
  `"text/csv: https://repo.example.org/data/file.csv"`
- **AND** the Measurement table has a `"Distribution"` comment column with that
  same label
- **AND** the Measurement `Output [URI]` remains the dataset landing-page URI
  (not the download `contentUrl`)

#### Scenario: Dataset with multiple DataDownload

- **GIVEN** a Dataset with two `schema:distribution` entries that both have
  `contentUrl` (e.g. CSV and JSON)
- **WHEN** the mapper creates Investigation and Assay
- **THEN** Investigation has one `"Distribution"` comment per entry
- **AND** the Measurement table has a single `"Distribution"` comment column
  whose cell joins both labels with `"; "`
- **AND** no extra Assay output columns are created for the downloads

#### Scenario: DataDownload without contentUrl is skipped

- **GIVEN** a `schema:DataDownload` under `schema:distribution` with
  `encodingFormat` but empty or missing `contentUrl`
- **WHEN** the mapper processes distributions
- **THEN** that entry is omitted from Investigation and Measurement
  `"Distribution"` comments

### Requirement: Fail closed on missing required fields

The system SHALL raise a mapping error (not invent fallbacks) when:

- A `schema:Dataset` lacks a non-empty `schema:name`
- A Person contact (creator/author/contributor) would have an empty given name
- The identifier cascade yields no usable identifier

#### Scenario: Dataset without name

- **GIVEN** a `schema:Dataset` with no `schema:name` literal
- **WHEN** the mapper processes the Dataset
- **THEN** a mapping error is raised indicating the missing required field

#### Scenario: Person contact without given name

- **GIVEN** a `schema:creator` that is a `schema:Person` with only
  `schema:familyName` "Müller"
- **WHEN** the mapper processes the contact
- **THEN** a mapping error is raised indicating the missing given name

### Requirement: Deterministic ordering of multi-value fields

The system SHALL produce deterministic (harvest-stable) ordering for all
multi-value fields: keywords (trim/dedup/sort casefold), contacts (sort by
family, given, display, then stable node key), publications (DOI order), DOIs
(casefold lexicographic minimum is canonical). When a graph yields multiple
`schema:Dataset` subjects, the mapper SHALL emit Investigation outputs via
`StableGraph.subjects_of_types` (deterministic subject order), independent of
RDF triple insertion order.

#### Scenario: Keywords with mixed case and duplicates

- **GIVEN** a Dataset with `schema:keywords` ["Agriculture", "agriculture",
  "Soil", "soil"]
- **WHEN** the mapper extracts keywords
- **THEN** the Investigation comment "Keywords" contains "Agriculture, Soil"
  (deduped, casefold-sorted, original casing of first occurrence preserved)

#### Scenario: Contacts from unordered RDF

- **GIVEN** two harvests of the same graph where `schema:creator` order differs
- **WHEN** both are mapped
- **THEN** the Investigation Contacts list has identical order in both harvests

#### Scenario: Multi-Dataset yield order is insertion-independent

- **GIVEN** two graphs with the same two `schema:Dataset` subjects inserted in
  opposite order
- **WHEN** both are mapped
- **THEN** the sequence of Investigation identifiers is identical across both
  harvests

### Requirement: Serialize the resulting ARC as valid RO-Crate JSON-LD

The system SHALL serialize the resulting ARC as valid RO-Crate JSON-LD.

#### Scenario: Successful mapping

- **GIVEN** a valid Dataset graph with all required fields
- **WHEN** mapping completes
- **THEN** the output is valid RO-Crate JSON-LD; `studies` = 1; `assays` = 1

### Requirement: Implement mapping in a dedicated Schema.org mapper

The system SHALL implement mapping in a dedicated mapper distinct from Regal or
INSPIRE mappers.

#### Scenario: Mapper selection by payload type

- **GIVEN** a repository configuration for Schema.org payload
- **WHEN** the plugin constructs the mapper
- **THEN** the returned mapper is the Schema.org mapper implementation
