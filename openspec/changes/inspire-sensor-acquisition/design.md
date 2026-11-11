# Design

## Context

See proposal.md — Why. OWSLib already parses `gmi:acquisitionInformation` into `MI_AcquisitionInformation` with
`platforms[]` → `MI_Platform` (`identifier`, `description`, `instruments[]` → `MI_Instrument` `identifier`/`type`).
Mapper today ignores it; Assay `TechnologyPlatform` is hardcoded. Study “Data Acquisition” already owns temporal extent.

## Goals / Non-Goals

**Goals:**

- Persist slim acquisition platforms/instruments on `InspireRecord`.
- Emit Assay protocol `Sensor Acquisition` with Platform/Instrument parameters when present.
- Keep docs aligned; preserve no-invent-IO and hardcoded TechnologyPlatform.

**Non-Goals:**

- TechnologyPlatform from live platform (#441).
- Operation/event/contentInfo.
- Temporal fields on this protocol.

## Decisions

1. **Nested model** — `AcquisitionInformation` → `platforms: list[AcquisitionPlatform]` → optional
   `identifier`/`description` + `instruments: list[AcquisitionInstrument]` (`identifier`/`instrument_type` for OWSLib
   `type`). Avoid Python attribute `type` clash.
2. **Parser in IsoParser** — Not CSWClient; same as keywords. Skip blank strings / placeholder-aware via existing nested
   `_HarvestedModel` optional-field drop.
3. **Assay protocol, parameters only** — Matches `docs/mappers/inspire.md` proposed Assay protocol; no Study Area / Raw
   Sensor Data IO (OpenSpec no-invent-data).
4. **Label preference** — Platform: description else identifier; Instrument: type else identifier; multi-join `"; "`
   with Schema.org-style trim/dedupe/sort.
5. **TechnologyPlatform unchanged** — Explicit non-goal; avoids mixing #36 and #441.

## Risks / Trade-offs

- **[Risk] Few live CSW records carry acquisition** → Protocol often absent; still correct. Mitigate with unit mocks.
- **[Trade-off] Hardcoded TechnologyPlatform remains misleading for non-satellite datasets** → Accepted until #441.

## Migration Plan

- Ship next release; no config flag. Rollback = revert.

## Open Questions

- None for lock-in A.
