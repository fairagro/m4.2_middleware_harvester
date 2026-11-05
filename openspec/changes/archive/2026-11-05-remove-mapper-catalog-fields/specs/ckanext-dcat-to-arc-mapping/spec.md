## MODIFIED Requirements

### Requirement: Register a ckanext_dcat DataMapper

The system SHALL register a DataMapper under `MapperType.ckanext_dcat` (`mapper.type: ckanext_dcat`) accepting
`rdf_graph`. The mapper type child MUST NOT accept `catalog_name` or `catalog_url` (unknown keys fail closed). Catalog /
RDI provenance MUST NOT be configured on the harvester mapper; it is owned by the middleware API `known_rdis` registry.

#### Scenario: Composes with the jsonld parser

- **WHEN** a generic repository uses nested `protocol.dcat_ap.entry_url` (or deprecated flat `protocol_type: dcat_ap` +
  `sitemap_url`), `parser.type: jsonld` and `mapper.type: ckanext_dcat`
- **THEN** config validation succeeds and each discovered dataset yields a `HarvestedArc`

#### Scenario: catalog fields are rejected

- **WHEN** a `mapper.ckanext_dcat` (or lifted flat) block sets `catalog_name` or `catalog_url`
- **THEN** configuration validation fails

### Requirement: Map dcat:Dataset to ARC Investigation, Study and Assay

The mapper SHALL build an ARC Investigation from the `dcat:Dataset` (title, description, identifier slug derived from
the dataset IRI) with Investigation comments for source identifier, modified date, keywords, language, publisher,
contact point and spatial extent. It MUST NOT write `Investigation.Comment("Data Catalog")` from mapper config. It SHALL
add one Study (`<id>_study`) with a dataset-processing table and one Assay (`<id>_assay`) with a distribution table; the
Assay has no table when the distribution table would have no columns (see "Assay table MUST NOT invent an input
source").

#### Scenario: Dataset with distribution

- **WHEN** a dataset graph has a title and one `dcat:Distribution`
- **THEN** the ARC root carries the title and a stable identifier derived from the dataset IRI

#### Scenario: No Data Catalog comment from mapper

- **WHEN** a dataset is mapped successfully
- **THEN** the Investigation MUST NOT carry a `Comment("Data Catalog")` produced by `CkanextDcatMapper`
