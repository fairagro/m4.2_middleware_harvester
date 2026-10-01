# dcat-ap-protocol Specification

## Purpose

Generic-plugin `Protocol` that discovers records from Hydra-paginated DCAT-AP JSON-LD catalogs (e.g. CKAN
`ckanext-dcat`) and yields one inline JSON-LD discovery unit per `dcat:Dataset`.

## Requirements

### Requirement: Register a dcat_ap Protocol

The system SHALL register a `Protocol` implementation under `ProtocolType.dcat_ap` (`generic.protocol_type: dcat_ap`)
whose entry point is `generic.sitemap_url`.

#### Scenario: dcat_ap resolves from the registry

- **WHEN** a generic repository sets `protocol_type: dcat_ap`
- **THEN** config validation and `GenericPlugin.create_protocol` resolve the DCAT-AP Protocol

### Requirement: Follow Hydra pagination

The Protocol SHALL fetch the entry page, then each `hydra:nextPage` URL until none remains, and MUST fail with
`GenericProtocolError` when a page URL repeats or a page cannot be fetched or parsed as JSON-LD.

#### Scenario: Multi-page catalog

- **WHEN** page 1 links to page 2 via `hydra:nextPage` and page 2 has no next page
- **THEN** datasets from both pages are discovered, in page order

#### Scenario: Pagination loop

- **WHEN** a `hydra:nextPage` points to an already visited page
- **THEN** discovery fails with a pagination-loop `GenericProtocolError`

### Requirement: Yield one inline JSON-LD unit per dataset

For each `dcat:Dataset` IRI on a page, the Protocol SHALL yield a `JsonLdDiscoveryResult` whose `identifier` is the
dataset IRI and whose `payload` is expanded JSON-LD (no `@context`) containing the dataset's Concise Bounded Description
plus the CBD of objects of `dcat:distribution`, `dcterms:publisher`, `dcat:contactPoint` and `dcterms:spatial`.

#### Scenario: Distribution and publisher included

- **WHEN** a dataset references a named distribution and publisher on the same page
- **THEN** the dataset's payload contains the distribution and publisher triples, and no other dataset's triples

### Requirement: Expected count from hydra:totalItems

The Protocol SHALL report `hydra:totalItems` of the entry page as the expected count, or `None` when absent or
non-numeric.

#### Scenario: Total items present

- **WHEN** the entry page declares `hydra:totalItems` 2
- **THEN** `get_expected_count()` returns 2
