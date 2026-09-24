## Why

The INSPIRE plugin parses XML from two untrusted-ish sources: operator-supplied `xml_query` templates, and CSW server
responses parsed inside OWSLib. Neither is hardened by anything this repository writes.

Entity expansion happens to be disabled today, but only as a side effect: OWSLib 0.36.0 runs
`etree.set_default_parser(etree.XMLParser(resolve_entities=False, remove_comments=True))` at import time
(`owslib/etree.py:31-33`), mutating lxml's **global** default parser. Verified in this venv: with OWSLib imported,
`<!DOCTYPE d [<!ENTITY a "X">]><d>&a;</d>` yields `text=None`; without it, the same document expands to `X`.

That is an undocumented, upgrade-fragile guarantee on global mutable state, in a code path that parses inside a
`ThreadPoolExecutor` (`openspec/specs/csw-threadpool/`). No test would catch an OWSLib upgrade that dropped the patch,
and `openspec/specs/csw-harvesting/` carries no XML-safety requirement at all — unlike the Linked Data sitemap path,
which has both `defusedxml` and a "Safe XML parsing" requirement (`openspec/specs/xml-sitemap-parser/spec.md`).

Tracked as [#16](https://github.com/fairagro/m4.2_middleware_harvester/issues/16).

## What Changes

- Install an explicitly configured hardened lxml parser as the process default from `middleware.inspire`, after the
  OWSLib import, so the guarantee is ours rather than incidental.
- Pass that parser explicitly to the one `lxml.etree.fromstring` call this repo owns (`_prepare_xml_paging`).
- Add behavioural regression tests: internal entities are not expanded, external `SYSTEM` entities never yield local
  file contents, on the main thread and inside a worker thread.
- Record the requirement under a new `csw-xml-hardening` capability.

## Non-Goals

- Using `defusedxml` on this path. `defusedxml.lxml` is deprecated upstream ("no longer supported and will be removed in
  a future release"), so the original wording of #16 is not implementable; the equivalent control is an explicit
  `lxml.etree.XMLParser`.
- Replacing OWSLib's XML handling or HTTP layer (see `openspec/specs/async-concurrency/` decision 1 and
  `openspec/changes/archive/2026-08-11-inspire-csw-ssl-verify/design.md`).
- Response body size limits or harvested-value validation — that is
  [#20](https://github.com/fairagro/m4.2_middleware_harvester/issues/20).
- Changing the Linked Data sitemap path, which is already hardened with `defusedxml`.

## Capabilities

### New Capabilities

- `csw-xml-hardening`: Explicitly configured lxml parser hardening for INSPIRE CSW XML parsing.

### Modified Capabilities

- (none)

## Impact

- **Affected domains**: new `openspec/specs/csw-xml-hardening/`; adjacent to `csw-harvesting` (which parses the
  documents) and `csw-threadpool` (which parses them off the event loop).
- **Code**: `middleware/inspire/src/middleware/inspire/csw_client.py`; new unit tests under
  `middleware/inspire/tests/unit/`.
- **Config**: none.
- **Dependencies**: none new. Removes a silent behavioural dependency on OWSLib's import-time global parser.
- **Behaviour**: none intended. The installed parser is behaviourally equivalent to the one OWSLib installs today
  (verified: comments removed, namespaced lookups unchanged, entities unexpanded).
