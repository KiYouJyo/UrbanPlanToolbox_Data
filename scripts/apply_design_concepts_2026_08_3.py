from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "packs" / "design-concepts" / "data" / "concepts.json"
MANIFEST_PATH = ROOT / "packs" / "design-concepts" / "manifest.source.json"
LABELS_PATH = ROOT / "scripts" / "design_concepts_2026_08_3_labels.json"
CASE_NOTES_PATH = ROOT / "scripts" / "design_concepts_2026_08_3_existing_case_notes.json"
ADDITIONS_PATH = ROOT / "scripts" / "design_concepts_2026_08_3_additions.json"

VERSION = "2026.08.3"
REVIEW_DATE = "2026-08-21"
MIN_APP_VERSION = "1.9.3"
LANGUAGES = ("zh-CN", "ja-JP", "en-US")

WUPEN_SOURCE = {
    "id": "UPT-WUPEN-2026-08",
    "name": {
        "zh-CN": "WUPEN City 获奖作品理念审核（2026-08）",
        "ja-JP": "WUPEN City 受賞作品コンセプトレビュー（2026-08）",
        "en-US": "WUPEN City Awarded-Project Concept Review (2026-08)"
    },
    "type": "curated-project-review",
    "note": {
        "zh-CN": "从 WUPEN City 获奖作品标题中的显式理论、理念、视角与模式表述出发，经专业相关性、概念可定义性、案例可核验性和去重审核后形成候选；正式条目的定义与案例由 UrbanPlanToolbox 编辑复核。",
        "ja-JP": "WUPEN City 受賞作品タイトルに明示された理論・理念・視点・モデルを出発点とし、専門分野との関連性、定義可能性、事例検証、重複排除を経て候補化した。最終的な定義と事例は UrbanPlanToolbox が編集・確認している。",
        "en-US": "Candidates were derived from explicit theory, concept, perspective and model statements in WUPEN City awarded-project titles, then screened for disciplinary relevance, definability, verifiable cases and duplication. Final definitions and cases are editorially reviewed by UrbanPlanToolbox."
    }
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def require_localized(value: dict, label: str) -> None:
    for language in LANGUAGES:
        if not isinstance(value.get(language), str) or not value[language].strip():
            raise SystemExit(f"{label}: missing {language}")


def main() -> None:
    data = load_json(DATA_PATH)
    labels = load_json(LABELS_PATH)
    existing_case_notes = load_json(CASE_NOTES_PATH)
    additions = load_json(ADDITIONS_PATH)

    base_entries = sorted((entry for entry in data.get("entries", []) if int(entry.get("id", 0)) <= 68), key=lambda entry: entry["id"])
    if [entry["id"] for entry in base_entries] != list(range(1, 69)):
        raise SystemExit("Existing design-concept IDs 1-68 are missing or out of order")
    if len(existing_case_notes) != 68:
        raise SystemExit(f"Expected 68 existing case-note translations, found {len(existing_case_notes)}")

    base_stable_ids = {entry["stableId"] for entry in base_entries}
    if base_stable_ids != set(existing_case_notes):
        missing = sorted(base_stable_ids - set(existing_case_notes))
        extra = sorted(set(existing_case_notes) - base_stable_ids)
        raise SystemExit(f"Existing case-note translation mismatch; missing={missing}, extra={extra}")

    for entry in base_entries:
        note = entry.setdefault("caseNote", {})
        if not isinstance(note.get("zh-CN"), str) or not note["zh-CN"].strip():
            raise SystemExit(f"{entry['stableId']}: existing zh-CN caseNote missing")
        translations = existing_case_notes[entry["stableId"]]
        note["ja-JP"] = translations["ja-JP"].strip()
        note["en-US"] = translations["en-US"].strip()
        require_localized(entry["title"], f"{entry['stableId']}.title")
        require_localized(entry["definition"], f"{entry['stableId']}.definition")
        require_localized(note, f"{entry['stableId']}.caseNote")
        entry["lastReviewed"] = REVIEW_DATE

    if [entry.get("id") for entry in additions] != list(range(69, 110)):
        raise SystemExit("2026.08.3 additions must contain exactly IDs 69-109")
    for entry in additions:
        require_localized(entry["title"], f"{entry['stableId']}.title")
        require_localized(entry["definition"], f"{entry['stableId']}.definition")
        require_localized(entry["caseNote"], f"{entry['stableId']}.caseNote")
        entry["lastReviewed"] = REVIEW_DATE

    all_entries = base_entries + additions
    stable_ids = [entry["stableId"] for entry in all_entries]
    if len(stable_ids) != len(set(stable_ids)):
        raise SystemExit("Duplicate design-concept stableId in 2026.08.3 data")

    for group_name in ("categories", "projectTypes", "tags"):
        group = labels.get(group_name)
        if not isinstance(group, dict) or not group:
            raise SystemExit(f"labels.{group_name} missing")
        for key, localized in group.items():
            require_localized(localized, f"labels.{group_name}.{key}")

    used_categories = {entry["category"] for entry in all_entries}
    used_project_types = {value for entry in all_entries for value in entry.get("projectTypes", [])}
    used_tags = {value for entry in all_entries for value in entry.get("tags", [])}
    coverage = {
        "categories": used_categories,
        "projectTypes": used_project_types,
        "tags": used_tags,
    }
    for group_name, used_values in coverage.items():
        missing = sorted(used_values - set(labels[group_name]))
        if missing:
            raise SystemExit(f"labels.{group_name} missing used keys: {missing}")

    sources = [source for source in data.get("sources", []) if source.get("id") != WUPEN_SOURCE["id"]]
    sources.append(WUPEN_SOURCE)

    data["schemaVersion"] = 1
    data["dataVersion"] = VERSION
    data["lastReviewed"] = REVIEW_DATE
    data["labels"] = labels
    data["sources"] = sources
    data["entries"] = all_entries
    write_json(DATA_PATH, data)

    manifest = load_json(MANIFEST_PATH)
    manifest["version"] = VERSION
    manifest["schemaVersion"] = 1
    manifest["minAppVersion"] = MIN_APP_VERSION
    write_json(MANIFEST_PATH, manifest)

    print(f"Prepared design-concepts {VERSION}: {len(all_entries)} entries, {len(used_project_types)} project types, {len(used_tags)} tags")


if __name__ == "__main__":
    main()
