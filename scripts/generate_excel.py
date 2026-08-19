#!/usr/bin/env python3
"""Generate human-readable Excel snapshots from canonical JSON data.

Uses only the Python standard library so the repository has no spreadsheet runtime
dependency. The generated .xlsx files are review snapshots; JSON under packs/ is
always the canonical source.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import zipfile
from datetime import datetime, timezone
from html import escape

ROOT = pathlib.Path(__file__).resolve().parents[1]

PACKS = {
    "planning-regulations": ROOT / "packs/planning-regulations/data/regulations.json",
    "planning-terminology": ROOT / "packs/planning-terminology/data/terminology.json",
    "design-concepts": ROOT / "packs/design-concepts/data/concepts.json",
}


def col_letter(index: int) -> str:
    result = ""
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return "；".join(str(v) for v in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def cell_xml(ref: str, value, style: int = 2) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'
    escaped = escape(text(value))
    return f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{escaped}</t></is></c>'


def sheet_xml(headers: list[str], rows: list[list], widths: list[float]) -> str:
    max_col = col_letter(len(headers))
    max_row = len(rows) + 1
    cols = "".join(
        f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>'
        for i, width in enumerate(widths, 1)
    )
    header_cells = "".join(cell_xml(f"{col_letter(i)}1", h, 1) for i, h in enumerate(headers, 1))
    row_xml = [f'<row r="1" ht="26" customHeight="1">{header_cells}</row>']
    for r_idx, row in enumerate(rows, 2):
        cells = "".join(cell_xml(f"{col_letter(c_idx)}{r_idx}", value, 2) for c_idx, value in enumerate(row, 1))
        row_xml.append(f'<row r="{r_idx}">{cells}</row>')
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>
  <sheetFormatPr defaultRowHeight="18"/>
  <cols>{cols}</cols>
  <sheetData>{''.join(row_xml)}</sheetData>
  <autoFilter ref="A1:{max_col}{max_row}"/>
</worksheet>'''


def write_xlsx(path: pathlib.Path, sheets: list[tuple[str, list[str], list[list], list[float]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(1, len(sheets) + 1):
        content_types.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')

    sheet_nodes = "".join(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i, (name, *_rest) in enumerate(sheets, 1))
    workbook_rels = "".join(
        f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, len(sheets) + 1)
    ) + f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2"><font><sz val="10"/><name val="Aptos"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="10"/><name val="Aptos"/></font></fonts>
  <fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF33424A"/><bgColor indexed="64"/></patternFill></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>'''

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">' + "".join(content_types) + "</Types>")
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>{sheet_nodes}</sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">' + workbook_rels + "</Relationships>")
        z.writestr("xl/styles.xml", styles)
        z.writestr("docProps/core.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>UrbanPlanToolbox Data Excel Snapshot</dc:title><dc:creator>UrbanPlanToolbox_Data</dc:creator><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created></cp:coreProperties>')
        z.writestr("docProps/app.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>UrbanPlanToolbox_Data</Application></Properties>')
        for i, (_name, headers, rows, widths) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(headers, rows, widths))


def meta_sheet(pack_id: str, data: dict, source_path: pathlib.Path) -> tuple[str, list[str], list[list], list[float]]:
    rows = [
        ["Pack ID", pack_id],
        ["Data Version", data.get("dataVersion", "")],
        ["Schema Version", data.get("schemaVersion", "")],
        ["Last Reviewed", data.get("lastReviewed", data.get("source", {}).get("sourceVerifiedDate", ""))],
        ["Canonical JSON", str(source_path.relative_to(ROOT)).replace("\\", "/")],
        ["Generated Snapshot", "This workbook is generated; edit JSON under packs/ instead."],
    ]
    return ("元数据", ["字段", "值"], rows, [24, 72])


def normalized_source_rows(value) -> list[list]:
    """Normalize source containers that may be lists or ID-keyed dictionaries."""
    rows = []
    if isinstance(value, dict):
        iterable = value.items()
    elif isinstance(value, list):
        iterable = [(None, item) for item in value]
    else:
        return rows

    for source_id, payload in iterable:
        if isinstance(payload, dict):
            sid = payload.get("id") or source_id or ""
            name = payload.get("name") or payload.get("title") or payload.get("label") or ""
            url = payload.get("url") or payload.get("officialUrl") or payload.get("sourceUrl") or ""
            note = payload.get("note") or payload.get("description") or payload.get("status") or ""
            jurisdiction = payload.get("jurisdiction") or payload.get("region") or ""
        else:
            sid = source_id or ""
            name = payload
            url = ""
            note = ""
            jurisdiction = ""
        rows.append([sid, name, url, note, jurisdiction])
    return rows


def regulations_sheets(data: dict, source_path: pathlib.Path):
    headers = ["ID", "Stable ID", "地区", "法域层级", "主题", "文档级别", "原文名称", "中文名称", "编号/年份", "适用范围与目的", "效力/采用情况", "官方 URL", "下载 URL", "下载与版权说明", "核验日期", "搜索关键词"]
    rows = []
    for e in data.get("entries", []):
        rows.append([e.get("id"), e.get("stableId"), e.get("region"), e.get("jurisdictionLevel"), e.get("topic"), e.get("documentLevel"), e.get("originalTitle"), e.get("chineseTitle"), e.get("identifierOrYear"), e.get("scopeAndPurpose"), e.get("effectOrAdoption"), e.get("officialUrl"), e.get("downloadUrl"), e.get("downloadAndCopyrightNote"), e.get("verifiedDate"), e.get("searchKeywords")])
    return [("法规条目", headers, rows, [7, 18, 12, 14, 18, 14, 32, 32, 16, 42, 36, 36, 36, 42, 14, 30]), meta_sheet("planning-regulations", data, source_path)]


def terminology_sheets(data: dict, source_path: pathlib.Path):
    headers = ["ID", "Stable ID", "分类", "中文", "日本語", "日语读音", "English", "法域", "概念类型", "对应关系", "中文定义", "日文定义", "英文定义", "别名", "易混/相关", "来源 ID", "来源状态", "审校备注", "翻译状态", "最近审校", "关联术语 ID", "发布状态"]
    rows = []
    for e in data.get("terms", []):
        rows.append([e.get("id"), e.get("stableId"), e.get("category"), e.get("zhCN"), e.get("jaJP"), e.get("jaReading"), e.get("enUS"), e.get("jurisdiction"), e.get("conceptType"), e.get("equivalence"), e.get("definitionZh"), e.get("definitionJa"), e.get("definitionEn"), e.get("aliases", []), e.get("confusableOrRelated"), e.get("sourceIds", []), e.get("sourceStatus"), e.get("reviewNote"), e.get("translationStatus"), e.get("lastReviewed"), e.get("relatedTermIds", []), e.get("releaseStatus")])
    source_rows = normalized_source_rows(data.get("sources", []))
    return [("术语", headers, rows, [7, 18, 16, 18, 22, 18, 26, 16, 18, 18, 42, 42, 42, 28, 34, 24, 22, 34, 18, 14, 24, 28]), ("来源", ["Source ID", "名称", "URL", "说明", "法域"], source_rows, [18, 32, 42, 52, 18]), meta_sheet("planning-terminology", data, source_path)]


def concept_sheets(data: dict, source_path: pathlib.Path):
    headers = ["ID", "Stable ID", "中文名称", "日文名称", "英文名称", "分类", "适用项目", "标签", "中文定义", "日文定义", "英文定义", "案例说明", "别名", "来源 ID", "审核状态", "最近审核"]
    rows = []
    for e in data.get("entries", []):
        title = e.get("title", {})
        definition = e.get("definition", {})
        case = e.get("caseNote", {})
        rows.append([e.get("id"), e.get("stableId"), title.get("zh-CN"), title.get("ja-JP"), title.get("en-US"), e.get("category"), e.get("projectTypes", []), e.get("tags", []), definition.get("zh-CN"), definition.get("ja-JP"), definition.get("en-US"), case.get("zh-CN"), e.get("aliases", []), e.get("sourceIds", []), e.get("reviewStatus"), e.get("lastReviewed")])
    source_rows = []
    for s in data.get("sources", []):
        names = s.get("name", {})
        notes = s.get("note", {})
        source_rows.append([s.get("id"), names.get("zh-CN"), names.get("ja-JP"), names.get("en-US"), s.get("type"), notes.get("zh-CN"), notes.get("ja-JP"), notes.get("en-US")])
    return [("设计理念", headers, rows, [7, 26, 18, 24, 28, 18, 28, 26, 44, 44, 44, 42, 20, 22, 14, 14]), ("来源", ["Source ID", "中文名称", "日文名称", "英文名称", "类型", "中文说明", "日文说明", "英文说明"], source_rows, [18, 28, 30, 34, 22, 52, 52, 52]), meta_sheet("design-concepts", data, source_path)]


def generate(output_root: pathlib.Path) -> list[pathlib.Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    generated = []
    links = []
    builders = {
        "planning-regulations": regulations_sheets,
        "planning-terminology": terminology_sheets,
        "design-concepts": concept_sheets,
    }
    display = {
        "planning-regulations": "建筑与规划法规索引",
        "planning-terminology": "中日英规划术语库",
        "design-concepts": "设计理念词典",
    }
    for pack_id, source_path in PACKS.items():
        data = json.loads(source_path.read_text(encoding="utf-8"))
        version = data["dataVersion"]
        out = output_root / pack_id / f"{pack_id}-{version}.xlsx"
        write_xlsx(out, builders[pack_id](data, source_path))
        generated.append(out)
        rel = out.relative_to(output_root).as_posix()
        links.append((display[pack_id], version, rel))

    index_lines = [
        "# Excel database snapshots",
        "",
        "Human-readable, versioned Excel snapshots generated from the canonical JSON databases under `packs/`.",
        "",
        "> Do not edit these spreadsheets as source data. Update JSON under `packs/`; the snapshots are regenerated automatically.",
        "",
        "## Current versions",
        "",
        "| Database | Version | Excel |",
        "| --- | --- | --- |",
    ]
    for name, version, rel in links:
        index_lines.append(f"| {name} | `{version}` | [{pathlib.PurePosixPath(rel).name}]({rel}) |")
    index_lines += ["", "Older versioned `.xlsx` files are retained in each database subdirectory for human review and audit history.", ""]
    (output_root / "README.md").write_text("\n".join(index_lines), encoding="utf-8")
    return generated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default=str(ROOT / "excel"))
    args = parser.parse_args()
    output_root = pathlib.Path(args.output_root)
    generated = generate(output_root)
    for path in generated:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
