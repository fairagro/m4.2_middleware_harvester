# Proposal

## Why

ISO 19115-2 `MI_AcquisitionInformation` (platform / instrument) is available via OWSLib on `MD_Metadata.acquisition` but
never reaches `InspireRecord` or ARC. Assay `TechnologyPlatform` stays a hardcoded label, and remote-sensing metadata is
lost. Issue #36; lock-in **A**: extract a slim acquisition model and emit a parameter-only Assay protocol when data
exists — without inventing IO columns or changing TechnologyPlatform (#441).

## What Changes

- Extend `InspireRecord` with `acquisition_information` (platforms with optional identifier/description; nested
  instruments with optional identifier/type), under existing value-bounds.
- `IsoParser` reads OWSLib `iso.acquisition` (`MI_AcquisitionInformation`); omit empty platforms/instruments; absent
  acquisition → field default empty/absent.
- `InspireMapper` adds Assay protocol table **"Sensor Acquisition"** with parameters only (e.g. Platform, Instrument)
  when at least one non-empty parameter exists; otherwise returns `None` / skips the table. No invented Input/Output
  columns. Do **not** change hardcoded `TechnologyPlatform`.
- Update `docs/mappers/inspire.md` MD_Acquisition / Assay sections to match.
- Unit tests: parse with/without acquisition; protocol present/absent.

### Non-goals

- Replacing hardcoded `TechnologyPlatform` with live platform names (#441 / option B).
- Invented protocol IO (“Study Area”, “Raw Sensor Data”) — conflicts with no-invent-data rules.
- Duplicating Temporal Extent into this protocol (stays on Study “Data Acquisition”).
- Full MI operation/event/contentInfo mapping.
- Claiming extraction lives in `CSWClient` (parser owns ISO→record).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `csw-harvesting`: IsoParser MUST populate `InspireRecord.acquisition_information` from OWSLib
  `MD_Metadata.acquisition` when present.
- `inspire-to-arc-mapping`: InspireMapper MUST emit Assay protocol “Sensor Acquisition” (parameters only) when
  acquisition terms yield at least one parameter; MUST omit it when absent; MUST NOT invent IO; docs MUST match.
  TechnologyPlatform behaviour unchanged in this change.

## Impact

- Code: `middleware/payload/.../inspire/models.py`, `middleware/inspire/.../iso_parser.py`,
  `middleware/payload/.../inspire/mapper.py`, unit tests, `docs/mappers/inspire.md`.
- Related: #36; TechnologyPlatform follow-up remains #441.
- Harvest value depends on source CSW actually shipping `gmi:acquisitionInformation` (no in-repo fixtures today).
