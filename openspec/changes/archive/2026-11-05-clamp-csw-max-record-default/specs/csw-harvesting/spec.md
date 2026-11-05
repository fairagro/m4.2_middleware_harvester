# Spec Delta

## REMOVED Requirements

### Requirement: Warn when the server's advertised MaxRecordDefault is below the configured page size

**Reason**: Operators prefer clamping the request page size down to the advertised `MaxRecordDefault` (and a single
INFO) over warn-without-clamp; silent page caps on servers such as Thünen/pycsw made the larger `maxRecords` inert
(#568).

**Migration**: Effective page size is now clamped when a positive advert is below it; see the ADDED requirement. No
config flag restores the old warn-only path.

## ADDED Requirements

### Requirement: Clamp request page size to advertised MaxRecordDefault when lower

The system SHALL inspect the `MaxRecordDefault` constraint from the CSW `GetCapabilities` response after connecting.
When the advertised value is a positive integer **below** the effective page size for subsequent GetRecords paging, the
system SHALL use the advertised value as `maxRecords` (clamp down only; never raise the configured size when the advert
is higher). The effective page size is config `chunk_size`, or — for `xml_query` — a valid XML root `maxRecords` (> 0)
when that override applies; the clamp SHALL apply after that override is resolved. The system SHALL log at most one INFO
naming both the advertised value and the pre-clamp page size when a clamp occurs, SHALL NOT emit a WARNING for this
mismatch, and SHALL stay silent when the constraint is absent or not a positive integer.

#### Scenario: Server advertises a cap below the configured chunk_size

- **WHEN** the endpoint advertises `MaxRecordDefault = 10` and `chunk_size` is 50
- **THEN** request `maxRecords=10` per page for subsequent GetRecords paging
- **AND** log one INFO at connect naming both 10 and 50 and that the page size was clamped
- **AND** still harvest every record, paginating on the response's `nextrecord` / `returned`

#### Scenario: XML maxRecords above the advert is also clamped

- **WHEN** the endpoint advertises `MaxRecordDefault = 10` and `xml_query` specifies `maxRecords="50"`
- **THEN** each page requests `maxRecords=10`
- **AND** at most one INFO describes the clamp

#### Scenario: Effective page size already at or below the advert

- **WHEN** the endpoint advertises `MaxRecordDefault = 100` and `chunk_size` is 50
- **THEN** request `maxRecords=50` per page
- **AND** log no page-cap clamp message

#### Scenario: XML maxRecords already below the advert

- **WHEN** the endpoint advertises `MaxRecordDefault = 10` and `xml_query` specifies `maxRecords="7"`
- **THEN** each page requests `maxRecords=7`
- **AND** log no page-cap clamp message

#### Scenario: Constraint is absent or unparsable

- **WHEN** `GetCapabilities` omits `MaxRecordDefault`, or advertises a non-numeric or non-positive value
- **THEN** use the configured effective page size without clamping
- **AND** log no page-cap clamp message
- **AND** connect successfully
