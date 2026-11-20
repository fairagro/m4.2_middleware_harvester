# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a minimal geographic INSPIRE record with a bounding box maps with no `#Source_Geographic_Region` entity,
      `Bounding Box` intact, and Data Acquisition still taking `Selected Location` as input (repro; fails on `main`)
- [x] 1.2 T2: the same for a minimal Regal record with recording location and coordinates
- [x] 1.3 T3: the same for a minimal PhenoROAM record with a complete bbox
- [x] 1.4 T4: a record without spatial information has no Spatial Sampling table
- [ ] 1.5 Update `docs/mappers/inspire.md` and `docs/mappers/regal.md`; regenerate fixtures that contain
      `#Source_Geographic_Region`

## 2. Verify and close

- [ ] 2.1 Manual: BonaRes and Publisso fixtures from container and source on the branch vs `main`; only the Source
      entity and the process `object` refs change; spatial parameter values still in the dump
- [ ] 2.2 Archive after merge
