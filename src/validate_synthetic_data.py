"""校验模拟数据标记、主键、跳题和子样本关系。"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from src.generate_synthetic_data import AI_FIELDS, DIMENSIONS


def validate_bundle(bundle: dict) -> list[str]:
    """返回全部发现的问题；空列表表示通过。"""
    errors: list[str] = []
    survey, task, ratings, jobs, labels = (bundle[name] for name in ("survey", "task", "ratings", "jobs", "labels"))
    for name, rows in (("survey", survey), ("task", task), ("ratings", ratings), ("jobs", jobs), ("labels", labels)):
        if any(row.get("synthetic_flag") != "TRUE" for row in rows):
            errors.append(f"{name}: 存在未标记为模拟的数据行")
    survey_ids = [row["research_id"] for row in survey]
    if len(survey_ids) != len(set(survey_ids)):
        errors.append("research_id 不唯一")
    survey_set = set(survey_ids)
    task_ids = {row["research_id"] for row in task}
    if not task_ids <= survey_set:
        errors.append("任务记录不是问卷样本子集")
    if not {row["research_id"] for row in ratings} <= task_ids:
        errors.append("评分记录不是任务样本子集")
    keys = [row["stable_job_record_key"] for row in jobs]
    if len(keys) != len(set(keys)):
        errors.append("stable_job_record_key 不唯一")
    for row in task:
        for dimension in DIMENSIONS:
            if str(row.get(dimension)) not in {"0", "1", "2"}:
                errors.append(f"任务评分超出0—2范围：{dimension}")
                break
        if row["ai_used_in_task"] != "YES" and any(row[field] not in {"NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS"} for field in ("asked_reason", "checked_evidence", "modified_ai", "rejected_ai")):
            errors.append("任务AI未使用者出现有效AI过程答案")
    for row in survey:
        if row["ai_used"] != "YES" and any(row.get(field) not in {"NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS", "NOT_USED", "NO_RELEVANT_OUTPUT", "NOT_ENCOUNTERED"} for field in AI_FIELDS):
            errors.append("问卷AI未使用者出现有效AI协作过程答案")
        if row["ai_gave_sources"] == "NO" and row["ai_evidence_check"] != "NO_RELEVANT_OUTPUT":
            errors.append("AI未给出来源时依据处理状态不一致")
        if row["method_choice_occurred"] == "NO" and row["ai_method_compare"] not in {"NA_APPL", "NA_SKIP"}:
            errors.append("未发生方法选择时生成了方法比较答案")
        if row["recent_research_task"] == "NO" and row["ai_used"] != "NA_SKIP":
            errors.append("无最近任务记录未按跳题规则编码")
    return errors


def validate_files(directory: Path = Path("data/synthetic")) -> list[str]:
    """从模拟CSV加载记录并运行结构校验及轻量敏感信息扫描。"""
    mapping = {"survey": "student_survey_synthetic.csv", "task": "student_task_synthetic.csv", "ratings": "task_ratings_synthetic.csv", "jobs": "enterprise_jobs_synthetic.csv", "labels": "enterprise_job_labels_synthetic.csv"}
    bundle = {key: list(csv.DictReader((directory / filename).open(encoding="utf-8-sig", newline=""))) for key, filename in mapping.items()}
    errors = validate_bundle(bundle)
    text = "\n".join(path.read_text(encoding="utf-8-sig") for path in directory.glob("*.csv"))
    if re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", text) or re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text):
        errors.append("模拟CSV出现手机号或邮箱格式")
    if re.search(r"(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,})", text):
        errors.append("模拟CSV出现疑似API密钥格式")
    return errors


def main() -> int:
    errors = validate_files()
    if errors:
        print("校验失败：" + "；".join(errors))
        return 1
    print("模拟数据结构、跳题和关联校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
