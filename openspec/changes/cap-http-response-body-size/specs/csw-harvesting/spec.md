## ADDED Requirements

### Requirement: CSW response body size limiting is out of scope without owned HTTP transport

The system SHALL NOT claim HTTP response body size limiting for the INSPIRE CSW / OWSLib path in this change. OWSLib
uses `requests` without a harvester-owned session (CSW HTTP pooling deferred — see related work on #355). Body-size
limiting for CSW MUST wait until the harvester owns the CSW HTTP transport, or a separate follow-up must document an
alternative. Value bounds on parsed `InspireRecord` remain unchanged and do not replace transport-level body caps.

#### Scenario: Spec does not require CSW body cap yet

- **WHEN** operators configure INSPIRE CSW harvesting
- **THEN** this capability does not require `max_response_body_bytes` enforcement on OWSLib GetRecords responses
