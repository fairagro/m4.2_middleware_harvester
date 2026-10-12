# Tasks

## 1. Bounds

- [x] 1.1 `InspireRecord.other_constraints` and `constraints` use `LongStr`; codelist constraint lists stay `MediumStr`
- [x] 1.2 `ValueBounds.max_str_long` description names free-text constraints

## 2. Tests

- [x] 2.1 `test_iso_parser.py`: a 1136-char `otherConstraints` and `useLimitation` parse untruncated; over
      `max_str_long` they fail; an oversized `accessConstraints` still fails at `max_str_medium`

## 3. Verify

- [x] 3.1 `uv run pytest middleware/` and CI-equivalent ruff / mypy / pylint
- [x] 3.2 Re-run against live `repository.zalf.de` and report the new valid count on #433
