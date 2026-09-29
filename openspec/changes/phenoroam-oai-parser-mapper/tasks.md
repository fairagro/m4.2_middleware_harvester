# Tasks

## 1. PayloadKind and PhenoroamRecord model

- [x] 1.1 Add `PayloadKind.phenoroam_record` to `middleware.payload.kinds` (or equivalent enum); verify import and that
      existing kinds remain unchanged
- [x] 1.2 Add Pydantic `PhenoroamRecord` (and nested contact / study / datafile-link DTOs as needed) under
      `middleware.payload` — fields covering `itemUUID`, titles/descriptions, keywords, license/rights, bbox, persons,
      nested study/investigation blocks, and optional remote `itemLink` URL strings; verify model round-trip from a dict
      fixture

## 2. phenoroam_xml PayloadParser

- [x] 2.1 Implement shared inline parser (`parser.type: phenoroam_xml`) in `middleware.parsing` that reads
      `XmlDiscoveryResult` (or equivalent) metadata, parses `pr:metadataDataset` with defusedxml, builds
      `PhenoroamRecord`, and returns `ParsedPayload(kind=phenoroam_record, …)`; raise `ParserError` on missing /
      wrong-root / unusable XML; verify unit tests (happy path, empty metadata, wrong root, no HTTP client required)
- [x] 2.2 Register the parser in `register_builtin_parsers`; verify registry lookup `phenoroam_xml` and
      `produces == phenoroam_record`
- [x] 2.3 Add a fixture from a live PhenoRoam OAI ListRecords `<metadata>` sample under parsing or payload tests; verify
      tests load it without network

## 3. phenoroam_general DataMapper

- [x] 3.1 Implement `mapper.type: phenoroam_general` accepting `phenoroam_record`: Investigation / Study / Assay with
      annotation tables for keywords (and license/rights / bbox when present); identifier = unique `itemUUID` else
      landing URL; never require DOI; verify unit tests for UUID id, landing-URL fallback, and title/description on
      Investigation
- [x] 3.2 Map `blockPerson` contacts via `split_display_name` + person-contact-given-name policy (same as INSPIRE /
      Schema.org); verify Person with given/family/affiliation and fail-closed or Comment path for empty given name
- [x] 3.3 Map nested `blockStudy` / `blockInvestigation` titles/descriptions into Study/Investigation; verify nesting
      appears in the ARC
- [x] 3.4 Ensure `listDatafiles` / `itemLink` values become comments or annotation cells only — **no** invented
      data-file Output entities (#353); verify unit test that a record with download links has no file Outputs
- [x] 3.5 Register the mapper in the payload registry; verify `accepts == phenoroam_record` and config kind alignment
      with `phenoroam_xml`

## 4. Config example and docs

- [x] 4.1 Add or update example/dev config for PhenoRoam OAI (`metadata_prefix: phenoroam`,
      `parser: { type:     phenoroam_xml }`, `mapper: { type: phenoroam_general }`); verify config validates at startup
- [x] 4.2 Touch AGENTS.md / OpenSpec principles only if the module graph or documented plugin list needs the new
      registry keys called out; verify documented commands still refer to real paths

## 5. Integration check

- [x] 5.1 Run targeted pytest for phenoroam parser + mapper + affected registry/config tests; verify green
- [x] 5.2 Run `openspec validate --changes` (or change-scoped validate) for `phenoroam-oai-parser-mapper`; verify the
      change validates
- [x] 5.3 Confirm non-goals: no Schema.org intermediate, no Geonetwork CSW path, no datafile Outputs, no byte download
      of `itemLink` URLs
