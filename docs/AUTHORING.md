# Data authoring

## Regulations

The initial regulations dataset is migrated from `UrbanPlanToolbox/Assets/Data/RegulationsIndex/regulations-index.v1.json`. The migration preserves the existing source content while normalizing field names and adding immutable `stableId` values such as `reg-0001`.

Do not copy paid standards or copyrighted full texts into this repository. Keep index metadata, original UrbanPlanToolbox summaries and authoritative source links.

## Terminology

The initial terminology dataset is migrated from `PlanningTerminology.v1.0.json`. Existing numeric IDs and relationship fields are preserved for compatibility; every term additionally receives an immutable `stableId` such as `term-0001`.

When correcting a translation, keep both `id` and `stableId` unchanged.

## Design concepts

`design-concepts` is an UrbanPlanToolbox-curated explanatory dataset. It is not presented as a legal or academic authority. New entries require three-language titles and definitions, project-type tags, a case note and provenance.

## Review checklist

- Stable ID unchanged for existing entries.
- No duplicate IDs.
- Required three-language fields complete where the schema requires them.
- Source URLs use HTTP/HTTPS.
- `lastReviewed` / `verifiedDate` updated only when a source is actually checked.
- No executable files, scripts, credentials, paid PDFs or copied restricted texts.
