"""生成仅供流程验证使用的固定种子模拟数据。"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

DIMENSIONS = ("problem_definition", "information_evaluation", "method_fit", "limitation_boundary", "independent_decision", "reasoning_quality")
AI_FIELDS = ("ai_reason_check", "ai_gave_sources", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance")
NA_CODES = ("NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS", "NA_REFUSE")
SURVEY_RECALL_FIELDS = ("ai_used", "ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", *AI_FIELDS, "method_choice_occurred")
TASK_AI_FIELDS = ("ai_stage", "asked_reason", "checked_evidence", "modified_ai", "rejected_ai")


def build_synthetic_bundle(seed: int = 20261004, n_survey: int = 240, n_task: int = 80, n_jobs: int = 360) -> dict[str, list[dict]]:
    """在内存中生成结构稳定、无真实身份的模拟记录。"""
    rng = random.Random(seed)
    ids = [f"SYN-R-{i:04d}" for i in range(1, n_survey + 1)]
    experiences = ["NONE", "COURSE", "SURVEY", "INNOVATION", "MENTOR_PROJECT", "OTHER"]
    survey: list[dict] = []
    for i, research_id in enumerate(ids):
        has_task = i % 13 != 0
        experienced = rng.choices(experiences, weights=[18, 34, 14, 15, 11, 8])[0]
        ai_used = rng.choices(["YES", "NO", "UNSURE"], [58, 34, 8])[0] if has_task else "NA_SKIP"
        method_choice = rng.choice(["YES", "NO", "NA_DK", "NA_MISS"]) if has_task else "NA_SKIP"
        gave_sources = rng.choice(["YES", "NO", "NA_DK"]) if ai_used == "YES" else "NA_SKIP"
        def ai_answer(options: list[str], *, unsure_allowed: bool = True) -> str:
            if ai_used == "YES":
                return rng.choice(options)
            if ai_used == "NO":
                return "NA_SKIP"
            if ai_used == "UNSURE" and unsure_allowed:
                return "NA_DK"
            return "NA_SKIP"

        if ai_used == "NO":
            stages = ["NOT_USED"] * 4
        elif ai_used == "UNSURE":
            stages = ["NA_DK"] * 4
        elif ai_used == "NA_SKIP":
            stages = ["NA_SKIP"] * 4
        else:
            stages = [rng.choice(["YES", "NO", "NA_DK"]) for _ in range(4)]
        details_shown = ai_used == "YES"
        survey.append({
            "research_id": research_id, "synthetic_flag": "TRUE", "synthetic_version": "phase1f_validation_v1",
            "recent_research_task": "YES" if has_task else "NO", "ai_used": ai_used,
            "ai_stage_problem": stages[0], "ai_stage_information": stages[1],
            "ai_stage_method": stages[2], "ai_stage_limitation": stages[3],
            "ai_reason_check": rng.choice(["YES", "NO", "NA_DK", "NA_MISS"]) if details_shown else "NA_SKIP",
            "ai_gave_sources": gave_sources,
            "ai_evidence_check": rng.choice(["CHECK_EXISTENCE", "CHECK_SUPPORT", "COMPARE_SOURCE", "NO_CHECK", "NA_DK", "NA_MISS"]) if gave_sources == "YES" else "NO_RELEVANT_OUTPUT" if gave_sources == "NO" else "NA_DK" if gave_sources == "NA_DK" else "NA_SKIP",
            "ai_output_handling": rng.choice(["ACCEPT", "MODIFY", "PARTIAL", "REJECT", "NOT_ENCOUNTERED", "NA_DK", "NA_MISS"]) if details_shown else "NA_SKIP",
            "ai_disagreement_response": rng.choice(["COMPARE_BASIS", "ASK_AGAIN", "KEEP_VIEW", "ACCEPT", "NOT_ENCOUNTERED", "NA_DK", "NA_MISS"]) if details_shown else "NA_SKIP",
            "method_choice_occurred": method_choice if details_shown else "NA_SKIP" if ai_used in {"NO", "UNSURE", "NA_SKIP"} else "NA_APPL",
            "ai_method_compare": rng.choice(["YES", "NO", "NA_DK", "NA_MISS"]) if details_shown and method_choice == "YES" else "NO_METHOD_CHOICE" if details_shown and method_choice == "NO" else method_choice if details_shown else "NA_SKIP",
            "info_source_check": rng.choice(["SOURCE", "DATE", "SAMPLE", "MEASURE", "SUPPORT", "NA_DK", "NA_MISS"]),
            "a9_first_action": rng.choice(["CHECK_DEFINITION", "CHECK_COVERAGE", "SEEK_OTHER_EVIDENCE", "WITHHOLD_INFERENCE", "NA_MISS"]),
            "a9_reason": rng.choice(["核对指标口径", "比较可支持的结论", "补充其他材料", "NA_MISS"]),
            "research_experience_type": experienced,
            "research_experience_depth": rng.choice(["OBSERVED", "ASSISTED", "LEAD", "NA_DK", "NA_MISS"]) if experienced != "NONE" else "NA_SKIP",
            "method_training": rng.choice(["COURSE", "WORKSHOP", "SELF_STUDY", "NONE", "NA_DK"]),
            "major_group": rng.choice(["ECONOMICS", "MANAGEMENT", "FINANCE", "OTHER_BUSINESS"]),
            "year_of_study": rng.choice(["YEAR_1", "YEAR_2", "YEAR_3", "YEAR_4"]),
            "school_type": rng.choice(["FINANCE_SPECIALIZED", "OTHER_WITH_RELATED_MAJOR", "NA_REFUSE"]),
            "guidance_context": rng.choice(["TEACHER", "COURSE", "PEER", "NONE", "NA_DK"]),
            "unverified_acceptance": ai_answer(["NEVER", "SOMETIMES", "OFTEN", "NA_DK"], unsure_allowed=False),
            "info_confidence_optional": rng.choice(["1", "2", "3", "4", "5", "NA_DK", "NA_APPL"]),
        })

    task_ids = rng.sample(ids, min(n_task, n_survey))
    task: list[dict] = []
    ratings: list[dict] = []
    for research_id in task_ids:
        ai_used = rng.choice(["YES", "NO"])
        status = rng.choices(["COMPLETE", "PARTIAL", "ABORTED"], [0.68, 0.22, 0.10])[0]
        row = {"research_id": research_id, "synthetic_flag": "TRUE", "synthetic_version": "phase1f_validation_v1", "task_status": status, "analysis_eligible": "TRUE" if status == "COMPLETE" else "FALSE", "ai_used_in_task": ai_used,
               "ai_stage": rng.choice(["QUESTION", "INFORMATION", "METHOD", "LIMITATION", "WRITING"]) if ai_used == "YES" else "NA_SKIP",
               "asked_reason": rng.choice(["YES", "NO", "NA_DK"]) if ai_used == "YES" else "NA_SKIP",
               "checked_evidence": rng.choice(["YES", "NO", "NA_DK"]) if ai_used == "YES" else "NA_SKIP",
               "modified_ai": rng.choice(["YES", "NO", "NA_APPL"]) if ai_used == "YES" else "NA_SKIP",
               "rejected_ai": rng.choice(["YES", "NO", "NA_APPL"]) if ai_used == "YES" else "NA_SKIP",
               "final_decision_owner": rng.choice(["STUDENT", "STUDENT_AFTER_AI_INPUT", "UNCLEAR"]) if ai_used == "YES" else rng.choice(["STUDENT", "UNCLEAR"]),
               "research_experience_group": next(item["research_experience_type"] for item in survey if item["research_id"] == research_id)}
        scorable = set(DIMENSIONS) if status == "COMPLETE" else set(rng.sample(list(DIMENSIONS), rng.randint(1, 5))) if status == "PARTIAL" else set()
        for dimension in DIMENSIONS:
            row[dimension] = rng.choices([0, 1, 2], [0.20, 0.50, 0.30])[0] if dimension in scorable else "NOT_SCORABLE"
        task.append(row)
        for dimension in DIMENSIONS:
            if row[dimension] == "NOT_SCORABLE":
                continue
            first = row[dimension]
            second = min(2, first + 1) if rng.random() < 0.13 and first < 2 else max(0, first - 1) if rng.random() < 0.13 and first > 0 else first
            ratings.extend([
                {"research_id": research_id, "rater_id": "R1", "dimension": dimension, "score": first, "rating_status": "RATED", "synthetic_version": "phase1f_validation_v1", "synthetic_flag": "TRUE"},
                {"research_id": research_id, "rater_id": "R2", "dimension": dimension, "score": second, "rating_status": "RATED", "synthetic_version": "phase1f_validation_v1", "synthetic_flag": "TRUE"},
            ])

    families = ["FINANCE", "ACCOUNTING", "AUDIT", "FINANCIAL_ANALYSIS", "DATA_ANALYSIS", "OPERATIONS_ANALYSIS", "CONSULTING_RESEARCH", "DIGITAL"]
    dimensions = ["information_evaluation", "method_understanding", "independent_judgment", "data_interpretation", "communication", "digital_tool_use", "problem_definition", "limitation_awareness"]
    jobs: list[dict] = []
    labels: list[dict] = []
    for i in range(n_jobs):
        key = f"SYN-JOB-{i + 1:05d}"
        family = rng.choices(families, [18, 16, 11, 16, 14, 9, 8, 8])[0]
        jobs.append({"stable_job_record_key": key, "synthetic_flag": "TRUE", "synthetic_version": "phase1f_validation_v1", "job_family": family,
                     "synthetic_title": f"模拟{family}岗位{i + 1:04d}", "synthetic_description": f"模拟职责文本：整理业务信息并形成可复核的工作说明。编号{i + 1:04d}。",
                     "year": rng.choice([2022, 2023, 2024, 2025]), "synthetic_industry": rng.choice(["INDUSTRY_A", "INDUSTRY_B", "INDUSTRY_C"]),
                     "synthetic_region": rng.choice(["REGION_A", "REGION_B", "REGION_C"]), "education_requirement": rng.choice(["BACHELOR", "ANY", "UNKNOWN"]),
                     "experience_requirement": rng.choice(["ENTRY", "1_TO_3", "UNKNOWN"]), "salary_band_synthetic": rng.choice(["LOW", "MID", "HIGH", "NA_MISS"])})
        selected = set(rng.sample(dimensions, rng.randint(1, 4)))
        for dimension in dimensions:
            labels.append({"stable_job_record_key": key, "synthetic_flag": "TRUE", "synthetic_version": "phase1f_validation_v1", "dimension": dimension,
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
