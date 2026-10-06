## 1. Implementation

- [x] 1.1 `arc_comments.unique_comment_names` and `drop_date_modified_comment_node`, applied in
      `HarvestedArc.from_arctrl`
- [x] 1.2 Unit tests, including the API path (read back + `ARC.Write`)
- [x] 1.3 Docs: `regal_mapping.md`, `schemaorg_mapping.md`, `inspire_mapping.md`

## 2. Validation

- [x] 2.1 ruff, mypy, pylint, bandit
- [x] 2.2 `uv run pytest middleware/`
- [x] 2.3 Live Publisso, BonaRes + Thünen, e!DAL through the API's read + `ARC.Write` (arctrl 3.2.2)
