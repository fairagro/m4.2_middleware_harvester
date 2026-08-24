## ADDED Requirements

### Requirement: Schema.org mapping MUST be harvest-deterministic for keywords, multi-literals, and contacts

`GeneralSchemaOrgMapper` MUST produce identical Investigation keyword comments / keyword protocol values, description text, Contact order, and Publication author strings when the logical RDF payload is unchanged — including when rdflib object iteration order differs between parses. The mapper MUST NOT rely on `graph.value` or unsorted `graph.objects` for these fields when multiple values exist.

Keyword literals MUST be trimmed and sorted with a documented stable Unicode policy before joining. When multiple Literals exist for a string predicate (at least `description`; preferably also `name` / other `_str` call sites), selection MUST drop empty values and prefer language tags in order `en`, then `de`, then untagged / other, with deterministic length-then-lexicographic tie-breaks. Creator, author, and contributor nodes MUST be sorted by a stable key (family name, given name, display name, node IRI) before Contacts are appended.

Publication author strings built from those Contacts MUST use the form `F. Last` (given-name initial, space, family name) joined with `"; "`, and MUST NOT use comma-separated `Last, F.` forms that ARCtrl splits into unstable `#Author_*` nodes.

#### Scenario: Same keywords, different RDF object order

- **WHEN** a Schema.org Dataset has the same keyword literal set presented in two different object orders
- **THEN** both mappings MUST produce the same Keywords comment text, the same joined keyword protocol value, and the same derived Keywords Comment / ParameterValue `@id`s

#### Scenario: Multi-language description with empty literal

- **WHEN** a Dataset has an empty description literal plus language-tagged `en` and `de` descriptions
- **THEN** mapping MUST select the same non-empty description on every run (preferring `en` over `de`)

#### Scenario: Same creators, different triple order

- **WHEN** the same creator/author set is present in different `graph.objects` iteration orders
- **THEN** Contact order and the Publication authors string MUST be identical across mappings

#### Scenario: Publication authors use initial-space-last form without commas

- **WHEN** a Dataset has creators Ada Lovelace and Zed Zebra (after stable Contact sort)
- **THEN** the Publication authors string / derived `#Author_*` `@id` MUST be `A. Lovelace; Z. Zebra` (or an `@id` containing that string) and MUST NOT contain a `Last, F.` comma form

#### Scenario: Double map of the same fixture graph

- **WHEN** the same Schema.org fixture graph is mapped twice
- **THEN** description, Keywords comments, Contact order, and Publication authors MUST match between the two results
