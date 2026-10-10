"""按问卷v0.6部分候选字段转换平台中立的虚构导出。"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


SYNTHETIC_VERSION = "phase2b_v06_contract_v2"
REQUIRED_COLUMNS = {
    "平台响应ID",
    "Q1_最近是否参与研究型学习任务",
    "Q2_最近任务类型",
    "Q3_实际参与环节",
    "Q7_最近任务AI使用",
}
OPTIONAL_METADATA_COLUMNS = {"平台提交时间"}
Q1_STATES = {
    "是": "YES", "YES": "YES",
    "否": "NO", "NO": "NO",
    "不确定是否符合上面的任务范围": "UNSURE", "不确定": "UNSURE", "UNSURE": "UNSURE",
    "不愿回答": "NA_REFUSE", "NA_REFUSE": "NA_REFUSE",
}
Q7_STATES = {
    "使用过": "YES", "YES": "YES",
    "没有使用": "NO", "NO": "NO",
    "不确定/记不清": "UNSURE", "不确定": "UNSURE", "UNSURE": "UNSURE",
    "最近任务没有可用的生成式 AI 工具": "NO_TOOL", "没有可用工具": "NO_TOOL", "NO_TOOL": "NO_TOOL",
    "不适用（该任务没有涉及生成式 AI 可参与的环节）": "NA_APPL", "不适用": "NA_APPL", "NA_APPL": "NA_APPL",
    "不愿回答": "NA_REFUSE", "NA_REFUSE": "NA_REFUSE",
}
TASK_TYPES = {
    "课程研究作业/课程论文": "COURSE_RESEARCH",
    "课程调查或研究报告": "COURSE_SURVEY_REPORT",
    "大学生创新训练项目": "INNOVATION_PROJECT",
    "学术科技竞赛中的研究任务（不指定具体赛事）": "COMPETITION_RESEARCH",
    "导师课题/科研助理任务": "MENTOR_PROJECT",
    "其他研究型学习任务": "OTHER_RESEARCH_TASK",
}
PARTICIPATION_STAGES = {
    "确定或缩小研究问题": "DEFINE_QUESTION",
    "查找、筛选或整理资料": "FIND_OR_EVALUATE_SOURCES",
    "判断资料是否可靠、相关或能支持主张": "EVALUATE_INFORMATION",
    "选择或修改研究方法": "CHOOSE_OR_MODIFY_METHOD",
    "收集或整理材料/数据": "COLLECT_OR_ORGANIZE_DATA",
    "分析材料/数据": "ANALYZE_DATA",
    "解释结果或说明结论限制": "INTERPRET_OR_LIMIT_CONCLUSION",
    "撰写或展示成果": "WRITE_OR_PRESENT",
}


def transform_survey_export(rows: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    """校验虚构导出列、Q1/Q2/Q3/Q7回答和跳题路径，返回模拟canonical字段。"""
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

        recent = _normalize_choice(row.get("Q1_最近是否参与研究型学习任务"), Q1_STATES, "Q1")
        task_type_raw = (row.get("Q2_最近任务类型") or "").strip()
        stages_raw = (row.get("Q3_实际参与环节") or "").strip()
        ai_raw = (row.get("Q7_最近任务AI使用") or "").strip()
        if recent != "YES":
            if any(value and value != "NA_SKIP" for value in (task_type_raw, stages_raw, ai_raw)):
                raise ValueError(f"第 {index} 行Q1非是路径不得填写Q2、Q3或Q7；应记NA_SKIP")
            task_type, stages, ai_used = "NA_SKIP", "NA_SKIP", "NA_SKIP"
        else:
            task_type = _normalize_optional(task_type_raw, TASK_TYPES, "Q2")
            stages = _normalize_stages(stages_raw)
            ai_used = _normalize_optional(ai_raw, Q7_STATES, "Q7")
        output.append({
            "research_id": f"SYN-{response_id}",
            "synthetic_flag": "TRUE",
            "synthetic_version": SYNTHETIC_VERSION,
            "recent_research_task": recent,
            "recent_task_type": task_type,
            "task_participation_stages": stages,
            "ai_used": ai_used,
        })
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


def _normalize_optional(value: str, mapping: dict[str, str], label: str) -> str:
    if not value:
        return "NA_MISS"
    if value in {"记不清", "不确定", "不确定/记不清", "NA_DK"}:
        return "NA_DK"
    if value in {"不愿回答", "NA_REFUSE"}:
        return "NA_REFUSE"
    if value not in mapping:
        raise ValueError(f"{label}存在未知选项：{value!r}")
    return mapping[value]


def _normalize_stages(value: str) -> str:
    if not value:
        return "NA_MISS"
    if value in {"记不清", "不确定"}:
        return "NA_DK"
    if value == "不愿回答":
        return "NA_REFUSE"
    selected = [part.strip() for part in value.split("|") if part.strip()]
    if not selected or len(selected) != len(set(selected)):
        raise ValueError("Q3多选值为空或重复")
    if any(part in {"记不清", "不确定", "不愿回答"} for part in selected):
        raise ValueError("Q3的记不清/拒答选项须与其他多选互斥")
    unknown = set(selected) - PARTICIPATION_STAGES.keys()
    if unknown:
        raise ValueError(f"Q3存在未知选项：{', '.join(sorted(unknown))}")
    return "|".join(PARTICIPATION_STAGES[part] for part in selected)


if __name__ == "__main__":
    raise SystemExit("请通过 tests 调用本导入原型；不得直接导入真人数据。")
