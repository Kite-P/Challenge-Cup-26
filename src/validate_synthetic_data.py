"""校验模拟数据标记、严格跳题路径、评分资格和记录关系。"""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from src.generate_synthetic_data import AI_FIELDS, DIMENSIONS, SURVEY_RECALL_FIELDS, SYNTHETIC_VERSION, TASK_AI_FIELDS

SURVEY_STAGE_FIELDS = ("ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation")
AI_RECALL_SKIP = ("ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance")
QUESTIONNAIRE_Q1_STATES = {"YES", "NO", "UNSURE", "NA_REFUSE"}
QUESTIONNAIRE_Q7_STATES = {"YES", "NO", "UNSURE", "NO_TOOL", "NA_APPL", "NA_REFUSE"}
Q10_CHECK_STATES = {"YES", "NO", "NO_RELEVANT_OUTPUT", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q10_OBJECT_OPTIONS = {"SOURCE_EXISTS", "CLAIM_SUPPORT", "DATE_SCOPE", "POPULATION_MEASURE", "DATA_CALCULATION", "CROSS_SOURCE", "OTHER"}
Q10_METHOD_OPTIONS = {"OPEN_ORIGINAL", "SEARCH_INDEPENDENT", "COMPARE_TEXT", "RECALCULATE", "CONSULT_QUALIFIED_PERSON", "OTHER"}
Q13_ACTION_OPTIONS = {"OPEN_ORIGINAL", "SEARCH_INDEPENDENT", "COMPARE_SOURCES", "CHECK_DATE", "CHECK_METHOD", "ASK_PERSON"}
Q13_EXCLUSIVE_OPTIONS = {"NO_SPECIAL_CHECK", "NO_RELATED_EXPERIENCE", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q14_ACTION_OPTIONS = {"UNDERSTOOD_PURPOSE", "MATCHED_TO_QUESTION", "CONSIDERED_DATA", "CHANGED_OR_REJECTED", "MADE_FINAL_CHOICE", "OTHER"}
Q14_AI_COMPARE_STATES = {"YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q3_STAGE_OPTIONS = {"DEFINE_QUESTION", "FIND_OR_EVALUATE_SOURCES", "EVALUATE_INFORMATION", "CHOOSE_OR_MODIFY_METHOD", "COLLECT_OR_ORGANIZE_DATA", "ANALYZE_DATA", "INTERPRET_OR_LIMIT_CONCLUSION", "WRITE_OR_PRESENT", "OTHER"}
Q6_TRAINING_OPTIONS = {"COURSE", "WORKSHOP", "GUIDED_TASK", "SELF_STUDY"}
Q4_MAJOR_STATES = {"ECONOMICS", "PUBLIC_FINANCE", "FINANCE_INSURANCE", "STATISTICS_DATA", "ACCOUNTING_AUDIT", "BUSINESS_MANAGEMENT", "TRADE_LOGISTICS", "OTHER_FINANCE_RELATED", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q5_YEAR_STATES = {"YEAR_1", "YEAR_2", "YEAR_3", "YEAR_4", "NA_REFUSE", "NA_MISS"}
Q8_STAGE_STATES = {"YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q9_STATES = {"YES", "NO", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q11_STATES = {"ACCEPT", "ACCEPT_AFTER_CHECK", "MODIFY", "PARTIAL", "REFERENCE_ONLY", "REJECT", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q12_STATES = {"COMPARE_BASIS", "ASK_AGAIN", "ASK_PERSON", "ACCEPT_AI", "KEEP_ORIGINAL", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q15_STATES = {"NEVER", "SOMETIMES", "OFTEN", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q18_STATES = {"CHECK_DEFINITION", "SEEK_OTHER_EVIDENCE", "DIRECT_EFFECT_CLAIM", "GENERALIZE_TO_ALL", "NA_DK", "NA_REFUSE", "NA_MISS"}
Q20_STATES = {"1", "2", "3", "4", "5", "NA_DK", "NA_REFUSE", "NA_MISS"}


def load_bundle(directory: Path = Path("data/synthetic")) -> dict[str, list[dict]]:
    """读取项目的五类模拟CSV。"""
    mapping = {"survey": "student_survey_synthetic.csv", "task": "student_task_synthetic.csv", "ratings": "task_ratings_synthetic.csv", "jobs": "enterprise_jobs_synthetic.csv", "labels": "enterprise_job_labels_synthetic.csv"}
    bundle = {}
    for key, filename in mapping.items():
        with (directory / filename).open(encoding="utf-8-sig", newline="") as stream:
            bundle[key] = list(csv.DictReader(stream))
    return bundle


def _scoreable(value: object) -> bool:
    """判断字段是否为真实可评分的0—2分，而不是缺失哨兵。"""
    return str(value) in {"0", "1", "2"}


def _valid_multiselect(value: object, options: set[str], exclusive: set[str]) -> bool:
    """检查去重多选或单独的互斥状态码。"""
    if not isinstance(value, str) or not value:
        return False
    selected = value.split("|")
    if len(selected) != len(set(selected)):
        return False
    if len(selected) == 1 and selected[0] in exclusive:
        return True
    return bool(selected) and not (set(selected) & exclusive) and set(selected) <= options and all(selected)


def strict_skip_violation_count(bundle: dict) -> int:
    """按问卷候选跳题树计数，不把未展示题目的未知当作合法缺失。"""
    count = 0
    for row in bundle["survey"]:
        recent = row.get("recent_research_task")
        if recent not in QUESTIONNAIRE_Q1_STATES:
            count += 1
        if not _valid_multiselect(row.get("info_source_check_actions"), Q13_ACTION_OPTIONS, Q13_EXCLUSIVE_OPTIONS):
            count += 1
        training_items = str(row.get("training_need", "")).split("|")
        training_specials = {"NO_ADDITIONAL_NEED", "NA_DK", "NA_REFUSE", "NA_MISS"}
        training_options = {"RESEARCH_QUESTION", "SOURCE_EVALUATION", "AI_CHECKING", "METHOD_SELECTION", "SURVEY_SAMPLING", "DATA_ANALYSIS", "LIMITATION_INTERPRETATION", "ACADEMIC_INTEGRITY", "MENTOR_FEEDBACK"}
        if len(training_items) > 3 or not _valid_multiselect(row.get("training_need"), training_options, training_specials):
            count += 1
        if not _valid_multiselect(row.get("method_training"), Q6_TRAINING_OPTIONS, {"NONE", "NA_DK", "NA_REFUSE", "NA_MISS"}):
            count += 1
        if row.get("policy_awareness") not in {"RULES_CLEAR_BOUNDARIES", "RULES_UNSPECIFIC", "INCONSISTENT", "NOT_HEARD", "NA_DK", "NA_REFUSE", "NA_MISS"}:
            count += 1
        if row.get("major_group") not in Q4_MAJOR_STATES:
            count += 1
        if row.get("year_of_study") not in Q5_YEAR_STATES:
            count += 1
        if row.get("info_confidence_optional") not in Q20_STATES:
            count += 1
        if row.get("a9_first_action") not in Q18_STATES:
            count += 1
        open_concern = row.get("open_concern")
        if open_concern not in {"NO_RELATED_VIEW", "NA_DK", "NA_REFUSE", "NA_MISS"} and not (isinstance(open_concern, str) and open_concern.startswith("模拟回答：")):
            count += 1
        if recent != "YES":
            count += sum(row.get(field) != "NA_SKIP" for field in SURVEY_RECALL_FIELDS)
            continue
        if row.get("recent_task_type") not in {"COURSE_RESEARCH", "COURSE_SURVEY_REPORT", "INNOVATION_PROJECT", "COMPETITION_RESEARCH", "MENTOR_PROJECT", "OTHER_RESEARCH_TASK", "NA_DK", "NA_REFUSE", "NA_MISS"}:
            count += 1
        participation = row.get("task_participation_stages", "")
        if not _valid_multiselect(participation, Q3_STAGE_OPTIONS, {"NA_DK", "NA_REFUSE", "NA_MISS"}):
            count += 1
        if row.get("guidance_context") == "NA_SKIP":
            count += 1
        ai_used = row.get("ai_used")
        if ai_used not in QUESTIONNAIRE_Q7_STATES:
            count += 1
        if ai_used != "YES":
            count += sum(row.get(field) != "NA_SKIP" for field in SURVEY_STAGE_FIELDS)
            count += sum(row.get(field) != "NA_SKIP" for field in AI_RECALL_SKIP if field != "method_choice_occurred")
        else:
            count += sum(row.get(field) not in Q8_STAGE_STATES for field in SURVEY_STAGE_FIELDS)
            count += int(row.get("ai_reason_check") not in Q9_STATES)
            count += int(row.get("ai_output_handling") not in Q11_STATES)
            count += int(row.get("ai_disagreement_response") not in Q12_STATES)
            count += int(row.get("unverified_acceptance") not in Q15_STATES)
        checked = row.get("ai_evidence_checked")
        if ai_used != "YES":
            count += sum(row.get(field) != "NA_SKIP" for field in ("ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods"))
        elif checked not in Q10_CHECK_STATES:
            count += 1
        elif checked == "YES":
            count += sum(not _valid_multiselect(row.get(field), options, {"NA_DK", "NA_REFUSE", "NA_MISS"}) for field, options in (("ai_evidence_objects", Q10_OBJECT_OPTIONS), ("ai_evidence_methods", Q10_METHOD_OPTIONS)))
        else:
            count += sum(row.get(field) != "NA_SKIP" for field in ("ai_evidence_objects", "ai_evidence_methods"))

        method_choice = row.get("method_choice_occurred")
        valid_method_choice_states = {"YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"}
        if method_choice not in valid_method_choice_states:
            count += 1
        if method_choice == "YES":
            count += int(not _valid_multiselect(row.get("method_decision_actions"), Q14_ACTION_OPTIONS, {"NA_DK", "NA_REFUSE", "NA_MISS"}))
        elif row.get("method_decision_actions") != "NA_SKIP":
            count += 1
        if ai_used == "YES":
            count += int(row.get("ai_method_compare") not in Q14_AI_COMPARE_STATES)
        elif row.get("ai_method_compare") != "NA_SKIP":
            count += 1
    return count


def ai_nonuser_field_violation_count(bundle: dict) -> int:
    """统计AI未使用/不确定问卷与任务中的有效AI过程字段违规数。"""
    count = 0
    for row in bundle["survey"]:
        if row["ai_used"] != "YES":
            count += sum(row.get(field) != "NA_SKIP" for field in AI_FIELDS)
    for row in bundle["task"]:
        if row["ai_used_in_task"] == "NO":
            count += sum(row.get(field) != "NA_SKIP" for field in TASK_AI_FIELDS)
            if row["final_decision_owner"] == "STUDENT_AFTER_AI_INPUT":
                count += 1
    return count


def validate_bundle(bundle: dict) -> list[str]:
    """返回全部数据质量及逻辑路径错误。"""
    errors: list[str] = []
    survey, task, ratings, jobs, labels = (bundle[name] for name in ("survey", "task", "ratings", "jobs", "labels"))
    for name, rows in (("survey", survey), ("task", task), ("ratings", ratings), ("jobs", jobs), ("labels", labels)):
        if any(row.get("synthetic_flag") != "TRUE" for row in rows):
            errors.append(f"{name}: 存在未标记为模拟的数据行")
        if any(row.get("synthetic_version") != SYNTHETIC_VERSION for row in rows):
            errors.append(f"{name}: 模拟数据版本缺失或不匹配")

    survey_ids = [row["research_id"] for row in survey]
    if len(survey_ids) != len(set(survey_ids)):
        errors.append("research_id 不唯一")
    survey_set = set(survey_ids)
    task_ids = [row["research_id"] for row in task]
    task_set = set(task_ids)
    if len(task_ids) != len(task_set):
        errors.append("任务research_id重复")
    if not task_set <= survey_set:
        errors.append("任务记录不是问卷样本子集")

    if strict_skip_violation_count(bundle):
        errors.append(f"问卷严格跳题路径违规：{strict_skip_violation_count(bundle)}项")
    if ai_nonuser_field_violation_count(bundle):
        errors.append(f"AI未使用者过程字段违规：{ai_nonuser_field_violation_count(bundle)}项")

    task_by_id = {row["research_id"]: row for row in task}
    status_values = {"COMPLETE", "PARTIAL", "ABORTED"}
    for row in task:
        if "reasoning_quality" in row:
            errors.append("旧版reasoning_quality不属于当前五维评分字段")
        status = row.get("task_status")
        scoreable = [_scoreable(row.get(dimension)) for dimension in DIMENSIONS]
        if status not in status_values:
            errors.append("任务状态无效")
            continue
        if row.get("analysis_eligible") != ("TRUE" if status == "COMPLETE" else "FALSE"):
            errors.append("analysis_eligible与task_status不一致")
        if status == "COMPLETE" and not all(scoreable):
            errors.append("COMPLETE任务存在不可评分维度")
        if status == "PARTIAL" and (not any(scoreable) or all(scoreable)):
            errors.append("PARTIAL任务须同时有可评分和不可评分维度")
        if status == "ABORTED" and any(scoreable):
            errors.append("ABORTED任务不应有有效评分")
        if status == "ABORTED" and row.get("final_decision_owner") != "NOT_REACHED":
            errors.append("ABORTED任务不得虚构最终决策归属，应记NOT_REACHED")
        for dimension, valid in zip(DIMENSIONS, scoreable, strict=True):
            value = row.get(dimension)
            if not valid and value != "NOT_SCORABLE":
                if str(value).lstrip("-").isdigit():
                    errors.append(f"任务评分超出0—2范围：{dimension}")
                else:
                    errors.append(f"任务维度缺失码无效：{dimension}")
                break
            if row["ai_used_in_task"] == "NO" and row["final_decision_owner"] == "STUDENT_AFTER_AI_INPUT":
                errors.append("未使用AI任务出现AI参与决策类别")
                break
        if row["ai_used_in_task"] not in {"YES", "NO"}:
            errors.append("任务AI使用状态无效")
        if row["ai_used_in_task"] == "NO" and any(row.get(field) != "NA_SKIP" for field in TASK_AI_FIELDS):
            errors.append("任务未使用AI者的AI过程字段未结构性跳题")
        if row["final_decision_owner"] not in {"STUDENT", "STUDENT_AFTER_AI_INPUT", "UNCLEAR", "NOT_REACHED"}:
            errors.append("最终决策归属类别无效")

    if strict_skip_violation_count(bundle):
        for row in survey:
            if row["recent_research_task"] == "NO" and any(row.get(field) != "NA_SKIP" for field in SURVEY_RECALL_FIELDS):
                errors.append("无最近任务路径存在未展示题目的非NA_SKIP值")
                break
            if row["ai_used"] == "NO" and any(row.get(field) != "NA_SKIP" for field in AI_RECALL_SKIP):
                errors.append("AI未使用路径存在未展示题目的非NA_SKIP值")
                break
            if row["ai_used"] == "UNSURE" and any(row.get(field) != "NA_SKIP" for field in AI_RECALL_SKIP):
                errors.append("AI不确定路径存在未展示题目的非NA_SKIP值")
                break

    rating_keys = [(row["research_id"], row["rater_id"], row["dimension"]) for row in ratings]
    if len(rating_keys) != len(set(rating_keys)):
        errors.append("评分记录复合键重复")
    ratings_by_cell: dict[tuple[str, str], set[str]] = {}
    for row in ratings:
        task_row = task_by_id.get(row["research_id"])
        if task_row is None:
            errors.append("评分记录不属于任务子样本")
            continue
        if row["dimension"] not in DIMENSIONS or not _scoreable(task_row.get(row["dimension"])):
            errors.append("评分者评定了不存在或不可评分的作答维度")
        if str(row["score"]) not in {"0", "1", "2"}:
            errors.append("评分者分数超出0—2")
        if row["rater_id"] not in {"R1", "R2"}:
            errors.append("评分者编号无效")
        if row.get("rating_status") != "RATED":
            errors.append("评分记录状态无效")
        ratings_by_cell.setdefault((row["research_id"], row["dimension"]), set()).add(row["rater_id"])
    for row in task:
        for dimension in DIMENSIONS:
            if _scoreable(row[dimension]) and ratings_by_cell.get((row["research_id"], dimension), set()) != {"R1", "R2"}:
                errors.append("可评分维度未由R1/R2成对评分")
                break

    job_keys = [row["stable_job_record_key"] for row in jobs]
    if len(job_keys) != len(set(job_keys)):
        errors.append("stable_job_record_key 不唯一")
    job_set = set(job_keys)
    if any(row["stable_job_record_key"] not in job_set for row in labels):
        errors.append("岗位标签不能关联到岗位表")
    return errors


def quality_summary(bundle: dict) -> dict[str, int]:
    """依据实际记录计算质量报告指标。"""
    statuses = Counter(row.get("task_status", "INVALID") for row in bundle["task"])
    unscorable = sum(value == "NOT_SCORABLE" for row in bundle["task"] for value in (row.get(dimension) for dimension in DIMENSIONS))
    score_anomalies = sum(not (_scoreable(row.get(dimension)) or row.get(dimension) == "NOT_SCORABLE") for row in bundle["task"] for dimension in DIMENSIONS)
    duplicate_research_ids = len(bundle["survey"]) - len({row["research_id"] for row in bundle["survey"]})
    duplicate_job_keys = len(bundle["jobs"]) - len({row["stable_job_record_key"] for row in bundle["jobs"]})
    task_ids = {row["research_id"] for row in bundle["task"]}
    survey_ids = {row["research_id"] for row in bundle["survey"]}
    rating_not_task = sum(row["research_id"] not in task_ids for row in bundle["ratings"])
    task_not_survey = sum(row["research_id"] not in survey_ids for row in bundle["task"])
    metrics = {
        "strict_skip_violations": strict_skip_violation_count(bundle),
        "complete_count": statuses["COMPLETE"], "partial_count": statuses["PARTIAL"], "aborted_count": statuses["ABORTED"],
        "analysis_eligible_count": sum(row.get("analysis_eligible") == "TRUE" and row.get("task_status") == "COMPLETE" for row in bundle["task"]),
        "unscorable_dimension_count": unscorable, "rating_row_count": len(bundle["ratings"]),
        "ai_nonuser_field_violations": ai_nonuser_field_violation_count(bundle), "score_range_anomalies": score_anomalies,
        "duplicate_research_id_count": duplicate_research_ids, "duplicate_job_key_count": duplicate_job_keys,
        "task_not_survey_count": task_not_survey, "rating_not_task_count": rating_not_task,
    }
    metrics["anomaly_count"] = sum(metrics[key] for key in ("strict_skip_violations", "ai_nonuser_field_violations", "score_range_anomalies", "duplicate_research_id_count", "duplicate_job_key_count", "task_not_survey_count", "rating_not_task_count"))
    metrics["validation_error_count"] = len(validate_bundle(bundle))
    return metrics


def validate_files(directory: Path = Path("data/synthetic")) -> list[str]:
    """从CSV读取记录，执行业务规则和敏感格式扫描。"""
    bundle = load_bundle(directory)
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
    print("模拟数据结构、严格跳题、任务可评分资格和关联校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
