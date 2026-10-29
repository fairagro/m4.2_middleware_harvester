# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a minimal INSPIRE record with a `dataSetURI` has no `#Source_Dataset_Source` entity in the RO-Crate
      (repro; fails on `main`)
- [x] 1.2 T2: the same for a DCAT-AP dataset with an `accessURL`
- [x] 1.3 T3: an INSPIRE record with no URI and no comments has an Assay without an annotation table
- [x] 1.4 T4: a DCAT-AP dataset with no distributions has an Assay without an annotation table and keeps its
      `Landing Page` comment
- [x] 1.5 T5: comment-only records (INSPIRE graphic overview, DCAT-AP titled distribution) keep a one-row table without
      an Input column
- [x] 1.6 Update `docs/mappers/inspire.md`, `docs/mappers/ckanext-dcat.md` and the `_create_assay_table` docstring

## 2. Verify and close

- [ ] 2.1 Manual: BonaRes/Thünen and SRADI harvests from the branch vs `main`; only the Assay input entity (and empty
      tables) change; source vs container identical for one ARC
- [ ] 2.2 Archive after merge
