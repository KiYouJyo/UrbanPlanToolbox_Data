#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--repository", default="KiYouJyo/UrbanPlanToolbox_Data")
parser.add_argument("--tag", required=True)
parser.add_argument("--write-source", action="store_true")
args = parser.parse_args()

packs = []
for manifest_path in sorted(DIST.glob("*.manifest.json")):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    asset = DIST / f"{manifest['id']}-{manifest['version']}.uptdata"
    packs.append(
        {
            "id": manifest["id"],
            "version": manifest["version"],
            "schemaVersion": manifest["schemaVersion"],
            "minAppVersion": manifest["minAppVersion"],
            "displayName": manifest["displayName"],
            "size": asset.stat().st_size,
            "sha256": sha256(asset),
            "downloadUrl": f"https://github.com/{args.repository}/releases/download/{args.tag}/{asset.name}"
        }
    )

catalog = {
    "catalogVersion": 1,
    "releaseTag": args.tag,
    "packs": packs
}
text = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
(DIST / "catalog-v1.json").write_text(text, encoding="utf-8")

if args.write_source:
    output = ROOT / "catalog" / "catalog-v1.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")

print(f"catalog contains {len(packs)} packs")
