# Design

## Context

Explore lock-in (#603): A1 all keyword mappers; B1 shared helper; C remove Study/protocol Keywords parameters where they
duplicate the Investigation surface; D1 Comments contract (no Investigation OntologyAnnotation keyword lists); Regal
bare-`keyword` fixed as part of the rewrite. Aggregate `Keywords` stays until #604.

`ArcInvestigation` exposes `Comments` / `OntologySourceReferences` only — no native keywords collection. API exports
aggregate Comments as Schema.org `keywords` today; per-term Comments are the input to api#663 DefinedTerm
materialization.

## Goals / Non-Goals

**Goals:**

- One Comment naming contract for every keyword-producing mapper.
- Shared helper for aggregate + per-term emission (unique Comment names within the Investigation).
- Docs + unit tests covering URI, plain, and optional DDC cases.

**Non-Goals:**

- Removing the aggregate `Keywords` Comment (#604).
- API DefinedTerm materialization (api#663).
- Investigation-level OntologyAnnotation keyword lists (#417 superseded path).
- Changing thesaurus title storage beyond what Comments need (INSPIRE may keep thesaurus on `KeywordTerm` unused in
  Comment names for this MVP).

## Decisions

1. **Shared helper in `middleware.payload`** (e.g. `keyword_comments.py`) takes ordered term records
   `{label, term_uri?, ddc_uri?}` (or separate subject vs DDC lists) and mutates `inv.Comments`. Reasoning: one
   uniqueness / join policy; Regal becomes a thin caller.

2. **Comment names**
   - Subject/plain: `keyword [<term_uri>]` if URI non-empty, else `keyword [<label>]` (label trimmed; never bare
     `keyword`).
   - DDC: `keyword [DDC:<class_uri>]` only when class URI present; omit DDC Comment when URI unknown (label alone is not
     enough for DDC Comments).
   - Aggregate name exactly `Keywords`; value = `", "`.join of subject/plain labels after trim / empty-drop /
     casefold-dedupe / sort (casefold then original) — same harvest-stable policy as Schema.org today. DDC labels
     excluded. Reasoning: matches issue table; avoids comma-split on classification text; unique names for ARCtrl.

3. **Uniqueness collisions** If two plain terms casefold-collide to the same `keyword [<label>]` name, keep one Comment
   (same dedupe as aggregate). If URI forms collide, last-write or first-write MUST be deterministic (document: first
   kept after stable sort of terms). Reasoning: Comment names must be unique; prefer stable sort of input terms before
   emit.

4. **MODS / Phenoroam / ckanext protocol Keywords** Remove Parameter `Keywords` from Study/Assay protocol tables when
   Investigation Comments carry the terms. Keep other parameters (e.g. ckanext Language, Processing Description). If a
   Data Collection table becomes empty of columns beyond stub I/O with no remaining parameters, omit the table or keep
   stub only if other columns remain — prefer omit empty Keywords-only tables. Reasoning: one SoT; Study parameters were
   not on the API keyword path.

5. **INSPIRE** Use `KeywordTerm.name` + optional `url` for subject Comments; thesaurus title not encoded in Comment name
   in this issue (optional future). No DDC unless a future mapping appears. Reasoning: parser already retains URL; AC
   allows optional classification.

6. **ckanext aggregate separator** Align Investigation aggregate to `", "` (Schema.org / Regal / INSPIRE). Today ckanext
   uses `"; "` on Comments — change to `", "` for the shared helper. Reasoning: uniform aggregate contract; note in docs
   as intentional align.

## Risks / Trade-offs

- **Breaking RO-Crate shape** for MODS/Phenoroam/ckanext consumers that read protocol Keywords — accepted; Search Hub
  path is Comments.
- **ckanext `"; "` → `", "`** may change exported keyword strings slightly — intentional.
- **Large plain-label sets** → many Comments; acceptable for ARC size vs losing term boundaries.
- **Ad-hoc Regal subject URIs** remain as `keyword [<uri>]` (Publisso source quality; not this issue).
