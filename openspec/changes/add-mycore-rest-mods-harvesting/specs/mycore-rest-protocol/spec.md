## Purpose

Generic-plugin Protocol that discovers published objects of a MyCoRe repository from its REST v2 object list and yields
one URL discovery unit per object, so records are fetched from the REST API instead of rendered record pages.

## ADDED Requirements

### Requirement: Register a mycore_rest Protocol

The system SHALL register a Protocol under type key `mycore_rest`. Its canonical configuration SHALL be nested
`generic.protocol.mycore_rest` with `entry_url` (a MyCoRe REST v2 object-list URL such as `https://host/api/v2/objects`,
optionally carrying operator filter parameters like repeated `category`) and `page_size` (positive integer, default
defined in the config model). The Protocol MUST NOT hard-code any repository host, path prefix beyond the `objects`
resource, or category filter.

#### Scenario: mycore_rest resolves from the registry

- **WHEN** a generic repository sets nested `protocol.mycore_rest.entry_url`
- **THEN** configuration validation succeeds and the generic plugin constructs the MyCoRe REST Protocol with those
  settings

#### Scenario: Operator filters are preserved

- **WHEN** `entry_url` is `https://host/api/v2/objects?category=mir_genres:research_data&category=state:published`
- **THEN** every list request carries both `category` parameters unchanged

### Requirement: Page through the object list with after_id

The Protocol SHALL request the object list with `limit` set to `page_size` and SHALL request each following page with
`after_id` set to the last object id of the previous page. Pagination parameters (`limit`, `after_id`, `offset`) SHALL
be owned by the software: values already present on `entry_url` MUST be ignored. Pagination SHALL stop when a page
returns fewer than `page_size` objects or no objects; it MUST NOT request a page after an empty one.

#### Scenario: Two pages

- **WHEN** `page_size` is 2 and the list holds 3 objects
- **THEN** the Protocol issues a first request with `limit=2`, a second with `limit=2&after_id=<second id>`, yields 3
  units and issues no third request

#### Scenario: Operator paging parameters are ignored

- **WHEN** `entry_url` contains `offset=100` or `after_id=x`
- **THEN** the first request carries neither value

### Requirement: Yield landing URL identity with REST fetch URL

For each `mycoreobject` element with a non-empty `id` attribute, the Protocol SHALL yield a URL discovery unit whose
`identifier`/`url` is the landing page `{scheme}://{host}{context}/receive/{id}`, whose `harvest_source_id` is the
object `id`, and whose fetch URL is the REST object resource `{entry_url path}/{id}` on the same scheme and host without
the list query. `{context}` is the path before `/api/v2/objects` in `entry_url` (empty for a root deployment).

#### Scenario: OpenAgrar object

- **WHEN** `entry_url` is `https://www.openagrar.de/api/v2/objects?category=state:published` and the list contains
  `<mycoreobject id="openagrar_mods_00021925"/>`
- **THEN** the unit has url `https://www.openagrar.de/receive/openagrar_mods_00021925`, `harvest_source_id`
  `openagrar_mods_00021925` and fetch URL `https://www.openagrar.de/api/v2/objects/openagrar_mods_00021925`

#### Scenario: Landing identity matches mycore_solr

- **WHEN** the same object is discovered by `mycore_solr` and by `mycore_rest` on the same repository
- **THEN** both units have the same `identifier` and `harvest_source_id`

### Requirement: Report the expected count from X-Total-Count

The Protocol SHALL return the integer value of the first list response's `X-Total-Count` header as expected count, and
SHALL return no count when the header is absent or not a non-negative integer. The first page fetched for the count
SHALL be reused by discovery in the same Protocol instance instead of being requested again.

#### Scenario: Count from header

- **WHEN** the first list response carries `X-Total-Count: 933`
- **THEN** `get_expected_count()` returns 933

#### Scenario: Header missing

- **WHEN** the first list response carries no `X-Total-Count`
- **THEN** `get_expected_count()` returns no count and discovery still runs

### Requirement: Fail closed on unusable list responses

The Protocol SHALL parse list responses with the shared safe XML parsing (no entity expansion, DTD loading, or network
access). A body that is not well-formed XML, or whose root is not `mycoreobjects`, MUST fail discovery with a
generic-protocol error. HTTP and transport errors MUST propagate unchanged for the generic plugin to wrap. A
`mycoreobject` element without a non-empty `id` MUST yield a `RecordProcessingError` without stopping discovery.

#### Scenario: Wrong root element

- **WHEN** the list response root is `html`
- **THEN** discovery fails with a generic-protocol error naming the expected `mycoreobjects` root

#### Scenario: Object without id

- **WHEN** one `mycoreobject` element has no `id` attribute
- **THEN** a `RecordProcessingError` is yielded for it and the remaining objects are still discovered

#### Scenario: Entity declarations are not expanded

- **WHEN** a list response declares and references an internal entity
- **THEN** discovery fails closed or treats the entity as unresolved, and never yields expanded entity text as an id
