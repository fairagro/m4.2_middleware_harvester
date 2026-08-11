## Context

See `proposal.md` for motivation. ISA/ARC contacts are Persons only; RO-Crate
may express organizations via affiliation or comments. `GeneralSchemaOrgMapper`
currently maps Organization publishers to `Person(first_name="", last_name=org)`.
`RegalMapper` splits `skos:prefLabel` on `", "` and sets `first_name=""` when
there is no comma — the same export failure mode for org-/label-only agents.
Linked-data plugins already turn mapper exceptions into `RecordProcessingError`
(no upload); fail-closed can reuse that path.

## Goals / Non-Goals

**Goals:**

- Guarantee every emitted Person contact has a non-empty trimmed given name.
- Represent publishers/orgs as Investigation comments (and affiliations where
  appropriate), never as empty-given-name Persons.
- Fail mapping (no `HarvestedArc`) when a Person contact would still lack a
  given name.
- Cover OpenAgrar-like Schema.org graphs and Regal org/label edge cases in tests,
  including an arctrl Write/load/export round-trip that must not raise
  `Person must have a given name`.

**Non-Goals:**

- Changing Middleware API ingest or inventing an Organization contact type.
- Shared helpers in `m4.2_advanced_middleware_api` (solve locally first).
- Broad rewrite of INSPIRE contact mapping (out of scope unless a tiny shared
  validator is reused; default is linked_data only).

## Decisions

1. **Validate after contact assembly, raise mapping error**
   — Prefer a single post-assembly check on Investigation contacts (non-empty
   trimmed `FirstName`) that raises `ValueError` (or a linked_data mapping
   error subclass used only if already conventional). Reasoning: the plugin
   already wraps mapper failures as `RecordProcessingError`, so fail-closed
   upload/report behaviour comes for free without orchestrator changes.
   Alternatives considered: silently drop invalid contacts (loses authors;
   violates fail-closed); invent placeholder given names (explicitly forbidden).

2. **Publisher Organization → Comment("Publisher", name), not Person**
   — In `GeneralSchemaOrgMapper._add_contacts`, skip `_append_contact` for
   publisher; in `_add_investigation_comments`, emit `Publisher` (and optional
   URL). Assay/study tables may keep existing Publisher annotations. Reasoning:
   matches allowed org representation and removes the Zenodo failure mode.
   Alternatives considered: affiliation-only without comment (publisher is not
   a person affiliation); keep Person with org name as givenName (forbidden).

3. **Organization-typed creators/contributors: omit as Person; optional Comment**
   — Do not create empty-given Persons. Prefer omitting or a role-appropriate
   Investigation comment if a stable name exists. Reasoning: same given-name
   invariant; OpenAgrar failure was publisher-shaped.

4. **Regal: refuse Person when split yields empty given name unless org path**
   — If `prefLabel` has no `", "` (or given part empty after trim): do not
   `Person.create(..., first_name="")`. Treat institution-like agents via
   existing Institution comments/Affiliation patterns where applicable; otherwise
   fail closed. Reasoning: docs currently allow LastName-only; this change
   overrides that for contacts to protect arc-export. Alternatives considered:
   only fix Schema.org (leaves Regal export landmines).

5. **No placeholder given names**
   — Never substitute `.`, `n/a`, or org name as FirstName. Reasoning: would
   pass arctrl checks but corrupt metadata and hide source quality issues.

6. **Local helper in linked_data package**
   — Small shared function e.g. `_require_person_given_names(inv)` used by both
   mappers. Reasoning: avoids API-repo dependency; keeps DRY within the package.

## Risks / Trade-offs

- [Risk] Records that previously uploaded with LastName-only contacts will now
  fail → Mitigation: intentional fail-closed; harvest report surfaces them;
  operators can fix source metadata or extend org→Comment heuristics later.
- [Risk] Existing unit tests that use literal creators like `"Alice Example"`
  (space-split yields given name) vs single-token literals may need updates →
  Mitigation: adjust fixtures to include given names; add explicit fail tests.
- [Trade-off] Stricter Regal contact rules vs historical “entire prefLabel →
  LastName” → Accept; document override in delta spec and `docs/regal_mapping.md`
  contact row if touched in tasks.

## Migration Plan

- Deploy with linked_data package only; no API migration.
- Rollback: revert mapper changes; known Zenodo/org cases fail again in DataHUB CI.
