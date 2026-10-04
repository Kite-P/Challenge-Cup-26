"""建立学生证据与模拟企业维度之间的定性结构映射。"""

import pandas as pd

from src.synthetic_analysis_common import read, write


def main() -> int:
    dimensions = ["information_evaluation", "method_understanding", "independent_judgment", "data_interpretation", "communication", "digital_tool_use", "problem_definition", "limitation_awareness"]
    rows = []
    for dimension in dimensions:
        direct = dimension in {"information_evaluation", "independent_judgment", "problem_definition", "limitation_awareness"}
        rows.append({"enterprise_signal": dimension, "student_survey_signal": "候选问卷相关自报或情境题" if direct else "候选问卷未直接覆盖",
                     "student_task_signal": "任务相关分项（模拟）" if direct else "任务只能提供部分对应",
                     "comparability": "DIRECT" if direct else "PARTIAL" if dimension in {"method_understanding", "data_interpretation"} else "NO_DIRECT_MATCH",
                     "interpretation_boundary": "不同证据来源不可合并为单一数值；本表仅供流程映射。"})
    # 读取模拟产出以确认学生端和岗位端接口均存在。
    _ = read("enterprise_job_labels_synthetic.csv")
    write(pd.DataFrame(rows), "student_enterprise_structural_mapping.csv")
    print("结构映射完成；未构造Gap Score。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
