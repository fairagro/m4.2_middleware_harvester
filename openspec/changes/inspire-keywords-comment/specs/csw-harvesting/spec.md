## ADDED Requirements

### Requirement: IsoParser MUST extract keyword terms from OWSLib MD_Keywords

When parsing ISO 19139 identification metadata into `InspireRecord`, the system MUST populate `InspireRecord.keywords`
with one term per non-empty keyword name from each OWSLib `MD_Keywords` entry on `identification.keywords`. Each term
MUST carry the keyword **name**, and MUST carry the keyword **url** when OWSLib exposes a non-empty `gmx:Anchor`
`xlink:href` on that keyword, and MUST carry the group's thesaurus **title** when present (`thesaurus['title']` or an
equivalent string). Plain `str` list items MUST be accepted as name-only terms. Empty names MUST be omitted. Existing
`inspire-value-bounds` list, string, and URL limits MUST continue to apply unchanged (fail the record on violation; do
not silently truncate). Keyword type and thesaurus URL/date are not required by this requirement.

#### Scenario: MD_Keywords with names, URL, and thesaurus title

- **WHEN** `identification.keywords` is one `MD_Keywords` group with thesaurus title `AGROVOC Keywords` and nested
  keywords `crop rotation` (no URL) and `Germany` with URL `http://example.org/agrovoc/germany`
- **THEN** `InspireRecord.keywords` MUST contain two terms with those names, both with thesaurus `AGROVOC Keywords`, and
  only the second term with that URL

#### Scenario: Plain string keywords become name-only terms

- **WHEN** `identification.keywords` is a list of strings `["a", "b"]`
- **THEN** `InspireRecord.keywords` MUST be two name-only terms `a` and `b` (no url, no thesaurus)

#### Scenario: Empty keyword list stays empty

- **WHEN** `identification.keywords` is missing or empty
- **THEN** `InspireRecord.keywords` MUST be an empty list
