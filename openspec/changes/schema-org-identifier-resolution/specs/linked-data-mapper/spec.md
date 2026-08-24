## MODIFIED Requirements

### Requirement: Schema.org Investigation identifier MUST be harvest-stable

`GeneralSchemaOrgMapper` MUST set `Investigation.identifier` from a catalog-stable value and MUST NOT use an rdflib blank-node label (`N` plus 32 hex digits, or `_:…`), MUST NOT hash or invent an identifier, and MUST NOT fall back to an 80-character title slug.

When mapping context includes a per-run set of **colliding DOIs** (DOIs associated with more than one discovered `source_url` in the same harvest batch), resolution MUST follow this decision chain:

1. If any valid DOI extracted from the graph is in the colliding-DOI set AND an RDI-specific ID is extractable from `source_url` (OpenAgrar: MyCoRe id matching `openagrar_mods_*` from a `/receive/{id}` URL), `Investigation.identifier` MUST be that RDI-specific ID. The shared external DOI(s) MUST remain in ARC metadata (Publication and/or Investigation Comments) but MUST NOT be used as `Investigation.identifier`.
2. Else if multiple valid DOIs are present on this page, `Investigation.identifier` MUST be the lexicographic minimum of the normalized DOI strings (Unicode `casefold` comparison). The choice MUST NOT depend on rdflib object iteration order or JSON-LD array order. Non-canonical DOIs MUST appear as Investigation Comments named `Alternate Identifier` (one per alternate DOI, deduplicated).
3. Else if exactly one valid DOI is present, `Investigation.identifier` MUST be that DOI.
4. Else resolution MUST follow the existing non-DOI fallbacks: canonical `http(s)` source URL from `schema:url`, then `schema:sameAs`, then the Dataset `@id` when it is an `http(s)` IRI (sanitized for arctrl identifier constraints), then the discovered dataset page URL supplied by the plugin (sanitized: scheme stripped, forbidden characters replaced with `_`, consecutive underscores collapsed).
5. Else mapping MUST fail closed (mapping error; no `HarvestedArc`).

When no colliding-DOI set is supplied (e.g. unit tests mapping an isolated graph), steps 1 is skipped and behaviour MUST match steps 2–5 above.

DOI extraction rules are unchanged: a literal whose value starts with `10.`, or a `PropertyValue` whose `propertyID` is an identifiers.org DOI URI or contains `doi` (case-insensitive) and whose `schema:value` starts with `10.` (optional `https://doi.org/` / `http://doi.org/` / `doi:` prefix MAY be stripped).

#### Scenario: OpenAgrar PropertyValue DOI without Dataset @id

- **WHEN** a Schema.org Dataset graph has no `@id`, `url`, or `sameAs`, and `schema:identifier` is a `PropertyValue` with `propertyID` `https://registry.identifiers.org/registry/doi` and `value` `10.3220/253-2025-42`
- **THEN** `Investigation.identifier` MUST be `10.3220/253-2025-42` and MUST NOT match an rdflib blank-node label

#### Scenario: Two parses of the same payload yield the same identifier

- **WHEN** the same Schema.org JSON-LD payload is parsed into a graph twice and mapped twice
- **THEN** both mappings MUST produce the same `Investigation.identifier`

#### Scenario: OpenAgrar record without DOI uses sanitized source URL

- **WHEN** a Schema.org Dataset graph has no DOI and no `url`/`sameAs`/`http(s)` `@id`, and the discovered page URL is `https://www.openagrar.de/receive/openagrar_mods_00107322`
- **THEN** `Investigation.identifier` MUST be `www_openagrar_de_receive_openagrar_mods_00107322`

#### Scenario: Missing DOI and missing source URL fails mapping

- **WHEN** a Schema.org Dataset graph has no DOI and no `http(s)` `url`/`sameAs`/`@id`, and no discovered page URL is supplied
- **THEN** mapping MUST raise a mapping error, MUST NOT return a `HarvestedArc`, and MUST NOT use `str(subject)` of a blank node as the identifier

#### Scenario: Multiple DOIs pick lexicographic minimum regardless of graph order

- **WHEN** a Schema.org Dataset has two valid DOI identifiers `10.5281/zenodo.15672440` and `10.3220/253-2025-54` (as literals or PropertyValues) in either order in the graph, and no DOI collision context is supplied
- **THEN** `Investigation.identifier` MUST be `10.3220/253-2025-54` on every mapping

#### Scenario: Non-canonical DOIs appear as Alternate Identifier comments

- **WHEN** a Schema.org Dataset has canonical DOI `10.3220/253-2025-54` and alternate DOI `10.5281/zenodo.15672440` and no DOI collision context is supplied
- **THEN** the mapped ARC MUST contain an Investigation Comment named `Alternate Identifier` with value `10.5281/zenodo.15672440`, and MUST NOT use the alternate DOI as `Investigation.identifier`

#### Scenario: Single DOI behaviour unchanged

- **WHEN** a Schema.org Dataset has exactly one valid DOI `10.1234/abc` and no DOI collision context is supplied
- **THEN** `Investigation.identifier` MUST be `10.1234/abc` and MUST NOT add an `Alternate Identifier` Comment for that same DOI

#### Scenario: DOI collision uses OpenAgrar RDI id instead of shared DOI

- **WHEN** two Schema.org Dataset graphs from different Receive-URLs both contain DOI `10.1594/PANGAEA.957630`, and mapping context includes that DOI in the colliding-DOI set, and one graph's `source_url` is `https://www.openagrar.de/receive/openagrar_mods_00088718`
- **THEN** that mapping MUST set `Investigation.identifier` to `openagrar_mods_00088718` and MUST NOT use `10.1594/PANGAEA.957630` as `Investigation.identifier`

#### Scenario: DOI collision pages get distinct identifiers

- **WHEN** two OpenAgrar pages share DOI `10.1594/PANGAEA.957630` with Receive-URLs `…/openagrar_mods_00088718` and `…/openagrar_mods_00109919`, and both are mapped with the colliding-DOI set containing that DOI
- **THEN** the two mappings MUST produce different `Investigation.identifier` values (`openagrar_mods_00088718` and `openagrar_mods_00109919`)
