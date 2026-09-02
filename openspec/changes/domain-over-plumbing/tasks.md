## 1. Update principles main spec

- [x] 1.1 Add **Domain over plumbing** under Values in `openspec/specs/principles/spec.md`
- [x] 1.2 Add the domain/infrastructure separation Constraint (including YAGNI for harvester-wide frameworks)
- [x] 1.3 Extend Module Dependency Graph with Linked Data `plugin.py` → `pipeline.py` (and note that pipeline MUST NOT perform mapping)
- [x] 1.4 Merge the ADDED requirement *Separate domain logic from technical plumbing* into the Requirements section of `openspec/specs/principles/spec.md`

## 2. Validate

- [x] 2.1 Run `openspec validate --change domain-over-plumbing` (and/or `--specs` after merge) and fix any issues
