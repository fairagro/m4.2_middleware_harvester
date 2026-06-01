# Schema.org to ARC Mapping by RDI

This document describes how the Schema.org harvester plugin maps dataset metadata from different Research Data Infrastructures (RDIs) to the ISA model (Investigation, Study, Assay) used by ARC.

## Inheritance Model

All RDI-specific mappers inherit from `GeneralSchemaOrgMapper`, which implements the common Schema.org → ARC pipeline:

```
SchemaOrgMapper(ABC)          — contract: map_graph(graph) → str (RO-Crate JSON-LD)
└─ GeneralSchemaOrgMapper     — general Schema.org dataset → ARC, applies defaults
   ├─ EdalPgpMapper           — EDAL-PGP (Leibniz IPK Gatersleben)
   └─ (Future RDIs...)
```

RDI-specific mappers **only override diverging behaviors** — the ~400 lines of Investigation/Study/Assay assembly, table construction, ontology sources, and RO-Crate serialization are reused unchanged.

## RDI Matrix

| RDI | Mapper Class | `PayloadType` | Source Format | Sitemap Type | Registration |
|-----|-------------|---------------|---------------|--------------|-------------|
| General (any schema.org) | `GeneralSchemaOrgMapper` | `general` | HTML + embedded JSON-LD (`application/ld+json`) | XML sitemap | `@SchemaOrgMapper.register(PayloadType.general)` |
| EDAL-PGP (IPK Gatersleben) | `EdalPgpMapper` | `edal_pgp` | HTML + embedded JSON-LD (`application/ld+json`) | XML sitemap | `@SchemaOrgMapper.register(PayloadType.edal_pgp)` |

## ARC Output Structure

Every dataset produces an RO-Crate containing:

- **`ArcInvestigation`** — title, description, contacts, publications, comments
- **`ArcStudy`** — "Data Collection" table + "Data Processing" table
- **`ArcAssay`** — "Measurement" table with URI, license, publisher, language

All serialized via `ARC.ToROCrateJsonString()`.

---

## Case Study: EDAL-PGP (Leibniz IPK Gatersleben)

**Endpoint**: `https://doi.ipk-gatersleben.de/sitemap.xml`

**Data format**: Each DOI landing page (e.g. `https://doi.org/10.5447/ipk/2011/0`) contains a `<script type="application/ld+json">` block with schema.org `Dataset` JSON-LD.

**Characteristics**: Flat `urlset` (~300 DOIs), no nested `sitemapindex`.

### Source → ARC Mapping

#### Investigation Fields

| Source JSON-LD | Graph Property | ARC Output | Method | Notes |
|---------------|---------------|------------|--------|-------|
| `@id` | `@id` or `schema:identifier` | `Investigation.Identifier` | `_map_investigation` | DOI extracted; if absent, slug from title |
| `name` | `schema:name` | `Investigation.Title` | `_map_investigation` | |
| `description` | `schema:description` | `Investigation.Description` | `_map_investigation` | Full description kept (unlike ArcStudy) |
| `datePublished` | `schema:datePublished` | `Investigation.SubmissionDate` | `_map_investigation` | Parsed via `_parse_edal_date`; falls back to `dateModified` |

#### Investigation Comments

| Source JSON-LD | Graph Property | ARC Comment | Method | Notes |
|---------------|---------------|-------------|--------|-------|
| `keywords` | `schema:keywords` | `Comment("Keywords", …)` | `_add_investigation_comments` | Comma-separated string split into individual terms, rejoined |
| `inLanguage` | `schema:inLanguage` | `Comment("Language", …)` | `_add_investigation_comments` | |
| `license` | `schema:license` | `Comment("License", …)` | `_add_license_comment` | `"$licenseURL"` → `"URL not provided"` (see edge cases) |
| `http://purl.org/dc/terms/conformsTo` | `dcterms:conformsTo` | `Comment("Conforms To", …)` | `_add_conforms_to_comment` | Falls back when `schema:conformsTo` absent |
| `distribution[].encodingFormat` + `distribution[].contentUrl` | `schema:distribution` | `Comment("Distribution", …)` | `_add_distribution_comments` | Inherited from GeneralSchemaOrgMapper |

#### Contacts (Persons)

