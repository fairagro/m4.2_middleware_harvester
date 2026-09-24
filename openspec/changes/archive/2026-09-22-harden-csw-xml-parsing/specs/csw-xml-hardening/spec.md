## Purpose

Guarantees that XML reaching the INSPIRE CSW path — operator-supplied `xml_query` templates and CSW server responses
parsed inside OWSLib — is processed by an explicitly hardened lxml parser, so entity expansion, DTD loading and network
retrieval cannot be triggered by remote content.

## ADDED Requirements

### Requirement: The INSPIRE package installs an explicitly hardened lxml parser as the process default

The system SHALL construct an `lxml.etree.XMLParser` with `resolve_entities=False`, `no_network=True`, `load_dtd=False`
and `huge_tree=False`, and SHALL install it via `lxml.etree.set_default_parser` when `middleware.inspire` CSW support is
imported. Installation SHALL occur after OWSLib's own import-time `set_default_parser` call so that this parser, not
OWSLib's, is in effect; the module performing the installation SHALL import `owslib.etree` itself so the ordering does
not depend on import order elsewhere. The parser SHALL also set `remove_comments=True` to preserve OWSLib's existing
tree shape.

#### Scenario: Hardening is owned by this repository

- **WHEN** the CSW client module has been imported
- **THEN** the lxml default parser in effect is the one this package configured, and XML hardening does not depend on
  OWSLib's import-time side effect

#### Scenario: Comment handling is unchanged

- **WHEN** a namespaced ISO 19139 document containing an XML comment is parsed with the installed default parser
- **THEN** element lookups return the same values as before and no comment nodes appear in the tree

### Requirement: Internal entity declarations are not expanded

The system SHALL NOT expand internal entity declarations when parsing XML on the CSW path.

#### Scenario: Internal entity in a CSW payload

- **WHEN** a document declaring `<!ENTITY a "EXPANDED">` and referencing `&a;` is parsed
- **THEN** the referencing element's text does not contain `EXPANDED`

### Requirement: External entities never yield local or remote content

The system SHALL NOT resolve external entities when parsing XML on the CSW path. Parsing MAY fail with `XMLSyntaxError`
or yield empty text — both are acceptable — but the referenced resource's contents SHALL NOT appear in the parse result.

#### Scenario: XXE attempt against a local file

- **WHEN** a document declaring `<!ENTITY x SYSTEM "file:///etc/hostname">` and referencing `&x;` is parsed
- **THEN** either an `XMLSyntaxError` is raised or the element text is empty, and in neither case does the file's
  content appear in the result

### Requirement: Hardening applies inside the CSW thread pool

The system SHALL ensure the hardening applies to parses performed on the worker threads used for OWSLib calls, not only
on the thread that imported the module.

#### Scenario: Parse on a pool worker

- **WHEN** a hostile document is parsed from a `ThreadPoolExecutor` worker thread
- **THEN** entities are not expanded and no external content appears, exactly as on the main thread

### Requirement: The xml_query template is parsed with the hardened parser explicitly

The system SHALL pass the hardened parser explicitly to the `lxml.etree.fromstring` call that parses the
operator-supplied `xml_query` in `_prepare_xml_paging`, rather than relying on the installed default.

#### Scenario: Malformed template still reports a clear error

- **WHEN** `xml_query` is not well-formed XML
- **THEN** a `ValueError` is raised describing the template as not well-formed, as before
