# Harvester Orchestration

## Purpose

The central harvester acts as an orchestrator that loads a unified configuration, executes multiple pluggable `xxx_to_arc` components, and publishes the resulting ARCs to the FAIRagro Middleware API.

## Requirements

### Requirement: Load a centralized configuration that inherits from ConfigBase
The system SHALL load a centralized configuration that inherits from `ConfigBase`.

#### Scenario: Satisfies — Load a centralized configuration that inherits from ConfigBase
- **WHEN** the conditions described by this requirement apply
- **THEN** Load a centralized configuration that inherits from `ConfigBase`

### Requirement: Parse a repositories list from the configuration, where each entry…
The system SHALL parse a `repositories` list from the configuration, where each entry contains shared fields (e.g. `rdi`) and exactly one optional plugin field whose name is the plugin type (e.g. `inspire`) and whose value is the plugin-specific configuration object.

#### Scenario: Satisfies — Parse a repositories list from the configuration, where each entry…
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse a `repositories` list from the configuration, where each entry contains shared fields (e.g. `rdi`) and exactly one optional plugin field whose name is the plugin type (e.g. `inspire`) and whose value is the plugin-specific configuration object

### Requirement: Parse api_client settings globally within the harvester configuration, rather than…
The system SHALL parse `api_client` settings globally within the harvester configuration, rather than within localized plugins.

#### Scenario: Satisfies — Parse api_client settings globally within the harvester configuration, rather than…
- **WHEN** the conditions described by this requirement apply
- **THEN** Parse `api_client` settings globally within the harvester configuration, rather than within localized plugins

### Requirement: Instantiate and invoke the appropriate xxx_to_arc plugin by looking up…
The system SHALL instantiate and invoke the appropriate `xxx_to_arc` plugin by looking up the plugin type key in `_PLUGIN_CLASSES`, instantiating the corresponding `Plugin` subclass with the plugin-specific config, and calling `.run()` and `.get_expected_datasets()` via the `Plugin` interface.

#### Scenario: Satisfies — Instantiate and invoke the appropriate xxx_to_arc plugin by looking up…
- **WHEN** the conditions described by this requirement apply
- **THEN** Instantiate and invoke the appropriate `xxx_to_arc` plugin by looking up the plugin type key in `_PLUGIN_CLASSES`, instantiating the corresponding `Plugin` subclass with the plugin-specific config, and calling `.run()` and `.get_expected_datasets()` via the `Plugin` interface

### Requirement: Plugin.run() is an async generator method (declared with async def)…
The system SHALL ensure that `Plugin.run()` is an `async` generator method (declared with `async def`) returning `AsyncGenerator[str | HarvesterError, None]`.

#### Scenario: Satisfies — Plugin.run() is an async generator method (declared with async def)…
- **WHEN** the conditions described by this requirement apply
- **THEN** `Plugin.run()` is an `async` generator method (declared with `async def`) returning `AsyncGenerator[str | HarvesterError, None]`

### Requirement: Plugin.get_expected_datasets() is an async method returning int | None
The system SHALL ensure that `Plugin.get_expected_datasets()` is an `async` method returning `int | None`.

#### Scenario: Satisfies — Plugin.get_expected_datasets() is an async method returning int | None
- **WHEN** the conditions described by this requirement apply
- **THEN** `Plugin.get_expected_datasets()` is an `async` method returning `int | None`

### Requirement: The Plugin base class defines no __init__ method; each concrete…
The `Plugin` base class SHALL define no `__init__` method; each concrete subclass defines its own constructor with its own strongly-typed config parameter.

#### Scenario: Satisfies — The Plugin base class defines no __init__ method; each concrete…
- **WHEN** the conditions described by this requirement apply
- **THEN** The `Plugin` base class defines no `__init__` method; each concrete subclass defines its own constructor with its own strongly-typed config parameter

### Requirement: Consume the output of each plugin via an AsyncGenerator[str |…
The system SHALL consume the output of each plugin via an `AsyncGenerator[str | HarvesterError, None]` that yields either serialized ARC JSON strings or `HarvesterError` instances for record-level failures.

#### Scenario: Satisfies — Consume the output of each plugin via an AsyncGenerator[str |…
- **WHEN** the conditions described by this requirement apply
- **THEN** Consume the output of each plugin via an `AsyncGenerator[str | HarvesterError, None]` that yields either serialized ARC JSON strings or `HarvesterError` instances for record-level failures

### Requirement: Upload the yielded ARCs to the target Remote Data Infrastructure…
The system SHALL upload the yielded ARCs to the target Remote Data Infrastructure (RDI) using the configured `api_client`.

#### Scenario: Satisfies — Upload the yielded ARCs to the target Remote Data Infrastructure…
- **WHEN** the conditions described by this requirement apply
- **THEN** Upload the yielded ARCs to the target Remote Data Infrastructure (RDI) using the configured `api_client`
