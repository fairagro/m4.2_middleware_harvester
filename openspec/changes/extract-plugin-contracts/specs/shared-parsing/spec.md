# Spec Delta

## MODIFIED Requirements

### Requirement: parsing may depend on harvester and payload

The `middleware.parsing` package MAY depend on `middleware.contracts` (for polite HTTP client types and shared harvest
error bases) and on `middleware.payload` (for `PayloadKind`, `ParsedPayload`, and related contracts). It MUST NOT depend
on `middleware.harvester` or on protocol plugin packages (`inspire`, `linked_data`, `generic`, `oai_pmh`, …).

#### Scenario: Dependency direction

- **WHEN** module dependencies are reviewed
- **THEN** `parsing` may import `contracts` and `payload`, and does not import `harvester` or protocol plugin packages
