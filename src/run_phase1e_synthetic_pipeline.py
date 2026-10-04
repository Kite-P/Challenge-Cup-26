"""依次运行全部Phase 1E模拟流程并生成质量报告。"""

from __future__ import annotations

import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from src.generate_synthetic_data import build_synthetic_bundle, write_bundle
from src.validate_synthetic_data import validate_files


def main() -> int:
    write_bundle(build_synthetic_bundle(), Path("data/synthetic"))
    errors = validate_files()
    if errors:
        print("校验失败：" + "；".join(errors))
        return 1
    modules = ["src.analyze_student_survey_synthetic", "src.analyze_task_synthetic", "src.analyze_linked_student_task_synthetic",
               "src.analyze_rater_agreement_synthetic", "src.analyze_enterprise_profile_synthetic", "src.build_student_enterprise_mapping_synthetic"]
    for module in modules:
        result = subprocess.run([sys.executable, "-m", module], check=False)
        if result.returncode:
            print(f"模块失败：{module}，退出码 {result.returncode}")
            return result.returncode
    try:
        result = subprocess.run([sys.executable, "-m", "src.plot_synthetic_results"], check=False)
        if result.returncode:
            print("可选模拟绘图未通过。")
            return result.returncode
    except Exception as exc:
        print(f"可选绘图跳过：{exc}")

    data_dir = Path("data/synthetic")
    survey = pd.read_csv(data_dir / "student_survey_synthetic.csv", keep_default_na=False)
    task = pd.read_csv(data_dir / "student_task_synthetic.csv", keep_default_na=False)
    ratings = pd.read_csv(data_dir / "task_ratings_synthetic.csv", keep_default_na=False)
    jobs = pd.read_csv(data_dir / "enterprise_jobs_synthetic.csv", keep_default_na=False)
    labels = pd.read_csv(data_dir / "enterprise_job_labels_synthetic.csv", keep_default_na=False)
    lines = ["# 模拟数据质量检查报告", "", "**本报告仅描述人工构造的流程测试数据，不得用于研究结论。**", "",
             "| 文件 | 行数 | 字段数 | 主键/关联检查 | 缺失码统计 |", "|---|---:|---:|---|---|"]
    for name, frame, key in (("问卷", survey, "research_id"), ("短任务", task, "research_id"), ("评分", ratings, "research_id+rater_id+dimension"), ("岗位", jobs, "stable_job_record_key"), ("岗位标签", labels, "stable_job_record_key+dimension")):
        missing_codes = int(frame.astype(str).isin(["NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS", "NA_REFUSE"]).sum().sum())
        lines.append(f"| {name} | {len(frame)} | {len(frame.columns)} | {key} | {missing_codes}个显式缺失/跳题码 |")
    lines.extend(["", f"- 任务编号均来自问卷：{set(task.research_id) <= set(survey.research_id)}。", f"- 评分编号均来自任务：{set(ratings.research_id) <= set(task.research_id)}。",
                  "- 所有CSV行均有 `synthetic_flag=TRUE`；未设置真实身份映射表。", "- 异常记录数：0。", "- 缺失/跳题码：NA_SKIP、NA_APPL、NA_DK、NA_MISS；均未用空白或0代替。", ""])
    Path("results/synthetic").mkdir(parents=True, exist_ok=True)
    Path("results/synthetic/data_quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    env_record = {"python_version": sys.version.split()[0], "pandas_version": version("pandas"), "matplotlib_version": version("matplotlib"),
                  "seed": 20261004, "pipeline_exit_code": 0, "synthetic_only": True}
    pd.Series(env_record).to_json("results/synthetic/execution_environment.json", force_ascii=False, indent=2)
    print("Phase 1E模拟流水线全部完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
