# UrbanPlanToolbox Data

Official structured data packs for [UrbanPlanToolbox](https://github.com/KiYouJyo/UrbanPlanToolbox).

This repository separates professional reference data from the application release cycle. UrbanPlanToolbox can ship a built-in offline baseline and optionally download newer validated `.uptdata` packs from this repository.

## Initial data packs

| Pack ID | Display name | Version | Schema |
| --- | --- | --- | --- |
| `planning-regulations` | 建筑与规划法规索引 | `2026.08.1` | `1` |
| `planning-terminology` | 中日英规划术语库 | `2026.08.1` | `1` |
| `design-concepts` | 设计理念词典 | `2026.08.1` | `1` |

## Repository layout

```text
catalog/                 Published catalog source
packs/                   Pack source manifests and structured data
schemas/                 JSON Schema contracts
scripts/                 Validation/build/catalog tooling
docs/                    Data authoring and release documentation
.github/workflows/        Validation and release automation
```

## Data-pack principles

- **Offline first:** the app keeps a built-in fallback and downloaded packs are local files.
- **Data only:** `.uptdata` must never contain executable code or scripts.
- **Stable IDs:** published entry IDs are immutable even when display names change.
- **Validated before activation:** package format, schema, path safety and SHA-256 are checked before the app switches the active version.
- **Versioned independently:** pack versions use `YYYY.MM.REVISION`; schema versions are independent integers.
- **Source-aware:** reference entries keep provenance metadata; summaries are authored for UrbanPlanToolbox rather than copying restricted full texts.

## Local validation and build

```bash
python scripts/validate.py
python scripts/build_packs.py
python scripts/generate_catalog.py --repository KiYouJyo/UrbanPlanToolbox_Data --tag data-2026.08.1
```

Build outputs are written to `dist/` and should be distributed as GitHub Release assets rather than committed to Git history.

## Contributions

Changes to published data should go through pull requests and pass `Data validation`. Corrections should preserve existing IDs and update source metadata where appropriate.

> This repository provides indexes, terminology mappings and original structured summaries. It is not a mirror of paid standards or copyrighted publications. Always use the linked authoritative source for legal or professional verification.
