## Purpose

Discover published MyCoRe repository objects via the REST `api/v2/objects` list API and yield one URL discovery unit per
object for subsequent MODS parsing — without Solr or HTML `/receive/` pages.

## ADDED Requirements

### Requirement: Register a mycore_rest Protocol

The system SHALL register a generic `Protocol` under type key `mycore_rest` whose entry point is nested
`generic.protocol.mycore_rest.entry_url`. The protocol MUST discover object ids from MyCoRe REST list responses and MUST
NOT query Solr (`/servlets/solr/`) or construct `/receive/{id}` record URLs.

#### Scenario: mycore_rest resolves from the registry

- **WHEN** a generic repository sets nested `protocol.mycore_rest.entry_url`
- **THEN** config validation and protocol construction resolve the MyCoRe REST Protocol

#### Scenario: Record URLs are REST object URLs

- **WHEN** discovery yields a unit for object id `openagrar_mods_00021925`
- **THEN** the discovery identifier / URL targets the REST object resource under `/api/v2/objects/…`, not `/receive/…`

### Requirement: List paging via after_id

The Protocol SHALL page the list endpoint using MyCoRe REST semantics (`after_id` and/or `offset` as designed) until the
page is empty or shorter than the configured page size. Requests MUST go through `NiceHttpClient` (rate limiting /
retries). Default `respect_robots_txt` behaviour of the shared client MUST remain available to operators (no forced
`false` in protocol code).

#### Scenario: Short or empty page stops pagination

- **WHEN** a list page returns no further `mycoreobject` entries (or fewer than the page size when that is the stop
  rule)
- **THEN** discovery ends without further list requests

#### Scenario: Operator category filter preserved

- **WHEN** `entry_url` includes category query parameters (e.g. `mir_genres:research_data`, `state:published`)
- **THEN** those parameters are forwarded on each list request

### Requirement: Yield UrlDiscoveryResult per mycoreobject id

Each list entry with a non-empty `id` SHALL yield a `UrlDiscoveryResult` (or equivalent URL discovery unit) for the
corresponding REST object URL. Entries without a usable id SHALL yield a record-level error and discovery MUST continue.

#### Scenario: Missing id is a record error

- **WHEN** a list element lacks a usable `id`
- **THEN** a `RecordProcessingError` (or subclass) is yielded and remaining entries are still processed

### Requirement: Optional expected count from X-Total-Count

When the list response exposes `X-Total-Count` (or an equivalent documented total), the system SHALL return that integer
from `get_expected_count`; otherwise `get_expected_count` MUST return `None`.

#### Scenario: Header total surfaces expected count

- **WHEN** the first list response includes `X-Total-Count: 933`
- **THEN** `get_expected_count` returns `933`
