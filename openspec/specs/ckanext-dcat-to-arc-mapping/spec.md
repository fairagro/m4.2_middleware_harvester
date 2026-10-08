# ckanext-dcat-to-arc-mapping Specification

## Purpose

Shared RDF DataMapper that maps one DCAT-AP `dcat:Dataset` graph in the CKAN `ckanext-dcat` flavour to an ARC.

**Authoritative Mapping Source:** [docs/mappers/ckanext-dcat.md](../../../docs/mappers/ckanext-dcat.md) defines the
conceptual mapping rules. This spec captures the implementation contract.

## Requirements

### Requirement: Authoritative CKAN ckanext-dcat mapping document path

The CKAN `ckanext-dcat` DCAT-AP→ARC field tables and conceptual mapping rules SHALL live in
[`docs/mappers/ckanext-dcat.md`](../../../docs/mappers/ckanext-dcat.md). This spec remains the implementation contract
and MUST NOT restate those field tables. Implementations SHALL honour the mapping document linked here.

#### Scenario: Spec points at central ckanext-dcat mapping doc

- **WHEN** a contributor needs CKAN `ckanext-dcat` source→ARC field placement rules
- **THEN** they use `docs/mappers/ckanext-dcat.md` as the authoritative mapping source for this domain

### Requirement: Register a ckanext_dcat DataMapper

The system SHALL register a DataMapper under `MapperType.ckanext_dcat` (`mapper.type: ckanext_dcat`) accepting
`rdf_graph`, configurable with optional `mapper.catalog_name` and http(s) `mapper.catalog_url` (blank values treated as
unset).

#### Scenario: Composes with the jsonld parser

- **WHEN** a generic repository uses nested `protocol.dcat_ap.entry_url`, `parser.type: jsonld` and
  `mapper.type: ckanext_dcat`
- **THEN** config validation succeeds and each discovered dataset yields a `HarvestedArc`

### Requirement: Map dcat:Dataset to ARC Investigation, Study and Assay

The mapper SHALL build an ARC Investigation from the `dcat:Dataset` (title, description, identifier slug derived from
the dataset IRI) with Investigation comments for source identifier, modified date, keywords, language, publisher,
contact point, spatial extent and — when configured — the data catalog (`catalog_name` / `catalog_url`). It SHALL add
one Study (`<id>_study`) with a dataset-processing table and one Assay (`<id>_assay`) with a distribution table.

#### Scenario: Dataset with distribution

- **WHEN** a dataset graph has a title and one `dcat:Distribution`
- **THEN** the ARC root carries the title and a stable identifier derived from the dataset IRI

### Requirement: Fail closed on missing dcat:Dataset title

The mapper MUST require a non-empty `dcterms:title` (after trim) for Investigation / Study / Assay titles. It MUST NOT
invent display titles such as `Untitled`. When the title is missing or blank, mapping MUST fail closed with a mapping
error (no `HarvestedArc`). Identifier fallbacks MUST NOT invent `untitled` when sanitization and the title slug are both
empty.

#### Scenario: Dataset without dcterms:title fails mapping

- **WHEN** a `dcat:Dataset` graph has no non-empty `dcterms:title`
- **THEN** mapping MUST raise a mapping error and MUST NOT return a HarvestedArc

### Requirement: Unwrap ckanext-dcat raw CKAN JSON-string fields

The mapper SHALL unwrap organisation literals that are raw CKAN JSON strings — a bare object or a single-element array
with `*_name` / `*_email` keys — into a display name with email, and use any other literal verbatim.

#### Scenario: Maintainer JSON string

- **WHEN** a literal is `{"maintainer_name": "A", "maintainer_email": "a@x"}`
- **THEN** the mapped value is `A <a@x>`

### Requirement: dcterms:issued MUST be datePublished

`CkanextDcatMapper` MUST set Investigation and Study `PublicReleaseDate` (RO-Crate `datePublished`) from
`dcterms:issued`, else `dcterms:modified`. `SubmissionDate` (RO-Crate `dateCreated`) MUST stay empty.

#### Scenario: Issued date

- **WHEN** a dataset has `dcterms:issued` "2025-11-25T11:58:28"
- **THEN** the RO-Crate root `datePublished` MUST be "2025-11-25T11:58:28" and the root MUST NOT have `dateCreated`

#### Scenario: Only a modified date

- **WHEN** a dataset has no `dcterms:issued` and `dcterms:modified` "2026-01-02"
- **THEN** the RO-Crate root `datePublished` MUST be "2026-01-02"
