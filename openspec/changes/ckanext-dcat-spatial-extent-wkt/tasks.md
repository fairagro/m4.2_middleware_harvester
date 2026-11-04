# Tasks

## 1. Tests and change

- [x] 1.1 T1: a POINT WKT literal becomes the `Spatial Extent` text (fails on `main`)
- [x] 1.2 T2: a MULTIPOLYGON WKT literal is copied verbatim
- [x] 1.3 T3: a WKT literal over the cap keeps the placeholder, is absent from the ARC, and logs a WARNING (rewrites
      `test_ckanext_dcat_mapper_flags_spatial_extent_without_embedding_raw_geometry`)
- [x] 1.4 T4: a GeoJSON-only location keeps the placeholder
- [x] 1.5 T5: two WKT literals are sorted and joined with `"; "`
- [x] 1.6 T6: a dataset without `dct:spatial` has no `Spatial Extent` comment
- [x] 1.7 T7: `mapper.ckanext_dcat.spatial_extent_max_chars: 50` turns a 100-character WKT into the placeholder
- [x] 1.8 Update `docs/mappers/ckanext-dcat.md` (Spatial Extent row and the config setting)

## 2. Verify and close

- [x] 2.1 Manual: SRADI harvest from the branch vs `main`; only `Spatial Extent` changes; source vs container identical
      for one ARC
- [ ] 2.2 Archive after merge
