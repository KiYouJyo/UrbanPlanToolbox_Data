# UrbanPlanToolbox Data Pack Specification v1

## Container

`.uptdata` is a ZIP container that contains only data/content files. Version 1 requires:

```text
manifest.json
data/<one primary JSON file>
```

Executable or script payloads are forbidden.

## Manifest

The runtime manifest records the pack ID, independent data version, schema version, minimum compatible app version, localized display names and SHA-256 for every payload file.

## Versioning

- `version`: `YYYY.MM.REVISION` (content version).
- `schemaVersion`: integer contract version for the pack's business data.
- `formatVersion`: container contract version (`1` initially).

These versions are independent.

## Activation contract

UrbanPlanToolbox should:

1. download to staging;
2. verify catalog metadata and package SHA-256;
3. reject path traversal and forbidden extensions;
4. read and validate `manifest.json`;
5. verify every payload size and SHA-256;
6. check `minAppVersion` and supported `schemaVersion`;
7. install into a versioned local directory;
8. switch the active-version registry only after all checks pass;
9. fall back to another compatible local version or the built-in baseline on failure.

Official packs are cacheable public content and should not be copied into user `.uptbackup` archives.
