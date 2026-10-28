# Spec Delta

## ADDED Requirements

### Requirement: Repository-level errors fail the API harvest

When a plugin yields a `HarvesterError` that is not a `RecordProcessingError` for a repository, the system MUST end that
repository's API harvest as FAILED, not COMPLETED, whether or not ARCs were submitted before the error. ARCs the API
accepted before the error MUST still be recorded as harvested, and the repository scope MUST hold exactly one repository
issue for the plugin's error (no additional upload-aborted issue). The system MUST log the failure at ERROR with the RDI
and the reason, and with the harvest id when the API client reports it, and other repositories MUST continue.
Record-level errors alone MUST NOT fail the harvest.

#### Scenario: Repository error with no ARCs submitted

- **GIVEN** a plugin yields a repository-level `HarvesterError` and no ARCs
- **WHEN** the plugin stream ends
- **THEN** the API harvest is FAILED and not completed, so the RDI catalog is not finalized

#### Scenario: Repository error after ARCs were submitted

- **GIVEN** a plugin yields two ARCs and then a repository-level `HarvesterError`
- **WHEN** the plugin stream ends
- **THEN** the API harvest is FAILED, `harvested_datasets` is 2 and the scope holds one repository issue

#### Scenario: Record-level errors only

- **GIVEN** a plugin yields one ARC and one `RecordProcessingError`
- **WHEN** the plugin stream ends
- **THEN** the API harvest is COMPLETED and `failed_datasets` is 1

#### Scenario: Failure is logged and other repositories continue

- **GIVEN** two repositories where the first yields a repository-level `HarvesterError`
- **WHEN** the harvester runs
- **THEN** an ERROR log names the first RDI and the reason, and the second repository's harvest is COMPLETED
