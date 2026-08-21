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
LANGUAGES = ("zh-CN", "ja-JP", "en-US")
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


def require_localized(value, label: str):
    if not isinstance(value, dict):
        error(f"{label}: localized object required")
        return
    for language in LANGUAGES:
        text = value.get(language)
        if not isinstance(text, str) or not text.strip():
            error(f"{label}: missing {language}")


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
    require_localized(manifest.get("displayName", {}), f"{pack_id}:displayName")

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
            require_localized(item.get("title", {}), f"{pack_id}:{stable_id}:title")
            require_localized(item.get("definition", {}), f"{pack_id}:{stable_id}:definition")
            require_localized(item.get("caseNote", {}), f"{pack_id}:{stable_id}:caseNote")
            if not item.get("sourceIds"):
                error(f"{pack_id}:{stable_id}: sourceIds required")
            if not isinstance(item.get("category"), str) or not item.get("category", "").strip():
                error(f"{pack_id}:{stable_id}: category required")
            for field in ("projectTypes", "tags"):
                values = item.get(field)
                if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
                    error(f"{pack_id}:{stable_id}: {field} must be a string array without blanks")

    if pack_id == "design-concepts":
        expected_ids = set(range(1, len(collection) + 1))
        if numeric_ids != expected_ids:
            error(f"design-concepts: numeric IDs must be contiguous 1-{len(collection)}")

        labels = data.get("labels")
        if not isinstance(labels, dict):
            error("design-concepts: labels object required")
            labels = {}
        label_groups = {
            "categories": {item.get("category") for item in collection if item.get("category")},
            "projectTypes": {value for item in collection for value in item.get("projectTypes", [])},
            "tags": {value for item in collection for value in item.get("tags", [])},
        }
        for group_name, used_values in label_groups.items():
            group = labels.get(group_name)
            if not isinstance(group, dict):
                error(f"design-concepts: labels.{group_name} object required")
                continue
            for key, localized in group.items():
                require_localized(localized, f"design-concepts:labels.{group_name}.{key}")
            for value in sorted(used_values):
                if value not in group:
                    error(f"design-concepts: labels.{group_name} missing used key {value}")

        source_ids = {source.get("id") for source in data.get("sources", []) if isinstance(source, dict)}
        for source in data.get("sources", []):
            if not isinstance(source, dict):
                error("design-concepts: source must be an object")
                continue
            source_id = source.get("id", "<missing>")
            require_localized(source.get("name", {}), f"design-concepts:source:{source_id}:name")
            require_localized(source.get("note", {}), f"design-concepts:source:{source_id}:note")
        for item in collection:
            for source_id in item.get("sourceIds", []):
                if source_id not in source_ids:
                    error(f"design-concepts:{item.get('stableId')}: unknown sourceId {source_id}")

if errors:
    print("Data validation failed:")
    for item in errors:
        print(f"- {item}")
    sys.exit(1)

print(f"Data validation passed for {len(PACKS)} packs; stable IDs: {len(stable_global)}")
