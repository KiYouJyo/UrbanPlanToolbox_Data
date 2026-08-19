# UrbanPlanToolbox Data

Official structured data packs for [UrbanPlanToolbox](https://github.com/KiYouJyo/UrbanPlanToolbox).

This repository separates professional reference data from the application release cycle. UrbanPlanToolbox can ship a built-in offline baseline and optionally download newer validated `.uptdata` packs from this repository.

## Quick human-readable access

For fast manual review, use the generated Excel snapshots:

- **[Excel database index](excel/README.md)**
- [建筑与规划法规索引 Excel](excel/planning-regulations/)
- [中日英规划术语库 Excel](excel/planning-terminology/)
- [设计理念词典 Excel](excel/design-concepts/)

The `.xlsx` files are generated mirrors only. **JSON under `packs/` remains the canonical source.** Every data update generates a new versioned Excel snapshot automatically, while older snapshots are retained for review history.

## Initial data packs

| Pack ID | Display name | Version | Schema |
| --- | --- | --- | --- |
| `planning-regulations` | 建筑与规划法规索引 | `2026.08.1` | `1` |
| `planning-terminology` | 中日英规划术语库 | `2026.08.1` | `1` |
| `design-concepts` | 设计理念词典 | `2026.08.1` | `1` |

## Repository layout

```text
catalog/                 Published catalog source
packs/                   Canonical pack manifests and structured JSON data
excel/                   Generated human-readable versioned Excel snapshots
schemas/                 JSON Schema contracts
scripts/                 Validation/build/catalog/Excel tooling
docs/                    Data authoring and release documentation
.github/workflows/        Validation, Excel sync and release automation
```

## Data-pack principles

- **Offline first:** the app keeps a built-in fallback and downloaded packs are local files.
- **Data only:** `.uptdata` must never contain executable code or scripts.
- **Stable IDs:** published entry IDs are immutable even when display names change.
- **Validated before activation:** package format, schema, path safety and SHA-256 are checked before the app switches the active version.
- **Versioned independently:** pack versions use `YYYY.MM.REVISION`; schema versions are independent integers.
- **Source-aware:** reference entries keep provenance metadata; summaries are authored for UrbanPlanToolbox rather than copying restricted full texts.
- **Human-readable mirror:** Excel snapshots are generated automatically from canonical JSON and are never edited as source data.

## Local validation and build

```bash
python scripts/validate.py
python scripts/build_packs.py
python scripts/generate_excel.py --output-root excel
python scripts/generate_catalog.py --repository KiYouJyo/UrbanPlanToolbox_Data --tag data-2026.08.1
```

Build outputs are written to `dist/` and should be distributed as GitHub Release assets rather than committed to Git history. Excel snapshots are the exception: versioned `.xlsx` files under `excel/` are intentionally committed for direct human review.

## Contributions

Changes to published data should go through pull requests and pass `Data validation`. Corrections should preserve existing IDs and update source metadata where appropriate. Do not hand-edit generated `.xlsx` files; modify the canonical JSON and let `Sync Excel snapshots` regenerate them.

See [Excel snapshot policy](docs/excel-snapshots.md) for synchronization details.

> This repository provides indexes, terminology mappings and original structured summaries. It is not a mirror of paid standards or copyrighted publications. Always use the linked authoritative source for legal or professional verification.
