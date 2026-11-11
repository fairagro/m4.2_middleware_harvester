# Tasks

## 1. Parser — MD_Keywords → InspireRecord.keywords

- [x] 1.1 Extend `IsoParser` keyword extraction so OWSLib `MD_Keywords` nested `.keywords[].name` / `.url` and group
      thesaurus title populate `InspireRecord.keywords` terms (plain `str` → name-only); omit empty names; leave
      value-bounds behaviour unchanged — verify with unit tests mocking `MD_Keywords` (with/without URL+thesaurus) and
      plain-string lists
- [x] 1.2 Cover empty / missing `identification.keywords` → empty list in parser unit tests — verify
      `uv run pytest middleware/inspire/tests/unit/test_iso_parser.py -q` (and related harvester parse tests still
      green)

## 2. Model + Mapper — KeywordTerm + Keywords Comment

- [x] 2.0 Add `KeywordTerm` (`name`, optional `url`, optional `thesaurus`) on `InspireRecord.keywords` with string
      coerce — verify model validation / existing string fixtures still construct
- [x] 2.1 In `InspireMapper`, emit Comment `Keywords` from non-empty term **names** with trim / casefold-dedupe / sort /
      `", "` join; omit when empty; do not put URI/thesaurus in the Comment — verify with mapper unit tests
- [x] 2.2 Update `docs/mappers/inspire.md` MD_Keywords table (retain vs ARC emit) and fix the stale GEMET NOTE — verify
      the doc matches this MVP

## 3. Integration check

- [x] 3.1 Run focused inspire + payload inspire mapper tests and `openspec validate inspire-keywords-comment` — verify
      all pass
