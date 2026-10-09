"""输出任务完成、AI使用分层和五维表现描述。"""

import pandas as pd

from src.generate_synthetic_data import DIMENSIONS
from src.synthetic_analysis_common import count_table, read, write


def main() -> int:
    data = read("student_task_synthetic.csv")
    count_table(data, "task_status", "task_status_distribution.csv")
    count_table(data, "ai_used_in_task", "task_ai_user_share.csv")
    eligible = data[data["analysis_eligible"].astype(str).str.upper() == "TRUE"]
    eligible = eligible.copy()
    eligible[list(DIMENSIONS)] = eligible[list(DIMENSIONS)].astype("int64")
    means = eligible.groupby("ai_used_in_task", dropna=False)[list(DIMENSIONS)].mean().reset_index()
    write(means.melt(id_vars="ai_used_in_task", var_name="dimension", value_name="descriptive_mean"), "task_dimension_means_by_ai_use.csv")
    exp = eligible.groupby("recent_task_type", dropna=False)[list(DIMENSIONS)].mean().reset_index()
    write(exp.melt(id_vars="recent_task_type", var_name="dimension", value_name="descriptive_mean"), "task_dimension_means_by_recent_task_type.csv")
    print(f"任务模拟分项描述完成：{len(eligible)}条COMPLETE进入完整五维分析；PARTIAL/ABORTED未纳入均值。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
