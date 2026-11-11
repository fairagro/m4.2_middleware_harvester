# Tasks

## 1. Model + parser

- [ ] 1.1 Add `AcquisitionInstrument` / `AcquisitionPlatform` / `AcquisitionInformation` (or equivalent) on
      `InspireRecord` with value-bounds — verify model construction / validation unit coverage
- [ ] 1.2 Parse OWSLib `iso.acquisition` in `IsoParser` into that field (omit empties; missing → empty) — verify unit
      tests with mocked `MI_AcquisitionInformation` / platform / instrument and a missing-acquisition case

## 2. Mapper + docs

- [ ] 2.1 Implement Assay `Sensor Acquisition` protocol (parameters Platform / Instrument only; `None` when empty; no
      invented IO; leave TechnologyPlatform hardcoded) — verify mapper unit tests present/absent
- [ ] 2.2 Update `docs/mappers/inspire.md` acquisition / Assay rows to the protocol mapping — verify docs match
      behaviour

## 3. Integration check

- [ ] 3.1 Run focused inspire + payload inspire mapper tests and `openspec validate inspire-sensor-acquisition` — verify
      all pass
