"""顺序运行模拟生成、严格校验、分项分析和动态质量报告。"""

from __future__ import annotations

import subprocess
import sys
import json
from importlib.metadata import version
from pathlib import Path

import pandas as pd

from src.generate_synthetic_data import SYNTHETIC_VERSION, build_synthetic_bundle, write_bundle
from src.validate_synthetic_data import load_bundle, quality_summary, validate_bundle, validate_files


def _validate_schema_files(directory: Path = Path("schemas")) -> tuple[int, list[str]]:
    """检查 JSON schema 可解析、required 字段存在且具备模拟边界说明。"""
    paths = sorted(directory.glob("*.json"))
    errors = []
    for path in paths:
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"schema不可解析：{path.name}: {exc}")
            continue
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if not properties or not set(required) <= set(properties):
            errors.append(f"schema字段定义不完整：{path.name}")
        if any("description_zh" not in item or "synthetic_only" not in item for item in properties.values()):
            errors.append(f"schema字段缺少中文说明或synthetic_only：{path.name}")
    if not paths:
        errors.append("schema目录没有JSON schema")
    return len(paths), errors


def _write_quality_report(bundle: dict, errors: list[str]) -> None:
    """依据实际模拟记录和校验函数输出质量摘要。"""
    metrics = quality_summary(bundle)
    schema_count, schema_errors = _validate_schema_files()
    frames = {
        "问卷": pd.DataFrame(bundle["survey"]), "短任务": pd.DataFrame(bundle["task"]),
        "评分": pd.DataFrame(bundle["ratings"]), "岗位": pd.DataFrame(bundle["jobs"]),
        "岗位标签": pd.DataFrame(bundle["labels"]),
    }
    lines = ["# Phase 1H.1 五维模拟数据质量检查报告", "", "**本报告只反映流程模拟数据，不得用于研究结论。**", "",
             "## 文件结构", "", "| 文件 | 行数 | 字段数 |", "|---|---:|---:|"]
    lines.extend(f"| {name} | {len(frame)} | {len(frame.columns)} |" for name, frame in frames.items())
    lines.extend(["", "## 跳题与任务可评分状态", "",
                  f"- 严格跳题违规数：{metrics['strict_skip_violations']}",
                  f"- AI未使用者过程字段违规数：{metrics['ai_nonuser_field_violations']}",
                  f"- COMPLETE：{metrics['complete_count']}", f"- PARTIAL：{metrics['partial_count']}",
                  f"- ABORTED：{metrics['aborted_count']}", f"- 完整五维分析可用记录：{metrics['analysis_eligible_count']}",
                  f"- 不可评分维度数：{metrics['unscorable_dimension_count']}", f"- 实际评分长表记录数：{metrics['rating_row_count']}",
                  f"- 任务评分范围异常数：{metrics['score_range_anomalies']}", "",
                  "## 关联与主键", "", f"- 问卷research_id重复数：{metrics['duplicate_research_id_count']}",
                  f"- 岗位stable_job_record_key重复数：{metrics['duplicate_job_key_count']}",
                  f"- 非问卷子集任务记录数：{metrics['task_not_survey_count']}",
                  f"- 非任务子集评分记录数：{metrics['rating_not_task_count']}", "",
                  f"- 实际异常计数：{metrics['anomaly_count']}", f"- Validator错误条数：{len(errors)}",
                  f"- JSON schema 数量：{schema_count}",
                  f"- schema 一致性：{'PASS' if not schema_errors else 'FAIL'}",
                  f"- 校验版本：`{SYNTHETIC_VERSION}`（合成流程版本，不是研究版本）",
                  "- 验证信息：" + ("无异常。" if not errors else "；".join(errors)),
                  "- schema问题：" + ("无。" if not schema_errors else "；".join(schema_errors)),
                  "- 任务表现均值仅使用 `COMPLETE` 且 `analysis_eligible=TRUE` 的记录。",
                  "- `PARTIAL`未进入默认完整五维均值；`ABORTED`未评分、未进入均值，最终方案归属记为`NOT_REACHED`。",
                  "- 0分表示存在可评作答但未呈现该行为；`NOT_SCORABLE`表示没有足够作答，两者不互换。",
                  "- 所有模拟CSV均检查 `synthetic_flag=TRUE`；不设置真实身份映射。", ""])
    output = Path("results/synthetic")
    output.mkdir(parents=True, exist_ok=True)
    (output / "data_quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    env = {"python_version": sys.version.split()[0], "pandas_version": version("pandas"),
           "matplotlib_version": version("matplotlib"), "seed": 20261004,
           "synthetic_version": SYNTHETIC_VERSION, "pipeline_exit_code": 0 if not errors else 1,
           "synthetic_only": True}
    pd.Series(env).to_json(output / "execution_environment.json", force_ascii=False, indent=2)


def main() -> int:
    """运行固定顺序的Phase 1F模拟链，任一分析失败均返回非零。"""
    write_bundle(build_synthetic_bundle(), Path("data/synthetic"))
    errors = validate_files()
    _, schema_errors = _validate_schema_files()
    errors.extend(schema_errors)
    bundle = load_bundle()
    if errors:
        _write_quality_report(bundle, errors)
        print("校验失败：" + "；".join(errors))
        return 1
    modules = ["src.analyze_student_survey_synthetic", "src.analyze_task_synthetic", "src.analyze_linked_student_task_synthetic",
               "src.analyze_rater_agreement_synthetic", "src.analyze_enterprise_profile_synthetic", "src.build_student_enterprise_mapping_synthetic"]
    for module in modules:
        result = subprocess.run([sys.executable, "-m", module], check=False)
        if result.returncode:
            errors.append(f"{module}退出码{result.returncode}")
            _write_quality_report(bundle, errors)
            print(errors[-1])
            return result.returncode
    result = subprocess.run([sys.executable, "-m", "src.plot_synthetic_results"], check=False)
    if result.returncode:
        errors.append(f"模拟绘图退出码{result.returncode}")
        _write_quality_report(bundle, errors)
        return result.returncode
    errors = validate_files()
    _write_quality_report(bundle, errors)
    if errors:
        print("流水线末尾校验失败：" + "；".join(errors))
        return 1
    print("Phase 1H.1五维合成流水线完成；质量报告指标均由实际记录计算。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
