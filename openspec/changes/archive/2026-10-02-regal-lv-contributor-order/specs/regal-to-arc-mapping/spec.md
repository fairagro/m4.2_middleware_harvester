## MODIFIED Requirements

### Requirement: Regal contributorOrder MUST NOT become an Investigation Comment

The predicates `http://purl.org/lobid/lv#contributorOrder` (`lv:contributorOrder`, what the Publisso context declares,
as `@list`) and `http://hbz-nrw.de/regal#contributorOrder` (`regal:contributorOrder`) MUST be treated as known mapping
metadata and MUST NOT be emitted as an opaque Investigation Comment, whether the value is a literal, an `rdf:List` or a
blank node. `contributorOrder` MUST NOT be used to sort Contacts: in Publisso data it repeats the creator (then
contributor) `@list` order, which Contacts already keep.

#### Scenario: lv:contributorOrder pipe-string does not create a Comment

- **WHEN** a Regal ResearchData graph has `lv:contributorOrder` with a pipe-separated literal of agent IRIs, either
  directly or as the member of a JSON-LD `@list` (real `/find` record `frl:6420709`)
- **THEN** the mapped ARC MUST NOT contain an Investigation Comment named `contributorOrder` or the pipe-string
