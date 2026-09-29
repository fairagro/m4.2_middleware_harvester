# Proposal

## Why

PhenoRoam exposes a working OAI-PMH path with native `phenoroam` XML (`pr:metadataDataset`), but the harvester only has
`rdf_xml` → `rdf_graph` parsers and Schema.org/Regal mappers. Without a dedicated parser + mapper, ~124 live records
cannot become ARCs even though `oai_pmh` can already ListRecords.

## What Changes

- Add a shared inline PayloadParser `phenoroam_xml` that turns OAI `<metadata>` XML into a typed intermediate
  (`PayloadKind.phenoroam_record`).
- Add a shared DataMapper `phenoroam_general` that maps that intermediate to ARC Investigation / Study / Assay with
  annotation tables — **no invented data-file Outputs** (aligned with #353).
- Extend `PayloadKind` and mapper/parser registries; wire example config for PhenoRoam OAI.
- Contact names use the same `split_display_name` + person-contact-given-name policy as INSPIRE / Schema.org.
- Stable identifier: prefer unique `itemUUID`; otherwise landing-page URL — not DOI-driven.

## Capabilities

### New Capabilities

- `phenoroam-xml-parser`: Inline OAI `phenoroam` / `pr:` XML → `ParsedPayload` (`phenoroam_record`).
- `phenoroam-to-arc-mapping`: `phenoroam_general` DataMapper → ARC Investigation/Study/Assay (+ annotation tables; no
  fabricated data-file entities).

### Modified Capabilities

- `payload`: Add `PayloadKind.phenoroam_record` and register mapper type `phenoroam_general`.
- `payload-parser`: Register parser type `phenoroam_xml`; alignment with sibling `parser:` / `mapper:` for `oai_pmh`.

## Impact

- Code: `middleware/parsing` (parser + register), `middleware/payload` (`kinds`, new mapper module, register), optional
  example YAML under `dev_environment/` / helm; tests + fixtures from a live OAI sample.
- Config: operators set `oai_pmh.metadata_prefix: phenoroam` with sibling `parser: { type: phenoroam_xml }` and
  `mapper: { type: phenoroam_general }`.
- Dependencies: none beyond existing XML stack (`defusedxml` / lxml as already used in OAI/parsing).
- Non-goals: CSW/DCAT Geonetwork paths; Schema.org intermediate; EPrints mapper; datafile Outputs from metadata-only
  harvest (#353); semantic data-quality validation (#132).
