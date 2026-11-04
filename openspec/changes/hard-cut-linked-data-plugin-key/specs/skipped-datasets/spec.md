## ADDED Requirements

### Requirement: generic yields SkippedRecord for duplicate discovery

The generic plugin MUST yield `SkippedRecord` (not `HarvesterError`) when Protocol discovery deduplication skips a
duplicate identifier or URL.

#### Scenario: Duplicate discovery id

- **WHEN** the same discovery identity appears more than once in a generic harvest run
- **THEN** subsequent occurrences are yielded as `SkippedRecord` and counted toward `skipped_datasets`

## REMOVED Requirements

### Requirement: linked_data yields SkippedRecord for duplicate discovery

**Reason:** `linked_data` plugin removed (#467); duplicate discovery skips are owned by generic Protocol discovery.

**Migration:** None for operators on `generic:`; behaviour unchanged for migrated repositories.
