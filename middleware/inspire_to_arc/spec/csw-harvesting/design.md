# CSW Harvesting Design

## Key Decisions

— Using an explicit dual-pass stable ID mechanism (extracting DC then full ISO).
Some CSW servers behave differently under pagination, yielding records in unexpected orders when sorting is ambiguous. By locking onto the quick Dublin Core identifier strings, if the ISO parse shifts, we detect the `Alignment mismatch` but continue.

— Returning `RecordProcessingError` inside the generator.
Because OWSLib fetching can throw arbitrary network and XML parse faults in `_yield_records_with_stable_ids`, we yield out an error entity rather than raising the exception. This lets `main.py` explicitly log the fault without crushing the iterator generator.

— Encompassing `MD_Metadata` parsing into an inner comprehensive `InspireRecord`.
While we technically get `MD_Metadata` from OWSLib, we map these immediately into `InspireRecord` (a pure Pydantic model with cleanly typed arrays of strings, Contacts, and Constraints). By dropping OWSLib as early as possible, the `mapper` no longer needs to deal with vague `str | list | ElementMap` returns.
