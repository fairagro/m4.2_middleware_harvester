# BonaRes arc-export fixtures

Smoke: `ro-crate-metadata.json` at this folder root (synthetic).

## Real-data cases

Generated via inspire plugin against `https://repository-e.dataservice.zalf.de/catalogue/csw` with `inspire_general`
mapper (placeholders: None / No information provided). Person `email` values redacted to `redacted@example.invalid`.

- `7743f5cf-dafe-4193-bd84-d80dcf1c3405/`: source id `7743f5cf-dafe-4193-bd84-d80dcf1c3405`; features: person, keywords,
  spatial, license, protocol, comment
- `f7cad4da-e142-4e53-89bd-e15b0c6752cc/`: source id `f7cad4da-e142-4e53-89bd-e15b0c6752cc`; features: person,
  organization, spatial, license, protocol, comment
- `bdc804a2-4e20-4463-b21a-57ce4cb6df00/`: source id `bdc804a2-4e20-4463-b21a-57ce4cb6df00`; features: keywords,
  spatial, license, protocol, comment (no Person nodes)
