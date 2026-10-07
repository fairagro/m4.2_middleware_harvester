## 1. Mappers

- [x] 1.1 Schema.org: `PublicReleaseDate` from `datePublished` → `dateModified` → `dateCreated`; `SubmissionDate` from
      `dateCreated`
- [x] 1.2 INSPIRE: `PublicReleaseDate` from the citation dates; `SubmissionDate` from the earliest creation date
- [x] 1.3 Regal and ckanext-dcat: `dcterms:issued` → `PublicReleaseDate`

## 2. Verification

- [x] 2.1 Unit tests, including the API read/write round trip
- [x] 2.2 Mapping docs
- [x] 2.3 Live Publisso, BonaRes/Thünen and e!DAL runs
