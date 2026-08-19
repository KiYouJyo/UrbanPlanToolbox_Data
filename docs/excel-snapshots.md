# Excel snapshots

The canonical database source is JSON under `packs/`. The `excel/` directory is a generated, human-readable mirror for quick review.

## Rules

- Never treat `.xlsx` files as canonical source data.
- Every published data version gets a versioned Excel snapshot and older snapshots are retained.
- `scripts/generate_excel.py` generates the snapshots and `excel/README.md` current-version links.
- `Sync Excel snapshots` runs after relevant changes reach `main` and commits generated spreadsheets back to `excel/`.
- `Data validation` also performs a dry-run Excel generation and validates the produced OOXML containers.
- `Publish data packs` includes the current Excel snapshots as release assets alongside `.uptdata` files.

This keeps application-facing machine data and reviewer-facing spreadsheets synchronized without requiring manual double-entry.
