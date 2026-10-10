"""生成仅供流程验证使用的固定种子模拟数据。"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

DIMENSIONS = ("problem_definition", "information_evaluation", "method_fit", "limitation_boundary", "independent_decision")
SYNTHETIC_VERSION = "phase2b_v06_contract_v2"
AI_FIELDS = ("ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance")
SURVEY_RECALL_FIELDS = ("ai_used", "ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", *AI_FIELDS, "method_choice_occurred", "method_decision_actions", "recent_task_type", "task_participation_stages", "guidance_context")
TASK_AI_FIELDS = ("ai_stage", "asked_reason", "checked_evidence", "modified_ai", "rejected_ai")


def build_synthetic_bundle(seed: int = 20261004, n_survey: int = 240, n_task: int = 80, n_jobs: int = 360) -> dict[str, list[dict]]:
    """在内存中生成结构稳定、无真实身份的模拟记录。"""
    rng = random.Random(seed)
    ids = [f"SYN-R-{i:04d}" for i in range(1, n_survey + 1)]
    task_types = ["COURSE_RESEARCH", "COURSE_SURVEY_REPORT", "INNOVATION_PROJECT", "COMPETITION_RESEARCH", "MENTOR_PROJECT", "OTHER_RESEARCH_TASK"]
    participation_stages = ["DEFINE_QUESTION", "FIND_OR_EVALUATE_SOURCES", "CHOOSE_OR_MODIFY_METHOD", "COLLECT_OR_ORGANIZE_DATA", "ANALYZE_DATA", "INTERPRET_OR_LIMIT_CONCLUSION", "WRITE_OR_PRESENT"]
    survey: list[dict] = []
    for i, research_id in enumerate(ids):
        recent_task = ("NO", "UNSURE", "NA_REFUSE", "YES")[i % 4]
        has_task = recent_task == "YES"
        task_type = rng.choice([*task_types, "NA_DK", "NA_REFUSE", "NA_MISS"]) if has_task else "NA_SKIP"
        participation = (rng.choice(["NA_DK", "NA_REFUSE", "NA_MISS"]) if i % 19 == 0 else "|".join(rng.sample([*participation_stages, "OTHER"], rng.randint(1, 3)))) if has_task else "NA_SKIP"
        ai_used = ("YES", "NO", "UNSURE", "NO_TOOL", "NA_APPL", "NA_REFUSE")[(i // 4) % 6] if has_task else "NA_SKIP"
        method_choice = ("YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS")[(i // 24) % 5] if has_task else "NA_SKIP"
        evidence_checked = ("YES", "NO", "NO_RELEVANT_OUTPUT", "NA_DK", "NA_REFUSE", "NA_MISS")[(i // 24) % 6] if ai_used == "YES" else "NA_SKIP"
        evidence_objects = ("|".join(rng.sample(["SOURCE_EXISTS", "CLAIM_SUPPORT", "DATE_SCOPE", "POPULATION_MEASURE", "DATA_CALCULATION", "CROSS_SOURCE", "OTHER"], rng.randint(1, 2))) if i % 5 < 2 else ("NA_DK", "NA_REFUSE", "NA_MISS")[i % 5 - 2]) if evidence_checked == "YES" else "NA_SKIP"
        evidence_methods = ("|".join(rng.sample(["OPEN_ORIGINAL", "SEARCH_INDEPENDENT", "COMPARE_TEXT", "RECALCULATE", "CONSULT_QUALIFIED_PERSON", "OTHER"], rng.randint(1, 2))) if i % 5 < 2 else ("NA_DK", "NA_REFUSE", "NA_MISS")[i % 5 - 2]) if evidence_checked == "YES" else "NA_SKIP"
        training_need = rng.choice(["NO_ADDITIONAL_NEED", "NA_DK", "NA_REFUSE", "NA_MISS"]) if i % 13 == 0 else "|".join(rng.sample(["RESEARCH_QUESTION", "SOURCE_EVALUATION", "AI_CHECKING", "METHOD_SELECTION", "SURVEY_SAMPLING", "DATA_ANALYSIS", "LIMITATION_INTERPRETATION", "ACADEMIC_INTEGRITY", "MENTOR_FEEDBACK"], rng.randint(1, 3)))
        def ai_answer(options: list[str]) -> str:
            if ai_used == "YES":
                return rng.choice(options)
            return "NA_SKIP"

        if ai_used == "YES":
            stages = [rng.choice(["YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"]) for _ in range(4)]
        else:
            stages = ["NA_SKIP"] * 4
        details_shown = ai_used == "YES"
        survey.append({
            "research_id": research_id, "synthetic_flag": "TRUE", "synthetic_version": SYNTHETIC_VERSION,
            "recent_research_task": recent_task, "ai_used": ai_used,
            "ai_stage_problem": stages[0], "ai_stage_information": stages[1],
            "ai_stage_method": stages[2], "ai_stage_limitation": stages[3],
            "ai_reason_check": rng.choice(["YES", "NO", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"]) if details_shown else "NA_SKIP",
            "ai_evidence_checked": evidence_checked,
            "ai_evidence_objects": evidence_objects,
            "ai_evidence_methods": evidence_methods,
            "ai_output_handling": rng.choice(["ACCEPT", "ACCEPT_AFTER_CHECK", "MODIFY", "PARTIAL", "REFERENCE_ONLY", "REJECT", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"]) if details_shown else "NA_SKIP",
            "ai_disagreement_response": rng.choice(["COMPARE_BASIS", "ASK_AGAIN", "ASK_PERSON", "ACCEPT_AI", "KEEP_ORIGINAL", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"]) if details_shown else "NA_SKIP",
            "method_choice_occurred": method_choice,
            "method_decision_actions": "|".join(rng.sample(["UNDERSTOOD_PURPOSE", "MATCHED_TO_QUESTION", "CONSIDERED_DATA", "CHANGED_OR_REJECTED", "MADE_FINAL_CHOICE", "OTHER"], rng.randint(1, 3))) if method_choice == "YES" else "NA_SKIP",
            "ai_method_compare": rng.choice(["YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"]) if details_shown else "NA_SKIP",
            "info_source_check_actions": "|".join(rng.sample(["OPEN_ORIGINAL", "SEARCH_INDEPENDENT", "COMPARE_SOURCES", "CHECK_DATE", "CHECK_METHOD", "ASK_PERSON"], rng.randint(1, 3))) if i % 11 < 7 else rng.choice(["NO_SPECIAL_CHECK", "NO_RELATED_EXPERIENCE", "NA_DK", "NA_REFUSE", "NA_MISS"]),
            "a9_first_action": rng.choice(["CHECK_DEFINITION", "SEEK_OTHER_EVIDENCE", "DIRECT_EFFECT_CLAIM", "GENERALIZE_TO_ALL", "NA_DK", "NA_REFUSE", "NA_MISS"]),
            "a9_reason": rng.choice(["核对指标口径", "比较可支持的结论", "补充其他材料", "NA_MISS"]),
            "recent_task_type": task_type,
            "task_participation_stages": participation,
            "method_training": ("NONE", "NA_DK", "NA_REFUSE", "NA_MISS")[i % 4] if i % 17 == 0 else "|".join(rng.sample(["COURSE", "WORKSHOP", "GUIDED_TASK", "SELF_STUDY"], rng.randint(1, 3))),
            "major_group": rng.choice(["ECONOMICS", "PUBLIC_FINANCE", "FINANCE_INSURANCE", "STATISTICS_DATA", "ACCOUNTING_AUDIT", "BUSINESS_MANAGEMENT", "TRADE_LOGISTICS", "OTHER_FINANCE_RELATED", "NA_DK", "NA_REFUSE", "NA_MISS"]),
            "year_of_study": rng.choice(["YEAR_1", "YEAR_2", "YEAR_3", "YEAR_4", "NA_REFUSE", "NA_MISS"]),
            "school_type": rng.choice(["FINANCE_SPECIALIZED", "OTHER_WITH_RELATED_MAJOR", "NA_REFUSE"]),
            "guidance_context": rng.choice(["TEACHER", "COURSE", "PEER", "NONE", "NA_DK"]) if has_task else "NA_SKIP",
            "training_need": training_need,
            "policy_awareness": rng.choice(["RULES_CLEAR_BOUNDARIES", "RULES_UNSPECIFIC", "INCONSISTENT", "NOT_HEARD", "NA_DK", "NA_REFUSE", "NA_MISS"]),
            "open_concern": rng.choice(["模拟回答：核对来源与适用范围。", "NO_RELATED_VIEW", "NA_DK", "NA_REFUSE", "NA_MISS"]),
            "unverified_acceptance": ai_answer(["NEVER", "SOMETIMES", "OFTEN", "NOT_ENCOUNTERED", "NA_DK", "NA_REFUSE", "NA_MISS"]),
            "info_confidence_optional": rng.choice(["1", "2", "3", "4", "5", "NA_DK", "NA_REFUSE", "NA_MISS"]),
        })

    task_ids = rng.sample(ids, min(n_task, n_survey))
    task: list[dict] = []
    ratings: list[dict] = []
    for research_id in task_ids:
        ai_used = rng.choice(["YES", "NO"])
        status = rng.choices(["COMPLETE", "PARTIAL", "ABORTED"], [0.68, 0.22, 0.10])[0]
        row = {"research_id": research_id, "synthetic_flag": "TRUE", "synthetic_version": SYNTHETIC_VERSION, "task_status": status, "analysis_eligible": "TRUE" if status == "COMPLETE" else "FALSE", "ai_used_in_task": ai_used,
               "ai_stage": rng.choice(["QUESTION", "INFORMATION", "METHOD", "LIMITATION", "WRITING"]) if ai_used == "YES" else "NA_SKIP",
               "asked_reason": rng.choice(["YES", "NO", "NA_DK"]) if ai_used == "YES" else "NA_SKIP",
               "checked_evidence": rng.choice(["YES", "NO", "NA_DK"]) if ai_used == "YES" else "NA_SKIP",
               "modified_ai": rng.choice(["YES", "NO", "NA_APPL"]) if ai_used == "YES" else "NA_SKIP",
               "rejected_ai": rng.choice(["YES", "NO", "NA_APPL"]) if ai_used == "YES" else "NA_SKIP",
               "final_decision_owner": "NOT_REACHED" if status == "ABORTED" else rng.choice(["STUDENT", "STUDENT_AFTER_AI_INPUT", "UNCLEAR"]) if ai_used == "YES" else rng.choice(["STUDENT", "UNCLEAR"]),
               "recent_task_type": next(item["recent_task_type"] for item in survey if item["research_id"] == research_id)}
        scorable = set(DIMENSIONS) if status == "COMPLETE" else set(rng.sample(list(DIMENSIONS), rng.randint(1, len(DIMENSIONS) - 1))) if status == "PARTIAL" else set()
        for dimension in DIMENSIONS:
            row[dimension] = rng.choices([0, 1, 2], [0.20, 0.50, 0.30])[0] if dimension in scorable else "NOT_SCORABLE"
        task.append(row)
        for dimension in DIMENSIONS:
            if row[dimension] == "NOT_SCORABLE":
                continue
            first = row[dimension]
            second = min(2, first + 1) if rng.random() < 0.13 and first < 2 else max(0, first - 1) if rng.random() < 0.13 and first > 0 else first
            ratings.extend([
                {"research_id": research_id, "rater_id": "R1", "dimension": dimension, "score": first, "rating_status": "RATED", "synthetic_version": SYNTHETIC_VERSION, "synthetic_flag": "TRUE"},
                {"research_id": research_id, "rater_id": "R2", "dimension": dimension, "score": second, "rating_status": "RATED", "synthetic_version": SYNTHETIC_VERSION, "synthetic_flag": "TRUE"},
            ])

    families = ["FINANCE", "ACCOUNTING", "AUDIT", "FINANCIAL_ANALYSIS", "DATA_ANALYSIS", "OPERATIONS_ANALYSIS", "CONSULTING_RESEARCH", "DIGITAL"]
    dimensions = ["information_evaluation", "method_understanding", "independent_judgment", "data_interpretation", "communication", "digital_tool_use", "problem_definition", "limitation_awareness"]
    jobs: list[dict] = []
    labels: list[dict] = []
    for i in range(n_jobs):
        key = f"SYN-JOB-{i + 1:05d}"
        family = rng.choices(families, [18, 16, 11, 16, 14, 9, 8, 8])[0]
        jobs.append({"stable_job_record_key": key, "synthetic_flag": "TRUE", "synthetic_version": SYNTHETIC_VERSION, "job_family": family,
                     "synthetic_title": f"模拟{family}岗位{i + 1:04d}", "synthetic_description": f"模拟职责文本：整理业务信息并形成可复核的工作说明。编号{i + 1:04d}。",
                     "year": rng.choice([2022, 2023, 2024, 2025]), "synthetic_industry": rng.choice(["INDUSTRY_A", "INDUSTRY_B", "INDUSTRY_C"]),
                     "synthetic_region": rng.choice(["REGION_A", "REGION_B", "REGION_C"]), "education_requirement": rng.choice(["BACHELOR", "ANY", "UNKNOWN"]),
                     "experience_requirement": rng.choice(["ENTRY", "1_TO_3", "UNKNOWN"]), "salary_band_synthetic": rng.choice(["LOW", "MID", "HIGH", "NA_MISS"])})
        selected = set(rng.sample(dimensions, rng.randint(1, 4)))
        for dimension in dimensions:
            labels.append({"stable_job_record_key": key, "synthetic_flag": "TRUE", "synthetic_version": SYNTHETIC_VERSION, "dimension": dimension,
                           "label": int(dimension in selected), "label_source": "SIMULATED_GROUND_TRUTH"})
    return {"survey": survey, "task": task, "ratings": ratings, "jobs": jobs, "labels": labels, "dimensions": list(DIMENSIONS)}


def write_bundle(bundle: dict, output_dir: Path) -> None:
    """将数据写入项目指定的纯模拟数据目录，不清理或删除目录。"""
    allowed = Path("data/synthetic").resolve()
    target = output_dir.resolve()
    if target != allowed:
        raise ValueError("生成器只允许写入 data/synthetic/。")
    target.mkdir(parents=True, exist_ok=True)
    mapping = {"survey": "student_survey_synthetic.csv", "task": "student_task_synthetic.csv", "ratings": "task_ratings_synthetic.csv", "jobs": "enterprise_jobs_synthetic.csv", "labels": "enterprise_job_labels_synthetic.csv"}
    for key, filename in mapping.items():
        rows = bundle[key]
        with (target / filename).open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]) if rows else ["synthetic_flag"])
            writer.writeheader()
            writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成固定种子的流程模拟数据")
    parser.add_argument("--seed", type=int, default=20261004)
    args = parser.parse_args()
    write_bundle(build_synthetic_bundle(seed=args.seed), Path("data/synthetic"))
    print("已生成纯模拟CSV；未接触真实数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
