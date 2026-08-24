## 1. Deterministic graph helpers

- [x] 1.1 Replace `_str` / `_obj` multi-value selection with language-preferring, empty-dropping, deterministic tie-break policy
- [x] 1.2 Make `_strs` return trimmed, deduplicated, casefold-sorted strings
- [x] 1.3 Apply sorted keywords join in Investigation comments and Data Collection protocol

## 2. Contacts and publications

- [x] 2.1 Sort creator / author / contributor nodes by stable key before appending Contacts
- [x] 2.2 Format Publication authors as `F. Last` (no comma) from sorted Contacts

## 3. Tests and validation

- [x] 3.1 Keywords order-invariance test
- [x] 3.2 Description multi-literal + empty + language preference test; double-map identical
- [x] 3.3 Contacts / publication-authors order-invariance test
- [x] 3.4 Full fixture double-map regression for description, keywords, contacts, authors
- [x] 3.5 `uv run pytest middleware/linked_data/tests -v --tb=short` and ruff check/format on changed paths
