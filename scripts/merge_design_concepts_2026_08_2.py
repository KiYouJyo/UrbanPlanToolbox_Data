from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "packs" / "design-concepts" / "data" / "concepts.json"
MANIFEST_PATH = ROOT / "packs" / "design-concepts" / "manifest.source.json"
STAGING_DIR = ROOT / "packs" / "design-concepts" / "data" / "staging-2026.08.2"
VERSION = "2026.08.2"
REVIEW_DATE = "2026-08-21"

TAG_MAP = {
    1: ["存量更新", "渐进实施", "公共空间"],
    2: ["街道界面", "公共空间", "弹性与适应"],
    3: ["空间结构", "连通网络", "产业创新"],
    4: ["蓝绿水系", "自然生态", "连通网络"],
    5: ["空间结构", "社区生活", "产业创新"],
    6: ["空间结构", "连通网络", "低碳气候"],
    7: ["社区生活", "慢行交通", "连通网络"],
    8: ["蓝绿水系", "灾害韧性", "低碳气候"],
    9: ["渐进实施", "公共空间", "存量更新"],
    10: ["公共空间", "社区生活", "场所认知"],
    11: ["慢行交通", "公共空间", "街道界面"],
    12: ["存量更新", "弹性与适应", "场所认知"],
    13: ["存量更新", "渐进实施", "社区生活"],
    14: ["渐进实施", "公共空间", "存量更新"],
    15: ["慢行交通", "连通网络", "包容设计"],
    16: ["自然生态", "连通网络", "蓝绿水系"],
    17: ["慢行交通", "公共空间", "街道界面"],
    18: ["灾害韧性", "空间结构", "低碳气候"],
}

ALLOWED_TAGS = {
    "空间结构", "连通网络", "公共空间", "慢行交通", "街道界面", "社区生活",
    "弹性与适应", "低碳气候", "自然生态", "蓝绿水系", "灾害韧性", "循环资源",
    "存量更新", "渐进实施", "产业创新", "公众协作", "包容设计", "场所认知",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize", action="store_true", help="Remove one-time staging fragments after canonical merge")
    args = parser.parse_args()

    if not STAGING_DIR.exists():
        print("No 2026.08.2 staging directory; canonical data already merged.")
        return

    fragment_paths = sorted(STAGING_DIR.glob("fragment-*.json"))
    if len(fragment_paths) != 5:
        raise SystemExit(f"Expected 5 staging fragments, found {len(fragment_paths)}")

    current = load_json(DATA_PATH)
    base_entries = [entry for entry in current["entries"] if int(entry["id"]) <= 18]
    if [entry["id"] for entry in base_entries] != list(range(1, 19)):
        raise SystemExit("Base design-concept IDs 1-18 are missing or out of order")

    for entry in base_entries:
        entry["tags"] = TAG_MAP[entry["id"]]
        entry["reviewStatus"] = "reviewed"
        entry["lastReviewed"] = REVIEW_DATE

    staged_entries = []
    for path in fragment_paths:
        value = load_json(path)
        if not isinstance(value, list):
            raise SystemExit(f"{path} must contain a JSON array")
        staged_entries.extend(value)

    ids = [entry["id"] for entry in staged_entries]
    if ids != list(range(19, 69)):
        raise SystemExit(f"Staged IDs must be exactly 19-68; got {ids}")

    stable_ids = [entry["stableId"] for entry in base_entries + staged_entries]
    if len(stable_ids) != len(set(stable_ids)):
        raise SystemExit("Duplicate stableId detected")

    bad_tags = sorted({tag for entry in base_entries + staged_entries for tag in entry["tags"] if tag not in ALLOWED_TAGS})
    if bad_tags:
        raise SystemExit(f"Unknown tags: {bad_tags}")

    current["dataVersion"] = VERSION
    current["lastReviewed"] = REVIEW_DATE
    current["entries"] = base_entries + staged_entries
    write_json(DATA_PATH, current)

    manifest = load_json(MANIFEST_PATH)
    manifest["version"] = VERSION
    write_json(MANIFEST_PATH, manifest)

    if args.finalize:
        shutil.rmtree(STAGING_DIR)
        print("Merged 68 design concepts and removed one-time staging fragments.")
    else:
        print("Merged 68 design concepts for validation; staging fragments retained.")


if __name__ == "__main__":
    main()
