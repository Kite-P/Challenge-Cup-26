"""检查模拟问卷—任务关联与自愿子样本选择差异。"""

import pandas as pd

from src.synthetic_analysis_common import read, write


def main() -> int:
    survey = read("student_survey_synthetic.csv")
    task = read("student_task_synthetic.csv")
    merged = task.merge(survey, on="research_id", suffixes=("_task", "_survey"), validate="one_to_one")
    eligible_flag = merged["analysis_eligible"].astype(str).str.upper() == "TRUE"
    write(merged[["research_id", "task_status", "analysis_eligible", "ai_used_in_task", "ai_used", "synthetic_flag_task"]].rename(columns={"synthetic_flag_task": "synthetic_flag"}), "linked_task_subsample.csv")
    eligible = merged[eligible_flag]
    write(eligible[["research_id", "task_status", "ai_used_in_task", "ai_used", "synthetic_flag_task"]].rename(columns={"synthetic_flag_task": "synthetic_flag"}), "linked_score_eligible_only.csv")
    survey["in_task_subsample"] = survey.research_id.isin(task.research_id)
    fields = ["year_of_study", "recent_task_type", "ai_used", "school_type"]
    rows = []
    for field in fields:
        counts = survey.groupby(["in_task_subsample", field], dropna=False).size().reset_index(name="count")
        counts["variable"] = field
        rows.extend(counts.to_dict("records"))
    write(pd.DataFrame(rows), "task_subsample_choice_bias.csv")
    user = eligible[eligible.ai_used_in_task == "YES"]
    write(user[["research_id", "ai_used_in_task", "asked_reason", "checked_evidence", "modified_ai", "rejected_ai", "synthetic_flag_task"]].rename(columns={"synthetic_flag_task": "synthetic_flag"}), "linked_ai_user_process_only.csv")
    print(f"问卷—任务关联完成：表现关联只纳入{len(eligible)}条COMPLETE可评分记录；AI过程只分析其中AI使用者。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
