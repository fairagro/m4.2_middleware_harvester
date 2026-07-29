# Plugin Execution

## Purpose

Exposes an asynchronous generator that iterates over CSW records and yields serialized ARCs. As a plugin, it must not execute standalone (no `main()` function) and relies on the global Harvester for API interactions.

## Requirements

### Requirement: Implement InspirePlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
The system SHALL ensure that implement `InspirePlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface.

#### Scenario: Satisfies — Implement InspirePlugin(Plugin) in plugin.py; the central Harvester instantiates it with…
- **WHEN** the conditions described by this requirement apply
- **THEN** Implement `InspirePlugin(Plugin)` in `plugin.py`; the central Harvester instantiates it with the plugin config and invokes `run()` and `get_expected_datasets()` via the `Plugin` interface

### Requirement: Use the CSWClient class to communicate with the CSW endpoint…
The system SHALL ensure that use the `CSWClient` class to communicate with the CSW endpoint and fetch all available metadata records iteratively.

#### Scenario: Satisfies — Use the CSWClient class to communicate with the CSW endpoint…
- **WHEN** the conditions described by this requirement apply
- **THEN** Use the `CSWClient` class to communicate with the CSW endpoint and fetch all available metadata records iteratively

### Requirement: Skip any record whose hierarchy is not a valid data…
The system SHALL ensure that skip any record whose `hierarchy` is not a valid data type (i.e., not within `["dataset", "series", "nongeographicdataset"]`).

#### Scenario: Satisfies — Skip any record whose hierarchy is not a valid data…
- **WHEN** the conditions described by this requirement apply
- **THEN** Skip any record whose `hierarchy` is not a valid data type (i.e., not within `["dataset", "series", "nongeographicdataset"]`)

### Requirement: Use the InspireMapper class to transform each valid parsed record…
The system SHALL ensure that use the `InspireMapper` class to transform each valid parsed record into an ARC object.

#### Scenario: Satisfies — Use the InspireMapper class to transform each valid parsed record…
- **WHEN** the conditions described by this requirement apply
- **THEN** Use the `InspireMapper` class to transform each valid parsed record into an ARC object

### Requirement: Serialize each ARC via arc.ToROCrateJsonString() and yield the resulting JSON…
The system SHALL ensure that serialize each ARC via `arc.ToROCrateJsonString()` and `yield` the resulting JSON string to the calling Harvester.

#### Scenario: Satisfies — Serialize each ARC via arc.ToROCrateJsonString() and yield the resulting JSON…
- **WHEN** the conditions described by this requirement apply
- **THEN** Serialize each ARC via `arc.ToROCrateJsonString()` and `yield` the resulting JSON string to the calling Harvester

### Requirement: Do not include a main() function, argument parsing, or ApiClient…
The system SHALL ensure that do not include a `main()` function, argument parsing, or `ApiClient` upload logic.

#### Scenario: Satisfies — Do not include a main() function, argument parsing, or ApiClient…
- **WHEN** the conditions described by this requirement apply
- **THEN** Do not include a `main()` function, argument parsing, or `ApiClient` upload logic
