# OpenAgrar fixture RDI

A static stand-in for OpenAgrar, served over HTTP so the real harvester binary can be run end-to-end against a
`mycore_solr` + `html_jsonld` + `schema_org_general` source.

## Why this exists

OpenAgrar gates anonymous traffic behind a proof-of-work challenge. Every path the harvester uses — record pages,
`servlets/solr/select`, and the `sitemap_google.xml` advertised in `robots.txt` — responds `302 → /pow-challenge`. The
live repository therefore cannot be harvested at all, which is tracked in
[#271](https://github.com/fairagro/m4.2_middleware_harvester/issues/271).

Without a stand-in there is no way to exercise the
[#164](https://github.com/fairagro/m4.2_middleware_harvester/issues/164) title-fallback cascade against the real binary.

## Provenance — what is real and what is not

`receive/openagrar_mods_00110150/` is the record #164 reports as failing. Its bibliographic values are the record's
**real** ones, taken from OpenAgrar's own `https://www.openagrar.de/api/v2/objects/openagrar_mods_00110150` (MODS XML),
which is not behind the gate:

| Field     | Value                                                                                                                           |
| --------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Title     | Trap nest and laboratory experiment data used to investigate pith diameter preferences of the digger wasp _Pemphredon lethifer_ |
| DOI       | `10.5073/20250926-163035-0`                                                                                                     |
| Creators  | Furtwengler, Jana; Böckman, Elias                                                                                               |
| Issued    | 2026-08-03                                                                                                                      |
| Licence   | CC-BY-4.0                                                                                                                       |
| Data file | `Raw_data_diameter_preference_Pemphredon_lethifer_laboratory.xlsx` (derivate `openagrar_derivate_00067866`)                     |

The **JSON-LD block is reconstructed**, not captured — the live page that would carry it is gated. It reproduces the
field mix #164 describes: a `Dataset` with no `name`, no `headline` and no `alternativeHeadline`, so the title can only
come from the page. The MODS record proves the dataset really does have a title upstream and that only the schema.org
export drops it.

`robots.txt` is a verbatim copy of the real one, fetched from the live site (it is not gated).

Every other record under `receive/` is **synthetic**, named `fixture_*`, and exists to pin one step of the cascade.

## The records

| Record                      | Cascade step exercised                                       | Expected resolved title source                                      |
| --------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------- |
| `openagrar_mods_00110150`   | 4 — HTML `citation_title`                                    | `html_title`                                                        |
| `openagrar_mods_00108436`   | none — control, `schema:name` present                        | no `Title Source` Comment at all                                    |
| `fixture_headline_only`     | 2 — `schema:headline`                                        | `headline`                                                          |
| `fixture_altheadline_only`  | 3 — first `schema:alternativeHeadline` in **document order** | `alternativeHeadline`                                               |
| `fixture_page_title_only`   | 4 — page `<title>`, no `citation_title`                      | `html_title`                                                        |
| `fixture_no_title_anywhere` | none — nothing resolves                                      | **must fail closed on every branch**                                |
| `fixture_ordertest`         | 3 — ordering of multiple `alternativeHeadline` values        | `alternativeHeadline`, resolving to `Apple is alphabetically-first` |

`fixture_altheadline_only` and `fixture_ordertest` pin the ordering of multiple `alternativeHeadline` values. RDF gives
no ordering to repeated predicates — there is no `@list` involved — so the order the mapper observes is an artefact of
the rdflib store rather than of the source document. Running from source and running the shipped PyInstaller binary
disagreed on exactly this, which is how it was found. The mapper therefore picks the casefold-alphabetical value
deliberately, and both fixtures assert that: `Alpha …` and `Apple is alphabetically-first`. `fixture_ordertest` uses
three values so that document, alphabetical and reverse-document order each select a different winner; a two-value
fixture cannot tell them apart.

## How it is served

`python -m http.server` strips the query string in `translate_path`, so the static file at `servlets/solr/select`
answers the paginated Solr requests the `mycore_solr` sitemap issues (`?q=*:*&fl=id&rows=…&wt=json&start=…`). Pagination
terminates because the envelope sets `response.numFound` equal to `len(response.docs)`.

Record URLs are built by `MycoreSolrSitemap` as `{scheme}://{netloc}/receive/{id}`, which maps onto the
`receive/<id>/index.html` layout.

```bash
uv run python -m http.server 8080 --directory dev_environment/fixtures/openagrar
```

`config.fixtures.yaml` sets `respect_robots_txt: false`, matching the real OpenAgrar config — the copied `robots.txt`
disallows `/servlets/`, which is where the Solr API lives.
