## Why

Every Publisso ARC is published without authors or contributors (92/92 records in the 2026-10-02 DataHUB export), although
the source lists them with ORCIDs. The Publisso context declares `creator` / `contributor` as `@list`, so rdflib emits one
triple per predicate pointing at an `rdf:List` head. `RegalMapper._add_contacts` treated that head as the agent, found no
`skos:prefLabel` and returned silently.

Tracked as GitHub [#403](https://github.com/fairagro/m4.2_middleware_harvester/issues/403).

## What Changes

- `ResourceView.is_list` / `ResourceView.list_members(*predicates)` in `stable_graph.py`: ordered `rdf:List` members,
  `rdf:nil` → empty, cycle / missing-`rest` guard.
- `RegalMapper._add_contacts` maps direct literals, then list members (list order), then direct non-list resources, for
  `dcterms:creator` (author) and `dcterms:contributor` (contributor).
- An agent resource without `skos:prefLabel` logs a warning instead of being skipped silently.
- Publication authors switch from `Last, F.` to `F. Last`: with authors now present, the comma form made the RO-Crate
  writer emit fragment `#Author_ D.; Willink` Person nodes.

### Non-goals

- Sorting Contacts by `contributorOrder`. (Note: Publisso uses `http://purl.org/lobid/lv#contributorOrder`, not
  `regal:contributorOrder`; follow-up.)
- INSPIRE mapper's identical `Last, F.` Publication authors form (follow-up).

## Capabilities

### Modified Capabilities

- `regal-to-arc-mapping`: `rdf:List` creators/contributors in list order; Publication authors form.

## Impact

- `middleware/payload/.../linked_data_mapper/stable_graph.py`, `regal_mapper.py`; unit tests + fixture
  `regal_frl_6420709.json`.
- Live check (92 `/find` records): 0 → 406 author and 76 contributor Persons, 9 organization `Contributor` Comments,
  0 failures. Existing Publisso ARCs change content and are re-pushed once.
