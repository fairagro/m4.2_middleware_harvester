## 1. Implementation

- [x] 1.1 `orcid_id` / `add_contact` in `person_contacts` with unit tests
- [x] 1.2 Schema.org mapper: ORCID from `@id` / `identifier`, merge into name-matched creator
- [x] 1.3 Regal mapper: `Person.ORCID` instead of `ORCID` Comment; contacts via `add_contact`
- [x] 1.4 Docs: `schemaorg_mapping.md`, `regal_mapping.md`

## 2. Validation

- [x] 2.1 ruff, mypy, pylint, prettier
- [x] 2.2 `uv run pytest middleware/`
- [x] 2.3 Live e!DAL and Publisso counts (see proposal Impact)
