# Design

## Context

See proposal.md — Why. Live CSW `identification.keywords` is a list of OWSLib `MD_Keywords` (nested `Keyword.name` /
`Keyword.url`, optional `thesaurus['title']`). Dropping URI at parse time is irreversible; #603 only defines how typed
keywords are written into ARC Comments later.

## Goals / Non-Goals

**Goals:**

- Persist keyword **name** plus optional **url** and **thesaurus** title on `InspireRecord`.
- Emit one deterministic aggregate `Keywords` Comment from names for Search Hub.
- Align `docs/mappers/inspire.md`.

**Non-Goals:**

- Per-term ARC Comments / OntologyAnnotation emission (#603).
- Protocol-table `Keywords` parameter on INSPIRE Study/Assay.
- Inferring ontology URIs from plain labels.

## Decisions

1. **`KeywordTerm` nested model** — `name: RequiredMediumStr`, `url: OptionalUrl`, `thesaurus: MediumStr | None`.
   Bounds/URL scheme checks reuse existing nested-model validation.
   - Alternative: parallel lists / keep `list[str]` → rejected; loses URI with no recovery path.

2. **Coerce bare strings → `{name: …}`** — Field `BeforeValidator` so existing tests and plain-string CSW edge cases
   keep working; placeholders still strip string list items on `InspireRecord` before coerce.

3. **Thesaurus = citation title only** — Copy `thesaurus['title']` (or a string mock) onto each term from that group.
   Thesaurus URL/date/type not stored in this slice (can extend later without ARC contract change).

4. **Mapper uses names only** — Same Schema.org-style trim / casefold-dedupe / sort / `", "` join. URI/thesaurus ignored
   until #603 writing lands.

5. **Comment only, no OntologyAnnotation** — Matches API Comments lock-in.

## Risks / Trade-offs

- **[Risk] Aggregate join vs commas in labels** → Known; #604 / API per-term path.
- **[Risk] Thesaurus URL unused** → Acceptable; title is enough to label AGROVOC vs GEMET for a later writer.
- **[Trade-off] Model churn for callers passing `list[str]`** → Mitigated by coerce validator.

## Migration Plan

- Ship with next harvester release; no config flag.
- Rollback: revert; prior behaviour was empty keywords.

## Open Questions

- None.
