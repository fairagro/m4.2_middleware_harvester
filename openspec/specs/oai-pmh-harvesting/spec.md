# OAI-PMH Harvesting

## Purpose

Dedicated OAI-PMH harvest plugin that lists records from an OAI-PMH 2.0 endpoint, converts each record’s metadata via a
shared PayloadParser from `middleware.parsing`, and maps through a shared DataMapper — without registering OAI as a
Generic Protocol type.

## Requirements

### Requirement: Provide an oai_pmh plugin Config as a Pydantic BaseModel

The system SHALL provide a plugin-level `Config` as a Pydantic `BaseModel` under the repository plugin key `oai_pmh`.
The config MUST require an OAI-PMH base endpoint URL and a `metadata_prefix` string. The config MUST accept an optional
`sets` list of OAI `setSpec` strings (default empty). The config MUST expose its own HTTP/retry fields comparable to
polite harvesting needs that the chosen OAI client can honour (at least user agent and request timeout; retries where
supported). The config MUST NOT be a subtype or mapped copy of `NiceHttpClientConfig`; unsupported NiceHttp-only
policies MUST NOT appear as required fields. Shared parser selection MUST use the repository-level `parser:` block (not
a field on the `oai_pmh` plugin config).

#### Scenario: Minimal valid oai_pmh config

- **WHEN** a repository sets `oai_pmh` with endpoint and `metadata_prefix`, plus sibling `parser` and `mapper`
- **THEN** configuration validation succeeds

#### Scenario: metadata_prefix is required

- **WHEN** `oai_pmh` omits `metadata_prefix`
- **THEN** configuration validation fails before harvesting starts

#### Scenario: Parser selected via sibling parser block

- **WHEN** an `oai_pmh` repository is configured with `parser: { type: rdf_xml }`
- **THEN** the PayloadParser implementation is selected from repository `parser.type`

### Requirement: Implement OaiPmhPlugin satisfying the Plugin harvest contract

The system SHALL implement an OAI-PMH plugin that the orchestrator instantiates with plugin config plus repository
`mapper` and `parser` config and invokes via the shared `Plugin` interface (`run()` and `get_expected_datasets()`).
Yields MUST be `HarvestedArc | HarvesterError | SkippedRecord`.

#### Scenario: Orchestrator dispatches oai_pmh repositories

- **WHEN** a repository entry selects `oai_pmh`
- **THEN** the harvester instantiates the OAI-PMH plugin and consumes its AsyncGenerator

### Requirement: Harvest via OAI-PMH ListRecords with resumption

The system SHALL obtain records using OAI-PMH `ListRecords` for the configured endpoint and `metadata_prefix`, following
`resumptionToken` pagination until the list is complete or a terminal OAI/protocol error occurs. The plugin MUST request
exactly one metadata format per `ListRecords` invocation (the configured prefix).

#### Scenario: Paginated ListRecords completes

- **WHEN** the endpoint returns multiple pages linked by resumption tokens
- **THEN** the plugin processes records from all pages before finishing the run for that set scope

### Requirement: Support zero or more OAI sets from config

When `sets` is empty, the system SHALL perform a single unfiltered `ListRecords` harvest (no `set` argument). When
`sets` is non-empty, the system SHALL perform one `ListRecords` harvest per configured `setSpec`, using that value as
the OAI `set` argument. Set membership semantics remain those of the repository (`ListSets`); the harvester MUST NOT
invent set names.

#### Scenario: Empty sets harvests whole repository

- **WHEN** `sets` is empty or omitted (default)
- **THEN** ListRecords is issued without a `set` argument

#### Scenario: Multiple sets run sequentially

- **WHEN** `sets` contains two distinct setSpec values
- **THEN** the plugin completes ListRecords for the first setSpec before starting the second

### Requirement: Compose shared PayloadParser then shared DataMapper

For each non-deleted OAI record with usable metadata, the system SHALL build a `middleware.parsing` discovery unit
carrying a stable identifier (OAI identifier) and the inline `<metadata>` payload, invoke the configured shared
PayloadParser to obtain a `ParsedPayload`, fail closed when `payload.kind` differs from the repository mapper’s
`accepts`, then invoke the shared DataMapper and yield `HarvestedArc` on success. Record-level parse/map failures
(including `ParserError` from `middleware.parsing`) MUST yield `HarvesterError` (or subclass) and MUST NOT abort the
remainder of the harvest.

#### Scenario: Successful record yields HarvestedArc

- **WHEN** ListRecords, parse, kind-check, and map succeed for a record
- **THEN** the plugin yields a `HarvestedArc` for that record

#### Scenario: Kind mismatch fails the record only

- **WHEN** the parser emits a kind the mapper does not accept
- **THEN** the plugin yields a record-level error and continues with remaining records

### Requirement: Apply polite HTTP policies within client limits

The system SHALL apply the plugin’s configured user agent on every OAI HTTP request. The system SHALL apply configured
timeouts and retry settings to the extent the OAI client allows. When configured to respect robots.txt, the system MUST
check the OAI endpoint before harvesting and MUST fail closed or skip the repository run if the endpoint is disallowed.
When a per-host rate limit is configured, the system MUST throttle OAI requests accordingly even if the OAI client has
no built-in limiter.

#### Scenario: Configured user agent is sent

- **WHEN** harvesting runs with a configured user agent string
- **THEN** OAI HTTP requests include that User-Agent value

### Requirement: Expected dataset count may be unknown

`get_expected_datasets()` SHALL return an integer when a reliable complete-list size is available from the OAI
interaction, and SHALL return `None` when it cannot be determined without unacceptable extra cost or risk.

#### Scenario: Unknown count returns None

- **WHEN** complete list size is not available
- **THEN** `get_expected_datasets()` returns `None` and harvesting may still run
