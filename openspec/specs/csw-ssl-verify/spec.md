# CSW SSL Verify

## Purpose

Configures TLS certificate verification for INSPIRE CSW connections so operators can harvest from endpoints with self-signed or privately issued certificates.

## Requirements

### Requirement: Inspire.Config exposes verify_ssl with default True
The system SHALL expose `inspire.Config.verify_ssl` typed as `bool | str` with default `True`. A `bool` SHALL enable (`True`) or disable (`False`) TLS certificate verification. A `str` SHALL be interpreted as a filesystem path to a CA bundle used for verification.

#### Scenario: Default verifies certificates
- **WHEN** `verify_ssl` is omitted from configuration
- **THEN** its value is `True` (system CA verification)

#### Scenario: Boolean disable
- **WHEN** configuration sets `verify_ssl: false`
- **THEN** `inspire.Config.verify_ssl` is `False`

#### Scenario: Custom CA path
- **WHEN** configuration sets `verify_ssl` to a string path
- **THEN** `inspire.Config.verify_ssl` holds that path string

#### Scenario: Boolean-like strings coerce to bool
- **WHEN** configuration sets `verify_ssl` to a boolean-like string such as `"false"` or `"true"` (quoted YAML or environment variable)
- **THEN** `inspire.Config.verify_ssl` is the corresponding `bool` (`False` / `True`), not a CA-bundle path string

### Requirement: CSWClient.connect forwards verify_ssl to CatalogueServiceWeb via Authentication
The system SHALL ensure that `CSWClient.connect()` (and its underlying connection setup) constructs `CatalogueServiceWeb` with `auth=Authentication(verify=config.verify_ssl)` so the configured verification setting applies to all subsequent OWSLib CSW HTTP requests for that client.

#### Scenario: Default auth verify is True
- **WHEN** connecting with the default `verify_ssl` value
- **THEN** `CatalogueServiceWeb` is constructed with an `Authentication` whose `verify` is `True`

#### Scenario: Disabled verification is forwarded
- **WHEN** connecting with `verify_ssl` set to `False`
- **THEN** `CatalogueServiceWeb` is constructed with an `Authentication` whose `verify` is `False`

#### Scenario: CA path is forwarded
- **WHEN** connecting with `verify_ssl` set to a CA bundle path string
- **THEN** `CatalogueServiceWeb` is constructed with an `Authentication` whose `verify` equals that path

### Requirement: Disabling certificate verification is logged as a warning
The system SHALL log a WARNING when connecting with `verify_ssl` set to `False`, stating that TLS certificate verification is disabled for the CSW endpoint.

#### Scenario: Warning on disable
- **WHEN** `CSWClient` connects with `verify_ssl` equal to `False`
- **THEN** a WARNING log message is emitted that mentions disabled TLS certificate verification
