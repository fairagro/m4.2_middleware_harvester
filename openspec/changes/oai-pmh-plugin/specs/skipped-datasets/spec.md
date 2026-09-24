## ADDED Requirements

### Requirement: oai_pmh yields SkippedRecord for deleted OAI records

The OAI-PMH plugin MUST yield `SkippedRecord` (not `HarvesterError`) when an OAI record header indicates
`status="deleted"`. The skip reason MUST identify deletion; the optional URL/identifier SHOULD carry the OAI identifier
when available. Propagation of deletions to the Middleware API (tombstone/delete) is out of scope for this requirement.

#### Scenario: Deleted header is skipped

- **WHEN** ListRecords returns a record whose header is marked deleted
- **THEN** the plugin yields `SkippedRecord` and does not invoke the PayloadParser or DataMapper for that record
