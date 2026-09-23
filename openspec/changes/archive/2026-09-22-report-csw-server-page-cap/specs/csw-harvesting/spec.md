# CSW Harvesting

## ADDED Requirements

### Requirement: Warn when the server's advertised MaxRecordDefault is below the configured page size

The system SHALL inspect the `MaxRecordDefault` constraint from the CSW `GetCapabilities` response
after connecting, and SHALL log a warning naming both the advertised cap and the configured
`chunk_size` when the advertised cap is lower. The system SHALL continue to send the configured
`chunk_size` as `maxRecords` without clamping it, and SHALL stay silent when the constraint is
absent or not a positive integer.

#### Scenario: Server advertises a cap below the configured chunk_size

- **WHEN** the endpoint advertises `MaxRecordDefault = 10` and `chunk_size` is 50
- **THEN** log one warning at connect naming both 10 and 50
- **AND** still request `maxRecords=50` per page
- **AND** still harvest every record, paginating on the response's `nextrecord` / `returned`

#### Scenario: Server advertises a cap at or above the configured chunk_size

- **WHEN** the endpoint advertises `MaxRecordDefault = 100` and `chunk_size` is 50
- **THEN** log no page-cap warning

#### Scenario: Constraint is absent or unparsable

- **WHEN** `GetCapabilities` omits `MaxRecordDefault`, or advertises a non-numeric or non-positive
  value
- **THEN** log no page-cap warning
- **AND** connect successfully
