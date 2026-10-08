## Why

Harvested INSPIRE CSW/ISO-19139 values reach an ARC with type-guards but essentially no validation.
`openspec/principles.md`'s "Security by default" rule treats endpoint input as untrusted; today it is not treated that
way in practice:

- **No length limits anywhere.** `title`, `abstract`, `lineage`, every constraint string, every `Contact` field — a
  hostile or misconfigured CSW server can return arbitrarily large strings for any of these, all the way into an ARC.
- **No list-count limits anywhere.** `keywords`, `contacts`, `resource_identifiers`, `conformance_results` and a dozen
  other list fields on `InspireRecord` are sized directly by the server's response.
- **No real URL-scheme validation.** The only check anywhere is a loose `code.startswith("http")` on one field
  (`ResourceIdentifier.url`); every other URL field — including `OnlineResource.url`, the download link — is passed
  straight through. `javascript:`, `file:`, `data:` URIs are all accepted verbatim.
- **Coded fields are free text.** `language`, `charset`, `hierarchy`, `status`, `Contact.role`, `InspireDate.datetype`
  and `topic_categories` are ISO 19139 codelist / ISO 639-2 values, but any string is accepted.
- **INSPIRE duplicates rather than reuses existing identifier sanitization**, never sanitizes a raw (non-URL-shaped)
  `fileIdentifier`, and falls back to the placeholder identifier `"untitled"`.

Tracked as [#20](https://github.com/fairagro/m4.2_middleware_harvester/issues/20). Codelist/format validation overlaps
[#132](https://github.com/fairagro/m4.2_middleware_harvester/issues/132); after review it is included here because it
lives on the same model fields.

## What Changes

- **Validation, not sanitization.** All limits are constraints on the `InspireRecord` Pydantic model (and its nested
  models). A violating record raises `ValidationError`, which the existing `_yield_iso_records` handling turns into a
  `RecordProcessingError` — the record is reported as failed. Values are never truncated or dropped: truncation could
  make distinct records collide (e.g. two long `fileIdentifier`s sharing a prefix mapping to one ARC).
- **Configurable limits.** New `Config.value_bounds` (`ValueBounds`): `max_str_short` (200), `max_str_medium` (1,000),
  `max_str_long` (10,000), `max_list_items` (500), `allowed_url_schemes` (`http`, `https`, `ftp`). `IsoParser` passes
  them to the model via the Pydantic validation context.
- **Codelists and formats.** `charset` (MD_CharacterSetCode), `hierarchy` (MD_ScopeCode), `status` (MD_ProgressCode),
  `Contact.role` (CI_RoleCode), `datetype` (CI_DateTypeCode), `topic_categories` (MD_TopicCategoryCode) — including the
  ISO 19115-1 additions; `language`/`resource_language` as ISO 639-2 three-letter codes; `date_stamp` and dates as ISO
  8601; a loose e-mail shape; conformance `degree` as `gco:Boolean`; `dataset_uri` as URL or URN.
- **Identifiers.** `middleware.payload.identifiers` (the module `LinkedDataMapper` already delegates to) is reused by
  `InspireMapper`. Every investigation identifier is allowlist-sanitized. Study/assay identifiers fall back from the
  title slug to the sanitized `fileIdentifier`; if nothing usable remains, mapping raises `ValueError`. The `"untitled"`
  placeholder is removed.
- **Config.** `csw_url` must be http(s) — a functional constraint (OWSLib uses `requests`), hence hardcoded.
  `max_records` keeps `ge=1` and no arbitrary ceiling.

## Non-Goals

- **Plausibility checks** — out-of-range bounding boxes, reachable URLs, sane map scales. Format/codelist conformance is
  checked; whether a conformant value is _true_ is not.
- **Response-body-size limiting.** Belongs to the HTTP transport layer (`http_pooling.py`/OWSLib), not value validation.
- **Sanitizing instead of rejecting.** Deliberately not done (see What Changes). The mapper's pre-existing
  `individualName` and spatial-distance handling are unchanged.
- **INSPIRE routing through `middleware.payload`'s `DataMapper` pipeline.** Only two plain functions are reused.

## Capabilities

### New Capabilities

- `inspire-value-bounds`: Configurable length/count/URL-scheme limits and codelist/format validation for harvested
  INSPIRE CSW/ISO-19139 values, enforced on `InspireRecord`; placeholder-free identifier derivation; `csw_url` scheme
  check.

### Modified Capabilities

- (none)

## Impact

- **Code**: `middleware/inspire/src/middleware/inspire/{config.py,iso_parser.py,csw_client.py}` and
  `middleware/payload/src/middleware/payload/inspire/{value_bounds.py,models.py,mapper.py}` (`ValueBounds` lives beside
  `InspireRecord` because `middleware.payload` must not import protocol plugins; `mapper.py` now imports
  `sanitize_identifier`/`to_identifier_slug` from the existing `middleware.payload.identifiers` module); unit tests
  under `middleware/inspire/tests/unit/` and `middleware/payload/tests/unit/`.
- **Config**: new optional `value_bounds` section (all fields defaulted); `csw_url` scheme check. Existing YAML stays
  valid unless `csw_url` is not http(s).
- **Behaviour**: records violating a limit, codelist or format are reported as failed instead of harvested. Measured on
  1,500 GDI-DE records (`gdk.gdi-de.org`) and the ZALF repository: 3 new failures (0.2%), all junk `dataSetURI` values
  (`I`, `?ResourceName=`, `G:\...`). Records whose title yields no slug now use the `fileIdentifier` instead of
  `"untitled"`.
- **Dependencies**: none new.
