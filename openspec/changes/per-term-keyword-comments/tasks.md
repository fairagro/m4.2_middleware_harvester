# Tasks

## 1. Shared helper

- [ ] 1.1 Add `middleware.payload` helper that appends aggregate `Keywords` + per-term / optional DDC Comments per
      `keyword-comments` (unique names; `", "` join; no bare `keyword`) — verify with focused unit tests for plain, URI,
      DDC-present, DDC-absent, and casefold dedupe
- [ ] 1.2 Document the contract in `docs/mappers/` (shared note or Regal as reference + cross-links) and note #417
      Comments-first / #604 aggregate removal — verify docs match the helper behaviour

## 2. Mapper call sites

- [ ] 2.1 Wire `InspireMapper` to the helper from `KeywordTerm` (name + url); update `docs/mappers/inspire.md` and
      mapper tests (URI + plain + empty) — verify pytest for inspire mapper keywords
- [ ] 2.2 Wire `GeneralSchemaOrgMapper`: Investigation Comments via helper; remove Study Data Collection Keywords-only
      table path; update docs + tests (determinism still holds) — verify schema.org / linked-data mapper tests
- [ ] 2.3 Align `RegalMapper` to helper (`keyword [<label>]` when no URI); drop duplicate Keywords protocol parameter if
      present; update docs + tests — verify regal keyword tests
- [ ] 2.4 Wire `CkanextDcatMapper` to helper; remove Dataset Processing Keywords parameter; align aggregate to `", "`;
      update docs + tests — verify ckanext-dcat tests
- [ ] 2.5 Wire `ModsMapper` / `PhenoroamMapper` to helper; remove Study Data Collection Keywords parameter/tables when
      Keywords-only; update docs + tests — verify mods + phenoroam tests

## 3. Integration

- [ ] 3.1 Run focused payload mapper pytest suites and `openspec validate per-term-keyword-comments` — verify green
