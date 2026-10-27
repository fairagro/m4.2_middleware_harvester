# Tasks

## 1. Tests and fix (US-003)

- [x] 1.1 T1: a schema.org Dataset maps to an RO-Crate with no "Raw Data" / "Published Dataset" File entities
- [x] 1.2 T2: a Regal record maps to an RO-Crate with no "Raw Data" / "Published Dataset" File entities
- [x] 1.3 T3: a ckanext-dcat dataset maps with no "Published Dataset" File entity and no "Raw Data" Source
- [x] 1.4 T4: processing protocol parameters are still present in all three mappers
- [x] 1.5 T5: the Assay `Output [URI]` is unchanged in all three mappers
- [ ] 1.6 Update `docs/mappers/ckanext-dcat.md` (and schema.org / Regal docs if they describe processing I/O)
- [ ] 1.7 Diff ARC payloads from a source run and a container run on one PUBLISSO, one SRADI and one schema.org record

## 2. Close

- [ ] 2.1 Comment on #353 with the PR
- [ ] 2.2 Archive after merge
