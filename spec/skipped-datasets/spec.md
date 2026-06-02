# Skipped Datasets

Plugins may deliberately skip individual records (e.g. duplicate sitemap
entries) without treating them as errors.  These skips are counted separately
in the harvest report so operators can distinguish between real failures and
intentional omissions.

## Requirements

- [ ] A new `SkippedRecord` class exists in `middleware.harvester.errors`.
      It carries a human-readable `reason` string and an optional `url`.
- [ ] `SkippedRecord` is **not** a subclass of `HarvesterError`; it is a
      distinct, non-exception signal type.
- [ ] The plugin contract (`Plugin.run()`) yields
      `tuple[str, str | None] | HarvesterError | SkippedRecord`.
- [ ] The orchestrator (`_arc_stream`) counts every `SkippedRecord` instance
      separately and accumulates the total in `_ArcStreamState.skipped_datasets`.
- [ ] A skipped record is logged at **INFO** level (not ERROR), including the
      `reason` and `url` if present.
- [ ] `RepositoryReport` includes a `skipped_datasets: int` field (always
      present, zero by default).
- [ ] The JSON-LD harvest report includes `fairagro:skippedDatasets` for every
      repository entry.
- [ ] The schema_org plugin yields `SkippedRecord` for every
      `DuplicateUrlDiscoveryResult` instead of `RecordProcessingError`.

## Edge Cases

- `skipped_datasets` is always emitted in the JSON-LD output, including when
  it is `0` — unlike `expectedDatasets`, which may be unknown and is omitted
  when `None`.
- A plugin that never yields `SkippedRecord` requires no change; the field
  defaults to `0`.
- A repository task that raises an unhandled exception → `skipped_datasets`
  is `0` (no skips were recorded before the crash).
