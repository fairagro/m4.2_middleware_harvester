## Context

See proposal.md. OpenAgrar Schema.org JSON-LD often carries multiple `schema:keywords`, multiple language-tagged `schema:description` literals, and unordered creator nodes. `graph.value` and unsorted `graph.objects` make harvest output oscillate; ARCtrl then derives new Comment / Author node `@id`s and the Middleware sees a content change.

## Goals / Non-Goals

**Goals:**

- Bit-stable Schema.org → ARC mapping for keywords, description (multi-literal), and contacts/publication authors under fixed source data.
- Document the sort and language policies in code comments / this design.

**Non-Goals:**

- API `content_hash` / order-insensitive hashing changes.
- Regal mapper, INSPIRE mapper.
- Swallowing real source edits (only stabilize order and multi-value selection).

## Decisions

1. **Keywords: trim + Unicode code-point sort (`sorted(…, key=str.casefold)` then original for stable case)**
   — Reasoning: case-insensitive primary order avoids `A`/`a` flip-flops while remaining deterministic; empty strings after trim are dropped; join remains `", "`.

2. **`_str` / `_obj`: choose among all objects with language preference `en` > `de` > untagged > other langs; empty discarded; ties by longer text then lexicographic `casefold`**
   — Reasoning: matches observed OpenAgrar DE/EN + empty literal churn; applies to all `_str` call sites so name/license/etc. do not reintroduce non-determinism.

3. **`_strs`: return sorted unique trimmed strings (casefold key)**
   — Reasoning: keywords and any multi-value comment lists stay stable.

4. **Contacts: collect nodes per role, sort by `(family.casefold, given.casefold, name.casefold, str(node))`, then append**
   — Reasoning: stable without inventing ids; Publication authors follow Contact order.

5. **Publication author format: `F. Last` (initial + space + last) instead of `Last, F.`**
   — Reasoning: removes the comma that ARCtrl splits into broken `#Author_` nodes, without depending on hash workarounds. Still derived from sorted Contacts.

## Risks / Trade-offs

- **First harvest after deploy changes GitLab/API content once** → intended; subsequent harvests stabilize.
- **Language preference may drop a longer DE text when EN exists** → accepted; preference is explicit and stable.
- **Author display string shape changes** → once; improves correctness of Author nodes.

## Migration Plan

- Deploy harvester only.
- Rollback: revert mapper; order churn resumes.
