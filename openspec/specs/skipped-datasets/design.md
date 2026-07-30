# Skipped Datasets — Design

## Module Overview

```text
middleware/harvester/errors.py
└── SkippedRecord               # new non-exception signal class

middleware/harvester/plugin_base.py
└── Plugin.run()                # yield type extended to include SkippedRecord

middleware/harvester/upload.py
└── arc_stream()                # isinstance(item, SkippedRecord) → scope.record_skipped()

middleware/harvester/reporting.py
└── handle_skipped_record()     # INFO log for skip reason / URL

middleware.shared.report
├── RepositoryScope.record_skipped()
├── RepositoryReport.skipped_datasets  # always int, default 0
└── JsonLdReportSerializer             # fairagro:skippedDatasets always emitted

middleware/linked_data/plugin.py
└── producer()                  # forwards SkippedRecord / RecordProcessingError from sitemap.discover()
```

## Key Decisions

1. **`SkippedRecord` is not a subclass of `HarvesterError`**
   — `HarvesterError` signals that something went wrong and increments
   `failed_datasets`.  A deliberate skip is not a failure; conflating the two
   produces a misleading report.  A separate, non-exception class makes the
   distinction explicit at the type level and requires callers to handle both
   branches consciously.

2. **`SkippedRecord` is not an exception (not raised, only yielded)**
   — Raising and catching within the plugin would couple skip-handling to
   exception machinery and obscure intent.  Yielding a value object keeps the
   plugin's async generator interface uniform: every yield is either a
   successful ARC payload, an error, or a skip.

3. **`skipped_datasets` is always present in the report (default `0`)**
   — `expectedDatasets` is omitted when `None` because the count may be
   genuinely unknown.  Skips are counted from the generator stream, so the
   count is always known (possibly `0`).  Emitting `0` explicitly avoids
   ambiguity for downstream consumers parsing the JSON-LD.

4. **Log at INFO, not WARNING or ERROR**
   — Duplicate sitemap entries are a data-quality issue in the source, not a
   bug in the harvester.  An ERROR log would trigger unnecessary alerts.
   INFO makes the skip visible in normal operation logs without inflating
   error counters.

5. **Plugin contract extended, not replaced**
   — `Plugin.run()` now yields `HarvestedArc | HarvesterError | SkippedRecord`.
   Existing plugins that never yield `SkippedRecord` remain valid; the
   orchestrator's `isinstance` dispatch handles all three branches
   independently.
