# SRADI (sradi) arc-export fixtures

No smoke crate at this folder root — real-data cases only (#612).

## Real-data cases

Generated via live DCAT-AP / ckanext-dcat (`https://agrihub.gis.lrg.tum.de/catalog.jsonld?fq=groups:dataset`) through
`DcatApProtocol` + `JsonLdParser` + `CkanextDcatMapper` (`ckanext_dcat`), matching
`dev_environment/config.all-rdis.yaml`. Contact emails that contained `@` are redacted to `redacted@example.invalid`. No
catalog record on the curated page exposed `dcterms:license` (dataset or distribution); crates keep the ARCtrl
`#LICENSE` default — real-source behaviour after #530.

Case directory names are CKAN package / dataset UUIDs (last path segment of the `dcat:Dataset` IRI).

- `3cb09cb4-7609-4a96-b65c-9821e9abfdbd/` — _DigiFarm - Erfassung und Auswertung der Heterogenität von Ackerschlägen
  (Daten von Krohberg )_: multi-distribution (5; CSV/XLSX); spatial WKT; org publisher/contact JSON unwrap; source
  identifier; landing page (dataset IRI); keywords; no `dcterms:license`
- `f1f0463b-5c73-40e4-a26e-c8626e5e5c67/` — _Roggenstein Field Cards_: multi-distribution (15; CSV/PDF/RAR); spatial
  WKT; org publisher/contact JSON unwrap; source identifier; landing page; keywords; no `dcterms:license`
- `dd26a2cb-aaa0-450e-86c3-c56ed4187334/` — _SOLAW 2021_: multi-distribution (3; HTML/PDF); **no spatial**; org
  publisher/contact JSON unwrap; source identifier; landing page; keywords (EN); no `dcterms:license`
- `01be8189-ba54-4be0-89bb-53b11d6f87ef/` — _Hof-Feld-Transportpfad zum Feldstück parcel_debyli8320000171_: **no
  distributions**; spatial WKT; org publisher/contact unwrap; source identifier; landing page; keyword; no
  `dcterms:license`
