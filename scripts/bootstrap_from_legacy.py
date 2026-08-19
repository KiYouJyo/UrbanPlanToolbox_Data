#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY_REPO = "KiYouJyo/UrbanPlanToolbox"
LEGACY_COMMIT = "dcad5b1923ba96bf825904d024a3b13af5e615da"
REG_PATH = "Assets/Data/RegulationsIndex/regulations-index.v1.json"
TERM_PATH = "Assets/Data/PlanningTerminology/PlanningTerminology.v1.0.json"
DATA_VERSION = "2026.08.1"


def fetch_json(path: str):
    url = f"https://raw.githubusercontent.com/{LEGACY_REPO}/{LEGACY_COMMIT}/{path}"
    request = urllib.request.Request(url, headers={"User-Agent": "UrbanPlanToolbox-Data-bootstrap/1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def write_json(path: pathlib.Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def migrate_regulations():
    legacy = fetch_json(REG_PATH)
    field_map = {
        "Id": "id",
        "Region": "region",
        "JurisdictionLevel": "jurisdictionLevel",
        "Topic": "topic",
        "DocumentLevel": "documentLevel",
        "OriginalTitle": "originalTitle",
        "ChineseTitle": "chineseTitle",
        "IdentifierOrYear": "identifierOrYear",
        "ScopeAndPurpose": "scopeAndPurpose",
        "EffectOrAdoption": "effectOrAdoption",
        "OfficialUrl": "officialUrl",
        "DownloadUrl": "downloadUrl",
        "DownloadAndCopyrightNote": "downloadAndCopyrightNote",
        "VerifiedDate": "verifiedDate",
        "SearchKeywords": "searchKeywords"
    }
    entries = []
    for source in legacy.get("Entries", []):
        item = {target: source.get(origin) for origin, target in field_map.items()}
        item["stableId"] = f"reg-{int(source['Id']):04d}"
        entries.append({"id": item.pop("id"), "stableId": item.pop("stableId"), **item})

    output = {
        "schemaVersion": 1,
        "dataVersion": DATA_VERSION,
        "source": {
            "legacyRepository": LEGACY_REPO,
            "legacyPath": REG_PATH,
            "legacyCommit": LEGACY_COMMIT,
            "sourceName": legacy.get("SourceName"),
            "sourceVerifiedDate": legacy.get("SourceVerifiedDate"),
            "legacyDataVersion": legacy.get("DataVersion"),
            "legacyGeneratedAt": legacy.get("GeneratedAt")
        },
        "entries": entries
    }
    write_json(ROOT / "packs/planning-regulations/data/regulations.json", output)
    print(f"migrated regulations: {len(entries)} entries")


def migrate_terminology():
    legacy = fetch_json(TERM_PATH)
    terms = []
    for source in legacy.get("terms", []):
        item = dict(source)
        item["stableId"] = f"term-{int(source['id']):04d}"
        terms.append({"id": item.pop("id"), "stableId": item.pop("stableId"), **item})

    output = dict(legacy)
    output["schemaVersion"] = 1
    output["dataVersion"] = DATA_VERSION
    output["languages"] = legacy.get("language", legacy.get("languages", ["zh-CN", "ja-JP", "en-US"]))
    output.pop("language", None)
    output["terms"] = terms
    output["migration"] = {
        "legacyRepository": LEGACY_REPO,
        "legacyPath": TERM_PATH,
        "legacyCommit": LEGACY_COMMIT,
        "legacyDataVersion": legacy.get("dataVersion")
    }
    write_json(ROOT / "packs/planning-terminology/data/terminology.json", output)
    print(f"migrated terminology: {len(terms)} terms")


if __name__ == "__main__":
    migrate_regulations()
    migrate_terminology()
