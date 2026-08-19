#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import re
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKS = ("planning-regulations", "planning-terminology", "design-concepts")
CALVER = re.compile(r"^\d{4}\.\d{2}\.\d+$")
FORBIDDEN_EXTENSIONS = {".exe", ".dll", ".ps1", ".bat", ".cmd", ".com", ".msi", ".msix", ".js", ".vbs", ".py"}
errors: list[str] = []


def error(message: str):
    errors.append(message)


def load_json(path: pathlib.Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        error(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return None


def check_url(value, label):
    if not value:
        return
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https"):
        error(f"{label}: URL must be http/https")


stable_global: set[str] = set()

for pack_id in PACKS:
    manifest_path = ROOT / "packs" / pack_id / "manifest.source.json"
    manifest = load_json(manifest_path)
    if not manifest:
        continue

    for key in ("formatVersion", "id", "version", "schemaVersion", "displayName", "minAppVersion", "dataPath", "publisher", "channel"):
        if key not in manifest:
            error(f"{pack_id}: manifest missing {key}")
    if manifest.get("formatVersion") != 1:
        error(f"{pack_id}: formatVersion must be 1")
    if manifest.get("id") != pack_id:
        error(f"{pack_id}: manifest id mismatch")
    if not CALVER.match(str(manifest.get("version", ""))):
        error(f"{pack_id}: invalid CalVer")
    for language in ("zh-CN", "ja-JP", "en-US"):
        if not manifest.get("displayName", {}).get(language):
            error(f"{pack_id}: missing displayName {language}")

    data_path = ROOT / "packs" / pack_id / manifest.get("dataPath", "")
    if data_path.suffix.lower() in FORBIDDEN_EXTENSIONS:
        error(f"{pack_id}: executable/script payload forbidden")
    data = load_json(data_path)
    if not data:
        continue
    if data.get("schemaVersion") != manifest.get("schemaVersion"):
        error(f"{pack_id}: schemaVersion mismatch")
    if data.get("dataVersion") != manifest.get("version"):
        error(f"{pack_id}: dataVersion != manifest version")

    collection = data.get("terms") if pack_id == "planning-terminology" else data.get("entries")
    if not isinstance(collection, list) or not collection:
        error(f"{pack_id}: missing/non-empty entry collection")
        continue

    numeric_ids: set[int] = set()
    stable_ids: set[str] = set()
    for index, item in enumerate(collection):
        numeric_id = item.get("id")
        stable_id = item.get("stableId")
        if not isinstance(numeric_id, int):
            error(f"{pack_id}[{index}]: integer id required")
        elif numeric_id in numeric_ids:
            error(f"{pack_id}: duplicate numeric id {numeric_id}")
        numeric_ids.add(numeric_id)

        if not isinstance(stable_id, str) or not stable_id:
            error(f"{pack_id}[{index}]: stableId required")
        elif stable_id in stable_ids:
            error(f"{pack_id}: duplicate stableId {stable_id}")
        elif stable_id in stable_global:
            error(f"global duplicate stableId {stable_id}")
        stable_ids.add(stable_id)
        stable_global.add(stable_id)

        if pack_id == "planning-regulations":
            for key in ("region", "jurisdictionLevel", "topic", "documentLevel", "originalTitle", "chineseTitle", "scopeAndPurpose", "effectOrAdoption", "officialUrl", "verifiedDate"):
                if item.get(key) in (None, ""):
                    error(f"{pack_id}:{stable_id}: missing {key}")
            check_url(item.get("officialUrl"), f"{pack_id}:{stable_id}:officialUrl")
            check_url(item.get("downloadUrl"), f"{pack_id}:{stable_id}:downloadUrl")
        elif pack_id == "planning-terminology":
            for key in ("category", "zhCN", "jaJP", "enUS", "jurisdiction", "equivalence", "definitionZh", "definitionJa", "definitionEn"):
                if item.get(key) in (None, ""):
                    error(f"{pack_id}:{stable_id}: missing {key}")
        else:
            title = item.get("title", {})
            definition = item.get("definition", {})
            for language in ("zh-CN", "ja-JP", "en-US"):
                if not title.get(language):
                    error(f"{pack_id}:{stable_id}: missing title {language}")
                if not definition.get(language):
                    error(f"{pack_id}:{stable_id}: missing definition {language}")
            if not item.get("sourceIds"):
                error(f"{pack_id}:{stable_id}: sourceIds required")

if errors:
    print("Data validation failed:")
    for item in errors:
        print(f"- {item}")
    sys.exit(1)

print(f"Data validation passed for {len(PACKS)} packs; stable IDs: {len(stable_global)}")
