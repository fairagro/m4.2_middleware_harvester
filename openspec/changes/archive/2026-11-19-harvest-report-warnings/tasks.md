# Tasks

## 1. HarvestedArc warnings transport

- [x] 1.1 Add optional `warnings: tuple[str, ...] = ()` to `HarvestedArc` and a matching kwarg on
      `HarvestedArc.from_arctrl`; verify with a unit test that default is empty and supplied messages are preserved
      without changing `arc_json` / counts (`uv run pytest middleware/payload/tests/unit/ -k harvested_arc -v`)
- [x] 1.2 In `arc_stream`, call `scope.record_warning(message, record_id=…, url=…)` for each warning on a yielded
      `HarvestedArc`; verify harvester unit tests cover one warning, multiple warnings, and empty list without changing
      harvested/failed/skipped (`uv run pytest middleware/harvester/tests/unit/ -k warning -v`)

## 2. Schema.org soft paths

- [x] 2.1 Thread a warning accumulator through Schema.org title-fallback mapping and attach a message on the yielded
      `HarvestedArc` when `Title Source` is set; verify `test_mapper_title_fallback` (and related) assert non-empty
      `HarvestedArc.warnings` (`uv run pytest middleware/payload/tests/unit/test_mapper_title_fallback.py -v`)
- [x] 2.2 Attach dataset warnings for Schema.org date normalisation / `Unparsed <term>` soft paths; verify existing date
      unit tests assert warnings when a WARNING is logged and none for clean ISO years
      (`uv run pytest middleware/payload/tests/unit/ -k 'iso or date' -v` focused on schema.org date cases)

## 3. Regal and CKAN soft paths

- [x] 3.1 When Regal skips a creator/contributor without `skos:prefLabel`, attach a dataset warning on the yielded
      `HarvestedArc`; verify with a unit test for the unlabelled-member case
      (`uv run pytest middleware/payload/tests/unit/test_regal_mapper.py -k prefLabel -v`)
- [x] 3.2 When CKAN spatial WKT exceeds `spatial_extent_max_chars`, attach a dataset warning on the yielded
      `HarvestedArc`; verify over-cap / configured-cap tests assert warnings
      (`uv run pytest middleware/payload/tests/unit/ -k spatial -v`)

## 4. Integration check

- [x] 4.1 Run focused payload + harvester tests and ruff on touched files; confirm a synthetic title-fallback ARC
      through `arc_stream` increments warned datasets on a real `RepositoryScope` snapshot
      (`uv run ruff format --config ruff.toml` / `uv run ruff check --config ruff.toml` on touched paths;
      `uv run pytest middleware/payload/tests/unit middleware/harvester/tests/unit -q`)
