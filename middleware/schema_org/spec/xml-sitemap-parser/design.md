# XML Sitemap Parser — Design

## Architecture overview

The XML sitemap parser is responsible for a single concern: translating sitemap documents into dataset URLs. It does not parse dataset payloads or map graphs to ARC.

The parser consumes a single configured sitemap URL as its entry point and preserves a stable, deduplicated set of dataset URLs across discovery.

The public contract is dataset-level deduplication: output must suppress duplicate dataset URLs, while sitemap-level fetch repetition is an implementation detail used only to safely support nested sitemap indexes. The implementation must also prevent cycles in nested sitemap indexes by tracking already visited sitemap URLs.

## Key Decisions

1. **Implement sitemap parsing in a dedicated `XmlSitemap` module**
   — This isolates protocol-specific XML handling from the rest of the plugin and makes it easier to add additional sitemap sources later.

2. **Keep dataset construction injectable via a dataset factory**
   — `XmlSitemap` accepts a `dataset_factory` so it can produce provider-specific dataset wrappers without depending on the dataset abstraction implementation.

3. **Use safe XML parsing for untrusted sitemap content**
   — The parser uses `defusedxml` to mitigate XML entity attacks and fulfill security requirements.
