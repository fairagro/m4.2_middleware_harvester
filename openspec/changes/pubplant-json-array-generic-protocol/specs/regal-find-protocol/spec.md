# Regal /find Protocol

## Purpose

Generic-plugin `Protocol` that discovers Regal records from an offset-paginated `/find` JSON array endpoint (e.g.
PUBLISSO FRL). It is the generic counterpart of the `linked_data` `regal_find` sitemap (#294 protocol half). The
`regal_jsonld` payload parser is out of scope here.

## ADDED Requirements

### Requirement: JSON array Protocols share one base

`pubplant_json_array` and `regal_find` SHALL both derive from a shared `JsonArrayProtocol` base. The base owns JSON array
validation, per-element failure reporting and inline `JsonLdDiscoveryResult` yielding. Subclasses provide only the page
source (`_pages`) and the record identity (`_record_identifier`).

#### Scenario: Both protocols use the base

- **WHEN** the registry resolves `pubplant_json_array` or `regal_find`
- **THEN** the resolved class is a `JsonArrayProtocol` subclass

#### Scenario: Non-object element

- **WHEN** an array element is not a JSON object
- **THEN** a `RecordProcessingError` with record id `<prefix>:[<page position>:]index=<n>` is yielded and discovery
  continues

### Requirement: Register a regal_find Protocol

The system SHALL register a `Protocol` under `ProtocolType.regal_find` (`generic.protocol_type: regal_find`) whose entry
point is `generic.sitemap_url`. The `linked_data` `regal_find` sitemap SHALL delegate to it, so existing `linked_data`
configurations keep working with unchanged behaviour.

#### Scenario: regal_find resolves from the registry

- **WHEN** a generic repository sets `protocol_type: regal_find`
- **THEN** config validation and `GenericPlugin.create_protocol` resolve the Regal /find Protocol

### Requirement: Offset pagination with a software-owned query contract

The Protocol SHALL request `sitemap_url` with `format=json`, `from=<offset>` and `until=<page size>` always set by the
software. The page size SHALL be the URL `until` when it is a valid positive integer, otherwise `generic.page_size`. `q`
SHALL default to `contentType:researchData` unless the operator supplies it, and other operator parameters SHALL be
forwarded. Discovery SHALL advance `from` by the page length and stop on an empty page or one shorter than the page
size.

#### Scenario: Short page stops pagination

- **WHEN** the second page holds fewer records than the page size
- **THEN** no further request is made

#### Scenario: Operator overrides

- **WHEN** `sitemap_url` carries `q`, `sort`, `from`, `format` and `until`
- **THEN** `q` and `sort` are forwarded, `until` sets the page size, and `from`/`format` are replaced by software values

### Requirement: Regal @id is the discovery identity

Each object record SHALL be yielded with its trimmed `@id` as `identifier` and no `harvest_source_id`. A record without
a non-empty string `@id` SHALL yield a `RecordProcessingError` (`regal_find:from=<offset>:index=<n>`); DOI is never used
as identity. A non-array response SHALL fail with `GenericProtocolError`, and the expected count SHALL be `None`.

#### Scenario: Missing @id

- **WHEN** a record carries only a `doi`
- **THEN** a `RecordProcessingError` naming the missing `@id` is yielded
