## ADDED Requirements

### Requirement: Regal Person contacts MUST satisfy given-name rules

`RegalMapper` MUST apply the `person-contact-given-name` rules to contacts
derived from `dcterms:creator` / `dcterms:contributor` (literal or labelled
nodes). A `skos:prefLabel` without `", "` that yields an empty given name MUST
NOT produce a Person contact with empty first name; such a contact MUST cause
fail-closed mapping failure for that record unless the node is treated as an
organization and represented via Comment / Affiliation instead of Person.

Authoritative field tables remain in [docs/regal_mapping.md](../../../../docs/regal_mapping.md);
this requirement overrides any reading that allows empty FirstName on contacts.

#### Scenario: Comma-split prefLabel with given name succeeds

- **WHEN** a creator node has `prefLabel` `Fuerst, Julia`
- **THEN** the mapper MUST emit a Person with LastName `Fuerst` and FirstName
  `Julia`

#### Scenario: Org-style prefLabel without given name is not an empty-given Person

- **WHEN** a creator or contributor node has a `prefLabel` with no `", "`
  separator (entire label would become LastName with empty FirstName), and the
  node represents an organization/institution rather than a parseable person
- **THEN** the mapper MUST NOT append a Person with empty FirstName; it MUST
  either represent the agent via Investigation comment / Affiliation or fail
  closed per `person-contact-given-name`

#### Scenario: Person-like label without given name fails closed

- **WHEN** a creator would map to a Person with empty FirstName and is not
  represented as an organization comment/affiliation instead
- **THEN** `map_graph` MUST raise a mapping error and MUST NOT return a
  HarvestedArc
