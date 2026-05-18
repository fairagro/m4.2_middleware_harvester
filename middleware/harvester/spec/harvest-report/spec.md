# Harvest Report

At the end of each harvester run, the orchestrator emits a machine-readable
summary of the completed harvest to **stdout** as a JSON-LD document.  The
document describes every repository that was processed, including timing,
expected dataset count, and outcome statistics.

## Requirements

- [ ] After all repository tasks finish (whether they succeed or fail), the
      orchestrator collects one `RepositoryReport` per configured repository
      and passes them to a `HarvestReport` builder.
- [ ] `RepositoryReport` captures:
  - the RDI identifier (string)
  - the `harvest_id` returned by `ApiClient.harvest_arcs` (`str | None` when the
    upload was skipped or failed before a harvest was created)
  - wall-clock duration of the repository harvest in seconds (`float`)
  - `expected_datasets`: the value returned by `Plugin.get_expected_datasets()`
    (`int | None` if unavailable)
  - `harvested_datasets`: number of ARC strings successfully yielded by the
    plugin and forwarded to the API
  - `failed_datasets`: number of `HarvesterError` instances yielded by the
    plugin
- [ ] `HarvestReport` captures:
  - overall wall-clock duration of the entire run in seconds (`float`)
  - the list of `RepositoryReport` objects
- [ ] The report is serialised as JSON-LD and printed to **stdout** (not to the
      logging subsystem and not to stderr).
- [ ] The JSON-LD document uses `https://schema.org/` as its primary
      vocabulary.  The harvest run is typed as `schema:Action`; each repository
      result is typed as `schema:EntryPoint` nested under `schema:result`.
- [ ] The JSON-LD document uses an additional `fairagro:` prefix
      (`https://fairagro.net/ns/`) for domain-specific properties
      (`expectedDatasets`, `harvestedDatasets`, `failedDatasets`,
      `harvestDurationSeconds`).
- [ ] `schema:startTime` and `schema:endTime` on the top-level `Action` are
      ISO 8601 UTC timestamps (e.g. `"2026-05-06T14:00:00Z"`).
- [ ] `schema:duration` on each repository entry is an ISO 8601 duration string
      (e.g. `"PT12.3S"`).
- [ ] Printing the report must not raise; if serialisation fails for any reason
      the exception is caught, a warning is logged, and the process continues
      to its normal exit.
- [ ] The report is printed **after** tracing shutdown has been initiated so
      that tracing data is flushed before stdout is closed.

## Edge Cases

Repository task raised an unhandled exception → `harvest_id` is `None`,
`failed_datasets` equals `expected_datasets` if known, otherwise `None`.

`get_expected_datasets()` returned `None` → `expected_datasets` is omitted
from the JSON-LD output (the key is not emitted rather than set to `null`).

No repositories configured → an `Action` with an empty `result` array and
a zero-duration is emitted.

Serialisation of the report raises → a single `WARNING` log line is emitted;
the harvester exits with the same code it would have used otherwise.
