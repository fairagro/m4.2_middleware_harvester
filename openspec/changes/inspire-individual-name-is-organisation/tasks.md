# Tasks

## 1. Config and mapper

- [x] 1.1 `MapperConfig.individual_name_is_organisation` (bool, default `false`) with description
- [x] 1.2 `InspireMapper(*, individual_name_is_organisation=False)` and `from_config`; `_add_contacts` routes every
      `individualName` to the role Comment path when set

## 2. Tests

- [x] 2.1 Mapper tests with the live DWD names: Comment and no Person when set, `Creator Organization` for creator
      roles, Person unchanged when unset; `from_config` passes the setting

## 3. Docs and examples

- [x] 3.1 `docs/mappers/inspire.md` individualName row; in-repo DWD examples set the flag

## 4. Verify

- [x] 4.1 `uv run pytest middleware/`, CI-equivalent quality checks, Prettier on Markdown
- [x] 4.2 Live DWD harvest (parser + mapper) with the flag: no Person left
