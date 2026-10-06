# Spec Delta

## ADDED Requirements

### Requirement: NiceHttpClient lives in middleware.contracts

The system SHALL provide `NiceHttpClient` and `NiceHttpClientConfig` in `middleware.contracts.nice_http_client`.
Protocol plugins and `middleware.parsing` MUST import those types from `middleware.contracts` and MUST NOT import
`middleware.harvester.nice_http_client`.

#### Scenario: Shared HTTP client import path

- **WHEN** a plugin or parser fetches over HTTP with the shared polite client
- **THEN** it constructs `NiceHttpClient` from `middleware.contracts.nice_http_client`
