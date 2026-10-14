# Tasks

## 1. Licence

- [x] 1.1 `inspire_license` reads GDI-DE JSON licences as `name (url)`, tolerating malformed JSON

## 2. Tests

- [x] 2.1 Unit tests with the live DWD constraints: valid JSON, no name, malformed JSON, no http(s) URL

## 3. Docs

- [x] 3.1 `docs/mappers/inspire.md` licence order

## 4. Verify

- [x] 4.1 `uv run pytest middleware/`, CI-equivalent quality checks
- [x] 4.2 Live DWD harvest (parser + mapper): 74 of 82 records get a licence (58 before)