| Source JSON-LD | Graph Property | ARC Contact | Method | Notes |
|---------------|---------------|-------------|--------|-------|
| `author[]` | `schema:author` | `Person` with role `"author"` | `_add_contacts` | Dedup across `creator`/`author`/`contributor` (see below) |
| `creator[]` | `schema:creator` | `Person` with role `"author"` | `_add_contacts` | Prioritized first; persons merged with `author` list via dedup |
| `contributor[]` | `schema:contributor` | `Person` with role `"contributor"` | `_add_contacts` | Deduped against persons already added as `author` |
| `publisher` | `schema:publisher` | `Person` with role `"publisher"` | `_add_contacts` | Organization type; affiliation stored as last name |
| `Person.givenName` + `Person.familyName` | `schema:givenName`, `schema:familyName` | `Person.FirstName`, `Person.LastName` | `_node_to_person` | |
| `Person.address` (PostalAddress) | `schema:address` | `Person.Address` | `_extract_address` | Structured: street → postalCode → addressCountry |
| `Person.address` (string) | `schema:address` (Literal) | `Person.Address` | `_extract_address` → `_parse_string_address` | Comma-split: street, postal code, country |
| `Person.identifier.propertyID=orcid` | nested `schema:identifier` | `Person.Comments[Comment("ORCID", …)]` | `_extract_orcid` | Extracted from PropertyValue structure |

#### Publication

| Source JSON-LD | Graph Property | ARC Output | Method | Notes |
|---------------|---------------|------------|--------|-------|
| `@id` (DOI) or `schema:identifier` | `@id` / `schema:identifier` | `Publication` | `_add_publications` | Authors generated from contacts with role `"author"` |
| `citation[]` | `schema:citation` | `Publication` | `_add_publications` | Additional citations appended |

#### Study

| Source | ARC Output | Method | Notes |
|--------|------------|--------|-------|
| `schema:name` | `Study.Title` | `_map_study` | |
| `schema:description` | `Study.Description` | `_map_study` | **Truncated to 500 chars** |
| `schema:datePublished` | `Study.SubmissionDate` | `_map_study` | Parsed via `_parse_edal_date` |
| `schema:keywords` + `schema:description` | "Data Collection" `ArcTable` | `_create_data_collection_table` | Inherited |
| – | "Data Processing" `ArcTable` | `_create_data_processing_table` | Inherited; includes publisher name |

#### Assay

| Source | ARC Output | Method | Notes |
|--------|------------|--------|-------|
| `schema:name` | `Assay.Title`, `Assay.Identifier` | `_map_assay` | |
| – | `MeasurementType = "Data Collection"` | `_map_assay` | Fixed |
| – | `TechnologyType = "Data Repository"` | `_map_assay` | Fixed |
| – | `TechnologyPlatform = "Schema.org Data Repository"` | `_map_assay` | Fixed |
| `schema:url` or `@id` | "Measurement" table `URI` output column | `_create_assay_table` | Inherited |
| `schema:license` | "Measurement" table `License` comment column | `_create_assay_table` | Inherited |
| `schema:publisher` | "Measurement" table `Publisher` comment column | `_create_assay_table` | Inherited |
| `schema:inLanguage` | "Measurement" table `Language` comment column | `_create_assay_table` | Inherited |

### EDAL-PGP Edge Cases

| Case | Behavior |
|------|----------|
| `$licenseURL` placeholder | Emit `Comment("License", "URL not provided")` — matched as substring (not `==`) to handle rdflib URIRef resolution |
| Non-ISO `datePublished` | `"<dow> <mon> <dd> <time> <tz> <yyyy>"` — parsed via `datetime.strptime("%a %b %d %H:%M:%S %Z %Y")` → `"YYYY-MM-DD"`. On parse failure, original value is passed through |
| Person in `author` and `creator` | Dedup by ORCID (primary key); if no ORCID, dedup by `(givenName, familyName)` (secondary). The richer record (with ORCID, structured address) survives |
| Person `address` is plain string | Split on comma: first part = street, second = postal code, third = country |
| `keywords` is a comma-separated string | Split on `,`, trim whitespace, rejoin as individual Comment terms |
| No `schema:conformsTo` present | Fall back to `dcterms:conformsTo` (`http://purl.org/dc/terms/conformsTo`) |
| Long description (>500 chars) | Investigation gets full text; Study gets truncated to 500 chars |
| Person with no given/family name but `schema:name` | Name auto-split: last space-separated token → `LastName`, rest → `FirstName` |

### Sample Data

