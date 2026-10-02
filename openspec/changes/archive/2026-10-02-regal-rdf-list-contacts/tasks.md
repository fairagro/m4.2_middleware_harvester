## 1. StableGraph

- [x] 1.1 `ResourceView.is_list` and `ResourceView.list_members` with nil / cycle / missing-rest handling
- [x] 1.2 Unit tests in `test_stable_graph.py`

## 2. Regal mapper

- [x] 2.1 `_add_contacts` resolves list members in order for creator and contributor
- [x] 2.2 Warning for agent resources without `skos:prefLabel`
- [x] 2.3 Publication authors use `F. Last`
- [x] 2.4 Tests with trimmed real `/find` payload `frl:6420709` (inline context, no network), contributor org, empty
      list, unlabelled member

## 3. Validation

- [x] 3.1 `uv run ruff format` / `ruff check` / mypy / pylint on affected paths
- [x] 3.2 `uv run pytest middleware/payload`
- [x] 3.3 Live Publisso `/find` (92 records): 0 → 406 author + 76 contributor Persons, 0 failures
