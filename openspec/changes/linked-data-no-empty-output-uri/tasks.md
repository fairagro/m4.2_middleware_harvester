# Tasks

## 1. Tests and fix

- [ ] 1.1 T1: a minimal PhenoROAM record with no catalog id maps with no empty `URI` entity in the RO-Crate (repro;
      fails on `main`)
- [x] 1.2 T2: the same for a MODS record with no http(s) source URL
- [x] 1.3 T3: the same for a schema.org dataset with no url, sameAs, http IRI, DOI or source URL
- [ ] 1.4 T4: records with a URL keep `Output [URI]` unchanged (one per mapper)
- [ ] 1.5 T5: no URL and no comments → no Assay table; no URL with comments → one-row table with the comments only
- [ ] 1.6 Update `docs/mappers/*.md` for the three mappers

## 2. Verify and close

- [ ] 2.1 Manual: PhenoROAM, OpenAgrar fixture and e!DAL harvests from the branch vs `main`; count changed ARCs
- [ ] 2.2 Archive after merge