| Field | 2011/0 value | 2016/0 value |
|-------|-------------|-------------|
| `name` | "A case study for efficient management of high throughput primary lab data" | "IAP example data set 1107BA_Corn_JPEG" |
| `license` | `"$licenseURL"` (placeholder) | `"https://creativecommons.org/licenses/by/4.0/legalcode"` (real URL) |
| `datePublished` | `"Sat Jan 01 00:00:00 CET 2011"` | `"Tue Apr 12 09:18:19 CEST 2016"` |
| `keywords` | `"bioinformatics, source code, database, LIMS, primary data"` | `"high throughput plant phenotyping, IAP (Integrated Analysis Pipeline)"` |
| Authors | 8 persons (3 with ORCID, mixed address types) | 2 persons (Klukas with ORCID, Pape string address) |
| `creator` | 5 persons (subset of authors, no ORCID) | 1 person (Klukas, no ORCID) |
| `contributor` | 3 persons (no given name, no ORCID) | 1 person (Pape, no given name) |

---

## General Schema.org (Default)

**Mapper**: `GeneralSchemaOrgMapper` (`PayloadType.general`)

Applies to any website embedding schema.org `Dataset` JSON-LD. Handles ~95% of cases without RDI-specific overrides. Differences from EDAL-PGP:

| Aspect | General | EDAL-PGP |
|--------|---------|----------|
| License | Pass-through | `$licenseURL` → `"URL not provided"` |
| ORCID extraction | Not extracted | Extracted from `Person.identifier(PropertyValue)` |
| Person dedup | `(givenName, familyName)` only | ORCID primary + name secondary |
| Address string parsing | `Literal` passed through | Comma-parsed into street/postal/country |
| Keywords | List of literals | Single comma-separated string |
| `dcterms:conformsTo` | Not checked | Fallback when `schema:conformsTo` absent |
| Description | Full in both Investigation + Study | Truncated to 500 in Study only |
| Date parsing | Pass-through | Non-ISO → `YYYY-MM-DD` |

All other behavior (study/assay assembly, ontology sources, RO-Crate serialization, contact roles, publications, distribution comments, assay tables) is identical.

### Known Limitations (General)

- License values that are URIRefs (relative or absolute) are emitted verbatim as the Comment value — no attempt to resolve or validate
- Persons with no `givenName`/`familyName` but a `name` are split by heuristics (last token = family name)
- The Data Collection table only carries "Research Subject" input + keywords parameter — no additional domain-specific columns

---

## Adding a New RDI

1. **Create a spec** in `middleware/{component}/spec/{rdi-name}-mapping/spec.md` + `design.md`
2. **Add `PayloadType` enum entry** in `config.py`
3. **Implement the mapper** subclassing `GeneralSchemaOrgMapper`:
   - Override only the methods that diverge
   - Use `@SchemaOrgMapper.register(PayloadType.{name})` decorator
4. **Export from package** `__init__.py` so the `@register` decorator executes
5. **Add unit tests** for each edge case
6. **Add integration tests** (recorded fixture + optional live test)
7. **Register in harvester config** (set `payload_type` in the RDI's source configuration)
8. **Update this document** with the new RDI's field mapping

Reference: [`middleware/schema_org/spec/edal-pgp-mapping/spec.md`](../middleware/schema_org/spec/edal-pgp-mapping/spec.md) and [`design.md`](../middleware/schema_org/spec/edal-pgp-mapping/design.md).

---

## Implementation Files

| File | Purpose |
|------|---------|
| `src/middleware/schema_org/schema_org_mapper/` | Base and concrete mappers |
| `src/middleware/schema_org/schema_org_mapper/general.py` | `GeneralSchemaOrgMapper` (~430 lines) |
| `src/middleware/schema_org/schema_org_mapper/edal_pgp.py` | `EdalPgpMapper` (~200 lines) |
| `src/middleware/schema_org/config.py` | `PayloadType`, `DatasetType`, `SitemapType` enums |
| `spec/edal-pgp-mapping/spec.md` | Feature requirements |
| `spec/edal-pgp-mapping/design.md` | Design decisions and override map |
| `tests/fixtures/edal_pgp_sample.json` | Sample EDAL-PGP dataset (JSON-LD) |
| `tests/fixtures/sitemap_doi_ipk_gatersleben.xml` | Snapshot of live sitemap |
| `tests/unit/test_edal_pgp_mapper.py` | 26 unit tests |
| `tests/integration/test_edal_pgp_integration.py` | Recorded-fixture pipeline test (5 tests) |
| `tests/integration/test_edal_pgp_live.py` | Live endpoint opt-in test |
