## ADDED Requirements

### Requirement: Optional mapper overlay selected by an explicit config key

The Linked Data plugin `Config` SHALL provide an optional `mapper` field naming a per-RDI mapper overlay. `payload_type`
SHALL continue to name the **payload format** only; repository identity SHALL NOT be encoded into `PayloadType` values
(protocol ≠ payload format, see `#140`).

When `mapper` is unset, mapper resolution SHALL use the `payload_type` registry exactly as before, so existing
repository configs keep their behaviour without edits. When `mapper` is set, resolution SHALL use the overlay registry
keyed by that name.

Each overlay SHALL declare the payload format it builds on. The plugin SHALL fail fast at construction when the
configured `mapper` is unknown, or when the overlay's declared base does not match the configured `payload_type`.
Overlay selection SHALL remain explicit: the system SHALL NOT infer an overlay from the sitemap URL, host name, or any
other source characteristic.

#### Scenario: Config without mapper resolves the payload_type mapper

- **WHEN** a repository config sets `payload_type: schema_org_general` and omits `mapper`
- **THEN** the plugin MUST construct the mapper registered for that payload type, with no behaviour change from before
  the `mapper` field existed

#### Scenario: Config with mapper resolves the overlay

- **WHEN** a repository config sets `payload_type: schema_org_general` and `mapper: openagrar`
- **THEN** the plugin MUST construct the overlay registered under `openagrar`

#### Scenario: Unknown mapper fails fast

- **WHEN** a repository config names a `mapper` that is not registered
- **THEN** plugin construction MUST raise a configuration error naming the unsupported mapper, and MUST NOT silently
  fall back to the base mapper

#### Scenario: Mapper incompatible with payload_type fails fast

- **WHEN** a repository config pairs `mapper: openagrar` with a `payload_type` that is not the payload format the
  overlay builds on
- **THEN** plugin construction MUST raise a configuration error naming both values, and MUST NOT map records with a
  mismatched overlay
