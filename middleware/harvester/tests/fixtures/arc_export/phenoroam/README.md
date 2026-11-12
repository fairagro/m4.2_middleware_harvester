# PhenoRoam (phenoroam) arc-export fixtures

No smoke crate at this folder root — real-data cases only (#615).

## Real-data cases

Generated via live OAI-PMH (`https://phenoroam.phenorob.de/geonetwork/srv/eng/oaipmh`, `metadataPrefix=phenoroam`)
through `PhenoroamXmlParser` + `PhenoroamMapper` (`phenoroam_general`), matching `dev_environment/config.all-rdis.yaml`.
Person `email` values redacted to `redacted@example.invalid` when present.

- `fc207e68-d7a9-484d-b2f7-e1ee40d5dd66/`: no bbox; single Person + affiliation + email; license; description; no
  keywords / datafile links / study-parent
- `9f1b0543-6377-47b0-8385-3406a0090869/`: no bbox; Person + affiliation; keywords; license; multiple datafile-link
  comments; study-parent titles; funded-by + core project
- `5c97b85f-69e3-481e-94d9-bb4e94d28bc8/`: **bbox**; Person + affiliation; keywords; license; datafile link;
  study-parent; funded-by + core project
- `aa1452d8-af03-4513-8cbe-38aca0a6081f/`: no bbox; Person + affiliation; keyword; license; multiple datafile links;
  study-parent + core project
