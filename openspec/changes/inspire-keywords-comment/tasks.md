# Tasks

## 1. Parser — MD_Keywords → InspireRecord.keywords

- [ ] 1.1 Extend `IsoParser` keyword extraction so OWSLib `MD_Keywords` nested `.keywords[].name` values (and plain
      `str` items) populate `InspireRecord.keywords`; omit empty names; leave value-bounds behaviour unchanged — verify
      with new/updated unit tests that mock `MD_Keywords` (names present) and plain-string lists
- [ ] 1.2 Cover empty / missing `identification.keywords` → empty list in parser unit tests — verify
      `uv run pytest middleware/inspire/tests/unit/test_iso_parser.py -q` (and related harvester parse tests still
      green)

## 2. Mapper — Keywords Investigation Comment

- [ ] 2.1 In `InspireMapper`, emit Comment `Keywords` from non-empty `record.keywords` with trim / casefold-dedupe /
      sort / `", "` join; omit when empty — verify with mapper unit tests (present, empty, duplicates, whitespace)
- [ ] 2.2 Update `docs/mappers/inspire.md` MD_Keywords table to the Comment mapping and fix/remove the stale GEMET
      OntologyAnnotation NOTE so it matches this MVP — verify the doc describes Comment `Keywords` only for this path

## 3. Integration check

- [ ] 3.1 Run focused inspire + payload inspire mapper tests
      (`uv run pytest middleware/inspire/tests/unit     middleware/payload/tests -k "keyword or inspire" -q` or
      package-equivalent) and `openspec validate --change     inspire-keywords-comment` — verify all pass
