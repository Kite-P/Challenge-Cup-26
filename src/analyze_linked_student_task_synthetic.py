"""检查模拟问卷—任务关联与自愿子样本选择差异。"""

import pandas as pd

from src.synthetic_analysis_common import read, write


def main() -> int:
    survey = read("student_survey_synthetic.csv")
    task = read("student_task_synthetic.csv")
    merged = task.merge(survey, on="research_id", suffixes=("_task", "_survey"), validate="one_to_one")
    write(merged[["research_id", "ai_used_in_task", "ai_used", "synthetic_flag_task"]].rename(columns={"synthetic_flag_task": "synthetic_flag"}), "linked_task_subsample.csv")
    survey["in_task_subsample"] = survey.research_id.isin(task.research_id)
    fields = ["year_of_study", "research_experience_type", "ai_used", "school_type"]
    rows = []
    for field in fields:
        counts = survey.groupby(["in_task_subsample", field], dropna=False).size().reset_index(name="count")
        counts["variable"] = field
        rows.extend(counts.to_dict("records"))
    write(pd.DataFrame(rows), "task_subsample_choice_bias.csv")
    user = merged[merged.ai_used_in_task == "YES"]
    write(user[["research_id", "ai_used_in_task", "asked_reason", "checked_evidence", "modified_ai", "rejected_ai", "synthetic_flag_task"]].rename(columns={"synthetic_flag_task": "synthetic_flag"}), "linked_ai_user_process_only.csv")
    print("问卷—任务关联与子样本选择描述完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
