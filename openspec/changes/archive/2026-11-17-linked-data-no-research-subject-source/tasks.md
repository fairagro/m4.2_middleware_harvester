# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a minimal e!DAL schema.org dataset with keywords maps with no `#Source_Research_Subject` or `#Sample_`
      entity and the `Keywords` parameter intact (repro; fails on `main`)
- [x] 1.2 T2: the same for a minimal Regal record
- [x] 1.3 T3: the same for a minimal MODS record
- [x] 1.4 T4: the same for a minimal PhenoROAM record
- [x] 1.5 Regenerate fixtures that contain `#Source_Research_Subject` or `#Sample_`

## 2. Verify and close

- [x] 2.1 Manual: OpenAgrar fixtures (schema.org + MODS) from container and source on the branch vs `main`; only the two
      entities and the process `object`/`result` refs change; keywords still in the dump
- [x] 2.2 Archive after merge
