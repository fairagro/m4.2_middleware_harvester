# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a minimal dataset with no distributions has no `URI` entity for the dataset IRI in the RO-Crate (repro;
      fails on `main`)
- [x] 1.2 T2: a dataset with an `accessURL` keeps `Output [URI]` = that URL
- [ ] 1.3 T3: a dataset with no URL but a titled distribution keeps a one-row table with Input, a title comment and its
      `Landing Page` comment
- [ ] 1.4 Update the distribution row and the "Assay Output URI" rule in `docs/mappers/ckanext-dcat.md`; markdown hooks
      pass

## 2. Verify and close

- [ ] 2.1 Manual: SRADI harvest from the branch vs `main`; expect 25 ARCs to change, only in the Assay output; source vs
      container identical for one ARC
- [ ] 2.2 Archive after merge
