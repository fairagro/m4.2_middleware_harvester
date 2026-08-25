## MODIFIED Requirements

### Requirement: Schema.org Investigation identifier MUST be harvest-stable

`GeneralSchemaOrgMapper` MUST set `Investigation.identifier` from a harvest-stable value and MUST NOT use an rdflib blank-node label (`N` plus 32 hex digits, or `_:…`), MUST NOT hash or invent an identifier, and MUST NOT fall back to an 80-character title slug.

Resolution MUST follow this decision chain:

1. When `harvest_source_id` is supplied (from the sitemap/discovery layer), `Investigation.identifier` MUST be that value. DOI(s) from the graph MUST NOT be used as `Investigation.identifier` when step 1 applies.
2. Else when the plugin supplies a discovered page URL (`source_url`), `Investigation.identifier` MUST be the sanitized discovered page URL. DOI(s) from the graph MUST NOT be used as `Investigation.identifier` when step 2 applies.
3. Else when the graph provides a canonical `http(s)` source URL via `schema:url`, then `schema:sameAs`, then the Dataset `@id` when it is an `http(s)` IRI, `Investigation.identifier` MUST be that URL sanitized for arctrl identifier constraints.
4. Else if exactly one valid DOI is present, `Investigation.identifier` MAY be that DOI (last resort for isolated graphs without harvest context).
5. Else if multiple valid DOIs are present without harvest or graph URL context, `Investigation.identifier` MUST be the lexicographic minimum of the normalized DOI strings (Unicode `casefold` comparison). Non-canonical DOIs MUST appear as Investigation Comments named `Alternate Identifier`.
6. Else mapping MUST fail closed (mapping error; no `HarvestedArc`).

When `harvest_source_id` or `source_url` is supplied and the graph lists multiple DOIs, non-canonical DOIs MUST appear as Investigation Comments named `Alternate Identifier`. The canonical Publication DOI MUST be the lexicographic minimum regardless of rdflib or JSON-LD order.

DOI extraction rules are unchanged: a literal whose value starts with `10.`, or a `PropertyValue` whose `propertyID` is an identifiers.org DOI URI or contains `doi` (case-insensitive) and whose `schema:value` starts with `10.`.

#### Scenario: OpenAgrar PropertyValue DOI with harvest source id uses catalog id

- **WHEN** a Schema.org Dataset graph has `schema:identifier` as a `PropertyValue` with DOI `10.3220/253-2025-42`, the discovered page URL is `https://www.openagrar.de/receive/openagrar_mods_00107322`, and `harvest_source_id` is `openagrar_mods_00107322`
- **THEN** `Investigation.identifier` MUST be `openagrar_mods_00107322` and the DOI MUST appear in ARC metadata but MUST NOT be `Investigation.identifier`

#### Scenario: OpenAgrar PropertyValue DOI without source URL falls back to DOI

- **WHEN** a Schema.org Dataset graph has no `@id`, `url`, or `sameAs`, and `schema:identifier` is a `PropertyValue` with DOI `10.3220/253-2025-42`, and no discovered page URL or `harvest_source_id` is supplied
- **THEN** `Investigation.identifier` MUST be `10.3220/253-2025-42`

#### Scenario: OpenAgrar record without DOI uses sanitized source URL when no harvest source id

- **WHEN** a Schema.org Dataset graph has no DOI and no `url`/`sameAs`/`http(s)` `@id`, the discovered page URL is `https://www.openagrar.de/receive/openagrar_mods_00107322`, and no `harvest_source_id` is supplied
- **THEN** `Investigation.identifier` MUST be `www_openagrar_de_receive_openagrar_mods_00107322`

#### Scenario: OpenAgrar record without DOI uses harvest source id when supplied

- **WHEN** the same graph and page URL as above, and `harvest_source_id` is `openagrar_mods_00107322`
- **THEN** `Investigation.identifier` MUST be `openagrar_mods_00107322`

#### Scenario: Multiple DOIs with harvest source id preserve alternates

- **WHEN** a Schema.org Dataset has DOIs `10.5281/zenodo.15672440` and `10.3220/253-2025-54` in either order, `source_url` is `https://www.openagrar.de/receive/openagrar_mods_00107508`, and `harvest_source_id` is `openagrar_mods_00107508`
- **THEN** `Investigation.identifier` MUST be `openagrar_mods_00107508` on every mapping and the mapped ARC MUST contain an Investigation Comment named `Alternate Identifier` with the non-canonical DOI

#### Scenario: Shared DOI on two pages uses distinct harvest identifiers

- **WHEN** two Schema.org Dataset graphs from different Receive-URLs both contain DOI `10.1594/PANGAEA.957630`, with `harvest_source_id` values `openagrar_mods_00088718` and `openagrar_mods_00109919`
- **THEN** the mappings MUST set `Investigation.identifier` to those harvest source ids respectively and MUST NOT use the shared DOI as `Investigation.identifier`

#### Scenario: Generic source URL without harvest source id uses sanitized page URL

- **WHEN** a Schema.org Dataset graph contains DOI `10.1594/PANGAEA.957630` and `source_url` is `https://example.org/generic-page` with no `harvest_source_id`
- **THEN** `Investigation.identifier` MUST be the sanitized page URL and MUST NOT be `10.1594/PANGAEA.957630`
