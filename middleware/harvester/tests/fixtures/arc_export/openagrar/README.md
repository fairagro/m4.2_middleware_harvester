# OpenAgrar (openagrar) arc-export fixtures

No smoke crate at this folder root — real-data cases only (#614). Nested dirs replace the former Schema.org smoke crate
(lock-in D2).

## Real-data cases

Generated via live OpenAgrar MyCoRe REST (`https://www.openagrar.de/api/v2/objects/{id}`) through `ModsXmlParser` +
`ModsMapper` (`mods_general`), matching the preferred commented path in `dev_environment/config.all-rdis.yaml`
(`mycore_rest` → `mods_xml` → `mods_general`). Person `email` values redacted to `redacted@example.invalid` when present
(none in this curated set). Corporate `mods:name` nodes may exist in source MODS; the mapper maps personal names only.

The local `openagrar-fixture` HTTP stand-in and PoW-gated HTML/Solr Schema.org path do **not** satisfy this suite.

- `openagrar_mods_00110150/`: DOI `10.5073/20250926-163035-0`; features: multi-Person (given/family) + ORCID +
  affiliation, corporate name in source, keywords, CC-BY license, abstract, derivate datafile name, EN
- `openagrar_mods_00108436/`: DOI `10.5281/zenodo.13951344`; features: larger multi-Person ORCID set + affiliation,
  corporate name in source, keywords, license, abstract, derivate datafile name, EN
- `openagrar_mods_00105000/`: DOI `10.1094/PBIOMES-05-24-0054-R`; features: multi-Person with affiliation (no ORCID),
  corporate name in source, many keywords, license, abstract, derivate datafile name, EN
- `openagrar_mods_00050000/`: no DOI (Investigation id = MyCoRe object id); features: DE language, dual corporate names
  in source, personal + affiliation (no ORCID), license, derivate datafile name, no keywords/abstract
