## ADDED Requirements

### Requirement: Dispatch oai_pmh plugin via registry

The system SHALL look up the `oai_pmh` plugin type in the plugin factory/registry, instantiate the corresponding Plugin
implementation with the repository’s `oai_pmh` config (and mapper config as required), and consume its harvest
AsyncGenerator like any other plugin.

#### Scenario: oai_pmh repository is invoked

- **WHEN** configuration contains a repository with plugin key `oai_pmh`
- **THEN** the orchestrator runs that plugin and processes its yields for upload and reporting
