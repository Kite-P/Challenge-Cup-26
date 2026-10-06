"""将平台中立的虚构问卷导出转换为最小 canonical 结构。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


SYNTHETIC_VERSION = "phase1g_import_mock_v1"
REQUIRED_COLUMNS = {
    "平台响应ID",
    "最近是否完成研究任务",
    "最近任务中是否使用生成式AI",
    "科研经历类型",
}
OPTIONAL_METADATA_COLUMNS = {"平台提交时间"}
YES_NO = {"是": "YES", "否": "NO", "YES": "YES", "NO": "NO", "TRUE": "YES", "FALSE": "NO"}
EXPERIENCE = {
    "无": "NONE",
    "无正式科研经历": "LOW_RESEARCH_EXPOSURE",
    "课程项目": "COURSE_BASED",
    "正式项目": "FORMAL_PROJECT",
}


def transform_survey_export(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """校验虚构导出列和值，返回最小、明确标记为合成的数据。"""
    records = list(rows)
    if not records:
        return []
    columns = set(records[0])
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"缺少必需列：{', '.join(sorted(missing))}")
    unknown_columns = columns - REQUIRED_COLUMNS - OPTIONAL_METADATA_COLUMNS
    if unknown_columns:
        raise ValueError(f"存在未登记列：{', '.join(sorted(unknown_columns))}")

    seen: set[str] = set()
    output: list[dict[str, str]] = []
    for index, row in enumerate(records, start=1):
        if set(row) != columns:
            raise ValueError(f"第 {index} 行字段结构不一致")
        response_id = (row.get("平台响应ID") or "").strip()
        if not response_id:
            raise ValueError(f"第 {index} 行平台响应ID为空")
        if response_id in seen:
            raise ValueError(f"重复响应ID：{response_id}")
        seen.add(response_id)
        recent = _normalize_choice(row.get("最近是否完成研究任务"), YES_NO, "最近是否完成研究任务")
        ai_used = "NA_SKIP" if recent == "NO" else _normalize_choice(
            row.get("最近任务中是否使用生成式AI"), {**YES_NO, "不确定": "UNSURE"}, "AI使用"
        )
        experience = _normalize_choice(row.get("科研经历类型"), EXPERIENCE, "科研经历类型")
        output.append(
            {
                "research_id": f"SYN-{response_id}",
                "synthetic_flag": "TRUE",
                "synthetic_version": SYNTHETIC_VERSION,
                "recent_research_task": recent,
                "ai_used": ai_used,
                "research_experience_type": experience,
            }
        )
    return output


def transform_csv(input_path: str | Path, output_path: str | Path) -> int:
    """读取 UTF-8/带 BOM CSV 并写出 UTF-8 canonical CSV。"""
    with Path(input_path).open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    transformed = transform_survey_export(rows)
    if not transformed:
        raise ValueError("导出文件没有数据行")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(transformed[0]))
        writer.writeheader()
        writer.writerows(transformed)
    return len(transformed)


def _normalize_choice(value: str | None, mapping: dict[str, str], label: str) -> str:
    normalized = (value or "").strip()
    if normalized in mapping:
        return mapping[normalized]
    if normalized.upper() in mapping:
        return mapping[normalized.upper()]
    raise ValueError(f"{label}存在未知选项：{normalized!r}")
