# ckanext-dcat-to-arc-mapping Specification

## Purpose

Shared RDF DataMapper that maps one DCAT-AP `dcat:Dataset` graph in the CKAN `ckanext-dcat` flavour to an ARC.

## Requirements

### Requirement: Register a ckanext_dcat DataMapper

The system SHALL register a DataMapper under `MapperType.ckanext_dcat` (`mapper.type: ckanext_dcat`) accepting
`rdf_graph`, configurable with optional `mapper.catalog_name` and http(s) `mapper.catalog_url` (blank values treated as
unset).

#### Scenario: Composes with the jsonld parser

- **WHEN** a generic repository uses nested `protocol.dcat_ap.entry_url` (or deprecated flat `protocol_type: dcat_ap` +
  `sitemap_url`), `parser.type: jsonld` and `mapper.type: ckanext_dcat`
- **THEN** config validation succeeds and each discovered dataset yields a `HarvestedArc`

### Requirement: Map dcat:Dataset to ARC Investigation, Study and Assay

The mapper SHALL build an ARC Investigation from the `dcat:Dataset` (title, description, identifier slug derived from
the dataset IRI) with Investigation comments for source identifier, modified date, keywords, language, publisher,
contact point, spatial extent and — when configured — the data catalog (`catalog_name` / `catalog_url`). It SHALL add
one Study (`<id>_study`) with a dataset-processing table and one Assay (`<id>_assay`) with a distribution table.

#### Scenario: Dataset with distribution

- **WHEN** a dataset graph has a title and one `dcat:Distribution`
- **THEN** the ARC root carries the title and a stable identifier derived from the dataset IRI

### Requirement: Unwrap ckanext-dcat raw CKAN JSON-string fields

The mapper SHALL unwrap organisation literals that are raw CKAN JSON strings — a bare object or a single-element array
with `*_name` / `*_email` keys — into a display name with email, and use any other literal verbatim.

#### Scenario: Maintainer JSON string

- **WHEN** a literal is `{"maintainer_name": "A", "maintainer_email": "a@x"}`
- **THEN** the mapped value is `A <a@x>`
