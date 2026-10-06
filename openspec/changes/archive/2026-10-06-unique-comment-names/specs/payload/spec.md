## ADDED Requirements

### Requirement: Harvested ARCs MUST have unique Comment names

`HarvestedArc.from_arctrl` MUST merge Comments with the same name on the Investigation, each Study, each Assay, each
Person (Investigation and Study contacts, Assay performers) and each Publication into the first such Comment, with the
distinct non-empty values joined by `; ` in order. The serialized RO-Crate MUST keep the root `dateModified` and MUST
NOT contain the `dateModified` Comment node or references to it. Reading the RO-Crate with
`ARC.from_rocrate_json_string` and writing it with `ARC.Write` MUST succeed.

#### Scenario: Repeated Regal facet

- **WHEN** an Investigation has Comments `associatedDataset` "frl:1" and `associatedDataset` "frl:2"
- **THEN** it MUST have one Comment `associatedDataset` "frl:1; frl:2"

#### Scenario: API read and write

- **WHEN** a harvested ARC with repeated Comment names and a `dateModified` is read back and written with `ARC.Write`
- **THEN** the write MUST succeed and the Investigation MUST have exactly one `dateModified` Comment
