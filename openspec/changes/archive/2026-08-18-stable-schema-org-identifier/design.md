## Context

See proposal.md for motivation. `GeneralSchemaOrgMapper._map_investigation` currently sets

`identifier = doi or str(subject) or title_slug`, then slugifies any non-DOI value that contains `/` or `://`. `_extract_doi` uses `graph.value(..., schema:identifier)` and `str(...)`, so a `PropertyValue` node never looks like `10.…`. Blank-node Dataset subjects therefore become a new `N{32hex}` string on every rdflib parse. The API hashes that string into a new GitLab path.

OpenAgrar HTML JSON-LD typically has no Dataset `@id`/`url`/`sameAs`. The stable catalog keys are the DOI (when present as `PropertyValue`) and the MyCoRe Receive-URL already known at discovery (`HtmlJsonLdDataset.identifier`).

## Goals / Non-Goals

**Goals:**

- Harvest-stable `Investigation.identifier` for Schema.org / OpenAgrar.
- Fail closed (record-level `RecordProcessingError`) when no catalog id exists.
- Keep Regal and INSPIRE identifier logic unchanged.

**Non-Goals:**

- Changing Solr default `fl=id` (Receive-URL already embeds Solr `id`).
- Shared identifier helper across INSPIRE and linked_data.
- Repairing historical GitLab repos.

## Decisions

1. **DOI first, then URL / MyCoRe id, then error**
   — Reasoning: DOI is the scholarly persistent id (~91% of OpenAgrar research_data). The remaining records still have a MyCoRe id on every Receive-URL. Inventing a title slug collides (eDAL). Blank nodes are parser-internal, not dataset ids.

2. **Walk every `schema:identifier` object; read `PropertyValue.schema:value`**
   — Reasoning: `graph.value` returns the node, not the nested `value`. OpenAgrar encodes DOI as `PropertyValue` with `propertyID` identifiers.org/doi. Literal `10.…` identifiers stay supported. `propertyID` matching is case-insensitive substring `doi` plus the identifiers.org DOI registry URI.

3. **Pass `source_url` into `map_graph`, do not inject triples**
   — Reasoning: the page URL is discovery context, not a statement in the JSON-LD. Optional `source_url: str | None = None` on `LinkedDataMapper.map_graph` keeps the ABC compatible; `RegalMapper` ignores it. The plugin passes `dataset.identifier` (Receive-URL for HTML JSON-LD).

4. **Keep the discovered Receive-URL and sanitize it**
   — Reasoning: The harvester passes the discovered page URL into Schema.org mapping as a stable context. The mapper produces an `arctrl`-compatible identifier by stripping the scheme and replacing forbidden characters. Generic `http(s)` landing URLs are kept as-is (aside from the same sanitization).

5. **Raise `ValueError` (mapping error), not `SkippedRecord`**
   — Reasoning: `SkippedRecord` is for deliberate omissions (duplicate discovery). Missing identity is a data-quality failure: no upload, and the orchestrator records a failed dataset / report issue via existing `RecordProcessingError` wrapping in `LinkedDataPlugin._process_result`.

6. **Do not change Solr `fl`**
   — Reasoning: `fl=id` is enough to build `{host}/receive/{id}`. `mods.identifier` would duplicate the DOI already in HTML JSON-LD for most records and is unused by this mapper. Values-file changes belong in `m4.2_infrastructure` only if a future mapper needs Solr DOIs without fetching HTML.

## Risks / Trade-offs

- **Existing GitLab repos keyed by `N{uuid}` will not be updated** → accepted; group is append-only. New harvests create the first stable path per record; old clones stay orphaned.
- **Identifier values change from title slugs / blank nodes to DOI or MyCoRe id** → first harvest after deploy creates new GitLab paths for OpenAgrar (intended). Other Schema.org sources that previously slugified `http(s)` `@id` will start using the URL or Receive-id instead of the title slug.
- **~9% OpenAgrar records without DOI depend on plugin-supplied Receive-URL** → if mapping is invoked on a graph alone in tests, those fixtures must pass `source_url` or include an `http(s)` `@id`.

## Migration Plan

- Deploy harvester only. No API or GitLab migration.
- Rollback: revert the mapper; blank-node churn resumes.
