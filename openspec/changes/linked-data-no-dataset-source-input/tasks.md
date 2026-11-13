# Tasks

## 1. Tests and fix

- [ ] 1.1 T1: a minimal e!DAL schema.org dataset maps with no `#Source_Dataset_Source` entity in the RO-Crate (repro;
      fails on `main`)
- [ ] 1.2 T2: the same for a minimal Regal record
- [ ] 1.3 T3: the same for a minimal MODS record
- [ ] 1.4 T4: the same for a minimal PhenoROAM record
- [ ] 1.5 Update `docs/mappers/regal.md` and regenerate fixtures that contain `#Source_Dataset_Source`

## 2. Verify and close

- [ ] 2.1 Manual: e!DAL, Publisso, OpenAgrar and PhenoROAM harvests from the branch vs `main`; only the Assay input
      entity changes; source vs container identical for one ARC
- [ ] 2.2 Archive after merge
