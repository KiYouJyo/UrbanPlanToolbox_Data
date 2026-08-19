#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PACKS = ("planning-regulations", "planning-terminology", "design-concepts")
ALLOWED_EXTENSIONS = {".json", ".csv", ".xml", ".txt", ".md", ".png", ".jpg", ".jpeg", ".webp", ".geojson", ".db"}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    sums: list[tuple[str, str]] = []

    for pack_id in PACKS:
        pack_root = ROOT / "packs" / pack_id
        source = json.loads((pack_root / "manifest.source.json").read_text(encoding="utf-8"))
        data_rel = pathlib.PurePosixPath(source["dataPath"])
        data_path = pack_root / pathlib.Path(*data_rel.parts)
        if data_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            raise SystemExit(f"forbidden payload extension: {data_path}")

        payload = data_path.read_bytes()
        runtime_manifest = {
            "formatVersion": source["formatVersion"],
            "id": source["id"],
            "version": source["version"],
            "schemaVersion": source["schemaVersion"],
            "displayName": source["displayName"],
            "description": source.get("description", {}),
            "minAppVersion": source["minAppVersion"],
            "publisher": source["publisher"],
            "channel": source["channel"],
            "files": [
                {
                    "path": str(data_rel),
                    "size": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest()
                }
            ]
        }
        manifest_bytes = (json.dumps(runtime_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        filename = f"{pack_id}-{source['version']}.uptdata"
        target = DIST / filename
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.writestr("manifest.json", manifest_bytes)
            archive.writestr(str(data_rel), payload)

        sidecar = DIST / f"{pack_id}-{source['version']}.manifest.json"
        sidecar.write_bytes(manifest_bytes)
        sums.append((sha256(target), filename))

    (DIST / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for digest, name in sums),
        encoding="utf-8"
    )
    print(f"built {len(PACKS)} .uptdata packages in {DIST}")


if __name__ == "__main__":
    main()
