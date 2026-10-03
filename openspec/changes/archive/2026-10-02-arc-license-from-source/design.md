## Decisions

1. **Licence path stays `LICENSE`; URL and text go into the content.** ARCtrl models `License.Path` as the licence file
   inside the ARC and reads it back from the RO-Crate licence `@id`. Setting `Path` to a URL gives a URL `@id`, and
   `ARC.from_rocrate_json_string(...).Write(...)` — what the API does when it writes ARCs — creates `https:/…`
   directories (same failure as the earlier `IOType.data` URL fix). The licence therefore always uses the default
   `LICENSE` path; the RO-Crate licence node is `{"@id": "LICENSE", "text": "<url or licence text>"}` and a written ARC
   has a `LICENSE` file with that text. A URL `@id` needs an ARCtrl change and is out of scope.

2. **No licence in the source keeps the ARCtrl default.** Absence of a licence grants no reuse rights, so "ALL RIGHTS
   RESERVED BY THE AUTHORS" is the correct statement; emitting "not specified" would suggest otherwise. This includes
   GeoNode's explicit `Not Specified: The original author did not specify a license.`.

3. **INSPIRE licence detection is conservative.** `otherConstraints` also holds access notes ("available on request from
   …", "keine"). Only these count as a licence, in order: a non-INSPIRE-registry `gmx:Anchor/@xlink:href`; a GeoNode
   licence text `Name (id): description` (BonaRes, Thünen Atlas); free text containing a URL on a known licence host
   (creativecommons.org, opendatacommons.org, govdata.de, spdx.org, rightsstatements.org).

4. **Unexpanded template placeholders are not licences.** e!DAL publishes `"license": "$licenseURL"` on some records;
   values matching `$name` / `${name}` are ignored.

5. **Schema.org CreativeWork licences use `url`.** A `license` node with `url` gives `name (url)` (or the URL); a plain
   URL or text is used as is.
