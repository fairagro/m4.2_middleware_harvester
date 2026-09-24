## Context

`middleware/inspire/src/middleware/inspire/csw_client.py` imports OWSLib and `lxml.etree`. It makes exactly one
`lxml.etree.fromstring` call of its own (`_prepare_xml_paging`, parsing the operator-supplied `xml_query`); every CSW
_response_ is parsed inside OWSLib (`owslib/util.py`, `owslib/iso.py`), which exposes no parser argument.

The only lever over OWSLib's internal parsing is lxml's process default parser — which is precisely what OWSLib mutates
at import time. See proposal.md for the verified behaviour. Related: `openspec/specs/csw-threadpool/` (parsing runs in a
bounded `ThreadPoolExecutor`), `openspec/specs/xml-sitemap-parser/` (the `defusedxml` precedent on the Linked Data
path).

## Goals / Non-Goals

**Goals:**

- Make XML hardening on the CSW path an explicit, tested property of this repository.
- Keep behaviour identical to today, so this is a safety/clarity change rather than a functional one.
- Fail CI if entity resolution is ever re-enabled, including inside the CSW thread pool.

**Non-Goals:**

- `defusedxml` on the lxml path (deprecated upstream).
- Reimplementing OWSLib's XML or HTTP handling.
- Bounding response size or validating harvested values (#20).

## Decisions

1. **Explicit `lxml.etree.XMLParser` rather than `defusedxml`** — `defusedxml.lxml` is deprecated and warns on import,
   so the literal remedy in #16 is unavailable. An explicit parser with
   `resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False` gives the same protections (no entity
   expansion, no external fetches, no DTD loading, bounded tree depth/size). _Alternative considered:_ switching the CSW
   path to stdlib `ElementTree` + `defusedxml` — rejected, it would mean reimplementing OWSLib's ISO parsing.

2. **Install it as the process default parser from a dedicated `xml_hardening` module that imports `owslib.etree`
   itself** — Installing a default parser is the only way to cover OWSLib's internal response parsing, which takes no
   parser argument. It must happen _after_ OWSLib's own import-time `set_default_parser`, or ours is overwritten.
   Putting both the `owslib.etree` import and our `set_default_parser` call in one small module makes that ordering a
   property of the module rather than of whichever module happens to import what first. _Alternative considered:_ the
   call inline in `csw_client.py` after its OWSLib imports — works, but the guarantee then depends on import order in a
   1000-line module, and it pushed that module past the pylint `max-module-lines` limit. _Alternative considered:_ leave
   OWSLib's parser in place and merely assert its behaviour in a test, pinning a minimum OWSLib version. Rejected as the
   primary mechanism — it documents the dependency instead of removing it — but the behavioural test below still guards
   the outcome either way, so an OWSLib change cannot silently regress us.

3. **`remove_comments=True` is included deliberately, to preserve OWSLib's behaviour** — OWSLib's own default parser
   sets it. Omitting it would leave comment nodes in trees OWSLib iterates, a behaviour change unrelated to security.
   Verified equivalent: with either parser installed, a namespaced ISO snippet yields the same `fileIdentifier` text and
   zero comment nodes.

4. **Accepting global-parser mutation as a deliberate, documented choice** — Global mutable state is normally worth
   avoiding, and lxml warns that the default parser is not thread-safe. We adopt it anyway because (a) it is the only
   lever over OWSLib internals, (b) the process already lives with it via OWSLib, and (c) worker threads inherit a copy
   of the main thread's default parser at creation, which the tests assert. The parser object is created once at import
   and never mutated afterwards, so there is no cross-thread write.

5. **Tests assert outcomes, not parser flags** — lxml parser flags are not introspectable
   (`getattr(parser, "resolve_entities")` does not exist), so the regression tests parse hostile documents and assert
   what comes out. For external entities the failure mode differs by thread (main thread yields empty text; a worker
   raises `XMLSyntaxError`), so the assertion is that local file contents never appear — not one specific exception.

## Risks / Trade-offs

- **Import-side-effect ordering.** Our `set_default_parser` call must follow OWSLib's. The `xml_hardening` module
  imports `owslib.etree` immediately before making the call, so the order holds however the module is reached; the
  entity tests would catch a regression regardless.
- **Process-wide reach.** The default parser affects any other lxml user in the process. Today there is none:
  `linked_data` parses sitemaps with `defusedxml.ElementTree` (stdlib-backed, unaffected) and RDF as JSON-LD.
- **Not a complete threat model.** This closes entity/DTD/network vectors. Response size limits and harvested-value
  bounds remain open under #20.
