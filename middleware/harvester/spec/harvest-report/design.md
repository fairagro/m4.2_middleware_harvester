# Harvest Report — Design

## Module Overview

A new module `middleware/harvester/src/middleware/harvester/report.py` owns all
reporting concerns: the `RepositoryReport` and `HarvestReport` dataclasses, the
JSON-LD serialiser, and the `print_report()` helper.

`main.py` is the only caller.  It accumulates `RepositoryReport` objects while
iterating over `_run_repository` results, builds a `HarvestReport`, and calls
`print_report()` once — after tracing shutdown, before `sys.exit`.

## JSON-LD Shape

```json
{
  "@context": {
    "@vocab": "https://schema.org/",
    "fairagro": "https://fairagro.net/ns/"
  },
  "@type": "Action",
  "name": "FAIRagro Harvest Run",
  "startTime": "2026-05-06T14:00:00Z",
  "endTime": "2026-05-06T14:03:45Z",
  "duration": "PT225.0S",
  "result": [
    {
      "@type": "EntryPoint",
      "name": "bonares",
      "identifier": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "schema:duration": "PT12.3S",
      "fairagro:expectedDatasets": 100,
      "fairagro:harvestedDatasets": 95,
      "fairagro:failedDatasets": 5,
      "fairagro:skippedDatasets": 2,
      "fairagro:failedRecords": [
        {
          "fairagro:message": "Failed to map dataset frl:123: …",
          "fairagro:recordId": "frl:123"
        }
      ]
    }
  ]
}
```

## Key Decisions

1. **`report.py` as a standalone module, not part of `main.py`**
   — Keeping reporting logic in its own file keeps `main.py` focused on
   orchestration control flow and makes the report shape testable in isolation
   without having to execute the full async orchestrator.

2. **`schema:Action` / `schema:EntryPoint` vocabulary**
   — A harvest run is an *action* performed by the system; schema.org's
   `Action` type is the closest standard match.  Each per-RDI result entry is
   an `EntryPoint` (a named interaction point in the system), which captures
   the identifier/name pair natively.  PROV-O `Activity` was considered but
   rejected because schema.org is already used in the linked_data plugin and
   requires no additional namespace declaration.

3. **Custom `fairagro:` prefix for domain statistics and failure detail**
   — `expectedDatasets`, `harvestedDatasets`, `failedDatasets`,
   `skippedDatasets`, and the `failedRecords` list have no direct equivalent
   in schema.org or PROV-O.  Rather than misusing an existing term, a
   project-owned `https://fairagro.net/ns/` prefix is used.  Counts alone are
   insufficient for operators: each yielded `HarvesterError` is also mirrored
   as a `failedRecords` entry (`message`, optional `recordId` / `url`) so the
   stdout report is the authoritative failure list, not only application logs.

4. **ISO 8601 duration strings (`PT12.3S`) for per-repository timing**
   — `schema:duration` is defined with range `schema:Duration`, which expects
   ISO 8601.  Python's `datetime.timedelta` does not format to ISO 8601
   natively, so a minimal helper converts seconds to `PTnS` / `PTnMnS`.

5. **Omit `expectedDatasets` when `None`**
   — Emitting `"fairagro:expectedDatasets": null` would assert the absence of
   expected datasets as a known fact, which is misleading.  Omitting the key
   entirely signals that the value was not available, consistent with JSON-LD
   open-world semantics.

6. **Print to stdout, not the logging subsystem**
   — The report is a structured machine-readable artefact intended for
   downstream consumers (CI pipelines, log aggregators).  Using `print()` /
   `sys.stdout.write()` ensures it reaches stdout as raw text without log-level
   prefixes or timestamps that would break JSON parsers.

7. **Silent failure with a logged warning**
   — If serialisation fails (e.g. unexpected type in a dataclass field), it
   must not mask the real exit code.  A warning is logged and execution
   continues; the report is simply missing, which is recoverable.
