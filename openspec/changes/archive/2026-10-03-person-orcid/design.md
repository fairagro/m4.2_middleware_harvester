## Decisions

1. **`Person.ORCID`, not a Comment.** ARCtrl's native field becomes the RO-Crate Person `@id`, the standard RO-Crate way
   to identify a person, and survives `ARC.from_rocrate_json_string`. A Comment ends up as free text in
   `disambiguatingDescription`.
2. **Bare iD, strict pattern.** `orcid_id` accepts `dddd-dddd-dddd-dddX` alone or behind `http(s)://(www.)orcid.org/`.
   Look-alike hosts and sandbox.orcid.org are rejected. A bare iD inside a Schema.org PropertyValue counts only when its
   `propertyID` names ORCID (so other identifier schemes with the same shape are not misread).
3. **One contact per ORCID.** ARCtrl writes one node per `@id`; two contacts with the same ORCID would read back as two
   contacts each carrying both roles. `add_contact` merges roles instead.
