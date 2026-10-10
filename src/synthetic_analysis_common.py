"""模拟流程分析脚本共用的CSV读写与汇总函数。"""

from pathlib import Path

import pandas as pd

DATA = Path("data/synthetic")
RESULTS = Path("results/synthetic")


def read(name: str) -> pd.DataFrame:
    """读取项目模拟目录中的CSV。"""
    return pd.read_csv(DATA / name, keep_default_na=False)


def write(frame: pd.DataFrame, name: str) -> None:
    """写出并显式附加模拟数据标记。"""
    RESULTS.mkdir(parents=True, exist_ok=True)
    if "synthetic_flag" not in frame.columns:
        frame.insert(0, "synthetic_flag", "TRUE")
    else:
        frame["synthetic_flag"] = frame["synthetic_flag"].map({True: "TRUE", False: "FALSE", "True": "TRUE", "False": "FALSE", "TRUE": "TRUE", "FALSE": "FALSE"})
    frame.to_csv(RESULTS / name, index=False, encoding="utf-8-sig")


def count_table(frame: pd.DataFrame, column: str, output_name: str, label: str | None = None) -> pd.DataFrame:
    """生成带模拟标记的频数和比例表。"""
    result = frame[column].value_counts(dropna=False).rename_axis(label or column).reset_index(name="count")
    result["proportion"] = result["count"] / max(len(frame), 1)
    write(result, output_name)
    return result


def multi_select_count_table(frame: pd.DataFrame, column: str, output_name: str, label: str | None = None) -> pd.DataFrame:
    """将竖线分隔的模拟多选按选项展开，比例分母为全部回答记录数。"""
    choices = frame[column].fillna("").astype(str).str.split("|").explode()
    choices = choices[~choices.isin({"", "NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS", "NA_REFUSE"})]
    result = choices.value_counts().rename_axis(label or column).reset_index(name="count")
    result["proportion_respondents"] = result["count"] / max(len(frame), 1)
    write(result, output_name)
    return result
