## Context

JSON-LD `@list` values parse to `rdf:first` / `rdf:rest` chains. RDF assigns no order to repeated predicates, but a list
is ordered, and author order is meaningful, so list members are taken in list order rather than StableGraph sort order.

## Decisions

- **List walking lives in `ResourceView`** (`is_list`, `list_members`), not in the Regal mapper, so RDF structure
  reading stays in the StableGraph layer and other mappers can reuse it. `resources()` is unchanged; callers filter list
  heads with `is_list`, so no existing mapper changes behaviour.
- **Own walker instead of `rdflib.collection.Collection`**: `Collection` loops forever on a cyclic list; the walker
  stops at `rdf:nil`, a missing `rdf:rest`, or a revisited cell.
- **Order inside a predicate**: direct literals, list members, direct resources. Several list heads on one predicate
  (not seen in Publisso) are concatenated in `sort_key` order, which keeps the result harvest-stable.
- **Warning, not failure**, for an unlabelled agent: one bad entry must not drop the record; the warning makes the gap
  visible in logs.
