## ADDED Requirements

### Requirement: Schema.org Investigation identifier MUST be harvest-stable

`GeneralSchemaOrgMapper` MUST set `Investigation.identifier` from a catalog-stable value and MUST NOT use an rdflib blank-node label (`N` plus 32 hex digits, or `_:…`), MUST NOT hash or invent an identifier, and MUST NOT fall back to an 80-character title slug.

Resolution MUST follow this order:

1. DOI from `schema:identifier`: a literal whose value starts with `10.`, or a `PropertyValue` whose `propertyID` is an identifiers.org DOI URI or contains `doi` (case-insensitive) and whose `schema:value` starts with `10.` (optional `https://doi.org/` / `http://doi.org/` / `doi:` prefix MAY be stripped).
2. Otherwise a canonical `http(s)` source URL from `schema:url`, then `schema:sameAs`, then the Dataset `@id` when it is an `http(s)` IRI. When that URL (or the discovered page URL) is a MyCoRe Receive-URL (`…/receive/{id}`), the mapper MUST use `{id}` (e.g. `openagrar_mods_*`).
3. Otherwise the discovered dataset page URL supplied by the plugin (Receive-URL / Solr `id` as above).

#### Scenario: OpenAgrar PropertyValue DOI without Dataset @id

- **WHEN** a Schema.org Dataset graph has no `@id`, `url`, or `sameAs`, and `schema:identifier` is a `PropertyValue` with `propertyID` `https://registry.identifiers.org/registry/doi` and `value` `10.3220/253-2025-42`
- **THEN** `Investigation.identifier` MUST be `10.3220/253-2025-42` and MUST NOT match an rdflib blank-node label

#### Scenario: Two parses of the same payload yield the same identifier

- **WHEN** the same Schema.org JSON-LD payload is parsed into a graph twice and mapped twice
- **THEN** both mappings MUST produce the same `Investigation.identifier`

#### Scenario: OpenAgrar record without DOI uses MyCoRe id

- **WHEN** a Schema.org Dataset graph has no DOI and no `url`/`sameAs`/`http(s)` `@id`, and the discovered page URL is `https://www.openagrar.de/receive/openagrar_mods_00107322`
- **THEN** `Investigation.identifier` MUST be `openagrar_mods_00107322`

#### Scenario: Missing DOI and missing source URL fails mapping

- **WHEN** a Schema.org Dataset graph has no DOI and no `http(s)` `url`/`sameAs`/`@id`, and no discovered page URL is supplied
- **THEN** mapping MUST raise a mapping error, MUST NOT return a `HarvestedArc`, and MUST NOT use `str(subject)` of a blank node as the identifier

### Requirement: Schema.org mapping failures without a stable identifier MUST become record-level harvest errors

When Schema.org mapping refuses a record for lack of a stable identifier, the linked-data plugin MUST yield a `RecordProcessingError` (a `HarvesterError`) for that record and MUST NOT upload an ARC. The harvest run MUST continue with remaining records.

#### Scenario: Unidentifiable Dataset is reported, not uploaded

- **WHEN** Schema.org mapping raises because no DOI, URL, or MyCoRe id is available
- **THEN** the plugin MUST yield `RecordProcessingError` for that dataset and MUST NOT yield a `HarvestedArc` for it
