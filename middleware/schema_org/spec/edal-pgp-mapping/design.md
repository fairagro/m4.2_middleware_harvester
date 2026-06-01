# EDAL-PGP Mapping Design

## Class Structure

```python
@SchemaOrgMapper.register(PayloadType.edal_pgp)
class EdalPgpMapper(GeneralSchemaOrgMapper):
```

Extends `GeneralSchemaOrgMapper` rather than `SchemaOrgMapper(ABC)` to reuse ~400 lines of Investigation/Study/Assay assembly, table construction, ontology sources, and RO-Crate serialization. Only diverging behaviors are overridden.

## Override Map

| Method | General behavior | EDAL-PGP override |
|--------|-----------------|-------------------|
| `_add_contacts` | Dedup by (given, family); iterate creator/author/contributor separately | Dedup by ORCID primary + name secondary; merge richer record; extract nested ORCID from Person.identifier |
| `_node_to_person` | Build Person from given/family/email/url/address | Also extract ORCID from `identifier(PropertyValue)` and store as `Comment("ORCID", …)` |
| `_extract_address` | Expects PostalAddress or Literal | Handle both PostalAddress object AND plain string; parse string by comma split |
| `_add_investigation_comments` | Add License, Language, Version, URL comments | Detect `$licenseURL` → emit `Comment("License", "URL not provided")`; also check `dcterms:conformsTo` fallback; split string keywords |
| `_map_study` | Full description | Truncate description to 500 chars |
| `_map_investigation` | Full description | Keep full description |

## New Helper Methods

| Method | Purpose |
|--------|---------|
| `_parse_edal_date(date_str: str) -> str` | Parse `"Sat Jan 01 00:00:00 CET 2011"` into `"2011-01-01"` using `datetime.datetime.strptime` |
| `_extract_orcid(graph, node) -> str | None` | Walk `schema:identifier` PropertyValue with `propertyID == "orcid"` and return the value |
| `_split_keywords(keywords: str | None) -> list[str]` | If string, split on `,` and trim; else pass through |

## Registered Variant

- `PayloadType.edal_pgp` -> `EdalPgpMapper` via `@SchemaOrgMapper.register()`

## Fixtures

- `tests/fixtures/edal_pgp_sample.json` — 3 real EDAL-PGP datasets (used for integration-level tests)
- Tests use inline RDF graphs for precise assertion control

## Test Strategy

| Test | Coverage |
|------|----------|
| `test_edal_pgp_mapper_orcid_dedup` | Same person with and without ORCID -> 1 contact with ORCID retained |
| `test_edal_pgp_mapper_license_placeholder` | `$licenseURL` -> `Comment("License", "URL not provided")` |
| `test_edal_pgp_mapper_date_parsing` | `"Sat Jan 01 00:00:00 CET 2011"` -> `"2011-01-01"` |
| `test_edal_pgp_mapper_string_address` | Plain string address parsed into structured fields |
| `test_edal_pgp_mapper_creator_not_duplicated` | Creator subset of author -> no duplicate contact |
| `test_edal_pgp_mapper_keywords_string` | Single comma string -> split and join |
| `test_edal_pgp_mapper_long_description` | >500 chars -> study truncated to 500 |
| `test_edal_pgp_mapper_dcterms_conforms_to` | No `schema:conformsTo`, has `dc:conformsTo` -> comment populated |
| `test_edal_pgp_mapper_registry` | `create_mapper` with `PayloadType.edal_pgp` returns `EdalPgpMapper` |
| `test_edal_pgp_mapper_smoke` | Fixture -> non-empty RO-Crate JSON-LD |
