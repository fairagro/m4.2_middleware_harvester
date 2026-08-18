## Why

OpenAgrar Schema.org JSON-LD often has no Dataset `@id`, `url`, or `sameAs`. The DOI sits in a `PropertyValue` (`schema:value`), which `GeneralSchemaOrgMapper._extract_doi` misses. The mapper then uses `str(subject)` — an rdflib blank node that is regenerated on every parse (`N` + 32 hex). The Middleware API hashes `sha256(identifier + ":" + rdi)` as the GitLab path, so each harvest creates a new repo instead of updating. Production already has ~17k OpenAgrar repos from ~916 real records.

## What Changes

- Resolve `Investigation.identifier` from catalog-stable values only, in this order:
  1. DOI from `schema:identifier` (literal `10.…` **or** `PropertyValue` whose `propertyID` is identifiers.org/doi or contains `doi` and whose `value` is `10.…`)
  2. Canonical source URL (`schema:url`, `sameAs`, `http(s)` `@id`) or MyCoRe id from the Receive-URL / Solr `id` (`openagrar_mods_*`)
  3. Otherwise refuse to map: raise a mapping error so the plugin yields `RecordProcessingError` (no upload, no GitLab repo)
- Never use an rdflib blank node (`N`+32 hex, `_:…`) as an identifier. Never invent an id. Never fall back to an 80-character title slug for `Investigation.identifier`.
- Pass the discovery page URL (`Dataset.identifier` / Receive-URL) into Schema.org mapping as a fallback when the JSON-LD graph has no URL/`@id`.
- Keep INSPIRE/DWD URN handling and Regal identifier rules unchanged.

## Non-Goals

- Changing Middleware API hashing (API hashes whatever the harvester sends; a prior API-side fix was reverted on purpose).
- GitLab cleanup of existing `N{uuid}` repos (append-only group).
- Title-slug fallback (eDAL duplicate identifiers in the same run).
- SQL-to-ARC / Edaphobase, INSPIRE CSW, or DWD URN mapping.
- Changing default MyCoRe Solr `fl=id` (Receive-URL already carries the Solr `id`; `mods.identifier` is not required for this mapper).
- Infrastructure values-file edits (those live in `m4.2_infrastructure`).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `linked-data-mapper`: `GeneralSchemaOrgMapper` MUST emit a harvest-stable `Investigation.identifier` and MUST fail closed when none exists.
- `linked-data-harvesting`: the plugin MUST pass the discovered dataset URL into Schema.org `map_graph` so Receive-URL / MyCoRe id is available when the JSON-LD graph has no `@id`/`url`/`sameAs`.

## Impact

- **Affected domains**: `openspec/specs/linked-data-mapper/`, `openspec/specs/linked-data-harvesting/`.
- **Code**: `middleware/linked_data` mapper ABC, `GeneralSchemaOrgMapper`, `RegalMapper` signature compatibility, `LinkedDataPlugin._process_result`; unit tests under `middleware/linked_data/tests/unit/`.
- **Config**: none. Solr `fl=id` stays; operators need not add `mods.identifier` for identifier stability.
- **Dependencies**: none new.
