# Harvest Report — Design

## Ownership

The harvest-report **contract** (mutable model, counting methods, JSON-LD
serializer, vocabulary) lives in
[`fairagro/m4.2_advanced_middleware_api`](https://github.com/fairagro/m4.2_advanced_middleware_api):

- Package: `middleware.shared.report` (`fairagro-middleware-shared`)
- OpenSpec: `openspec/specs/harvest-report/` (after archive of
  `shared-harvest-report`)
- Vocabulary: `ns/harvest-report/v2/` (v1 frozen with `failedRecords`)

This harvester repo only wires that library into the orchestration loop.

## Module Overview

```text
middleware/harvester/
  orchestrator.py   HarvestReport() at run start; open_repository per RDI
  upload.py         stream ARCs; apply scope.record_* from API outcomes
  reporting.py      emit_report / source-URL annotation / outcome helpers
  plugin_base.py    HarvestedArc (+ from_arctrl) / Plugin protocol
  main.py           CLI; emit_report after tracing shutdown

middleware.shared.report   ← API repo / PyPI package
  HarvestReport, RepositoryScope, RepositoryReport, HarvestIssue, IssueKind
  JsonLdReportSerializer
```

Orchestration-only helpers (ARC `@graph` study/assay parsing, source-URL
annotation text, exit-code “all failed”) stay in the harvester. They MUST NOT
duplicate harvested/failed/skipped/study/assay totals outside the scope.

## Key Decisions

1. **Do not duplicate the report contract here**
   — Shape, omit rules, namespace IRI, counting API, and serializers are owned
   by the API repository so harvester and other clients stay compatible.

2. **Scope is the sole counter; count from the API result**
   — While streaming, only track how many ARCs were submitted plus study/assay
   sums from each yielded `HarvestedArc` (and source-URL hints). After
   `harvest_arcs` returns: one `record_failed` per API error, then
   `record_harvested` × `(submitted - len(errors))`, then `add_studies` /
   `add_assays` for the batch totals. If upload aborts with submitted ARCs,
   each is `record_failed`; if none were submitted, one
   `record_repository_issue`. Composition counts come from the plugin
   (arctrl `StudyCount` / `AssayCount`), not from re-parsing RO-Crate JSON.

3. **Separate dataset failures from repository issues**
   — Per-dataset map/upload/`RecordProcessingError` outcomes call
   `record_failed` (`IssueKind.DATASET`, bumps `failed_datasets`). RDI-global
   problems (unknown plugin type, unhandled repository exception, gather
   escape, sitemap/discovery `HarvesterError`) call
   `record_repository_issue` (`IssueKind.REPOSITORY`, no counter bump). Do not
   manually adjust `failed_datasets` to encode repo issues.

4. **Emit after tracing shutdown**
   — Shared library returns a document string only; the harvester prints it to
   stdout after OTLP flush. Print/serialize errors are logged and ignored for
   exit code. Wire vocabulary is v2 (`fairagro:failures` + `fairagro:kind`).
