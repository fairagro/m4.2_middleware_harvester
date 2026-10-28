# Tasks

## 1. Tests and fix

- [x] 1.1 T1: a SRADI-style dataset (http(s) IRI, no `dcat:landingPage`) maps without a `Landing Page` comment (repro;
      fails on `main` once asserting the comment)
- [x] 1.2 T2: the same dataset gets `Landing Page` = the dataset IRI
- [x] 1.3 T3: an explicit `dcat:landingPage` wins over the IRI
- [x] 1.4 T4: two `dcat:landingPage` values give one comment, the same value on repeated mapping
- [x] 1.5 T5: a blank-node dataset with no `dcat:landingPage` gets no comment and still maps
- [x] 1.6 T6: no `URL` comment in any of the above
- [ ] 1.7 Add the `dcat:landingPage` / dataset IRI → `Investigation.Comment("Landing Page")` row to
      `docs/mappers/ckanext-dcat.md`; markdown hooks pass

## 2. Verify and close

- [ ] 2.1 T7: dev stack (dmz-web-140): SRADI harvest from source and container, 57/57 ARCs with a `Landing Page` that
      opens the Agrihub page, payloads identical apart from timestamps
- [ ] 2.2 Comment on #531 with the PR and the dev-stack result
- [ ] 2.3 Archive after merge
