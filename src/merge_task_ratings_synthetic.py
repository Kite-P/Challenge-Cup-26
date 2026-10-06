"""合并两名评分员分别填写的虚构评分表。"""

from __future__ import annotations

import csv
from typing import Iterable
from pathlib import Path


DIMENSIONS = {
    "problem_definition",
    "information_evaluation",
    "method_fit",
    "limitation_boundary",
    "independent_decision",
    "reasoning_quality",
}

TASK_DIMENSION_COLUMNS = {
    "problem_definition",
    "information_evaluation",
    "method_fit",
    "limitation_boundary",
    "independent_decision",
    "reasoning_quality",
}


def merge_task_ratings(
    r1_rows: Iterable[dict[str, str]],
    r2_rows: Iterable[dict[str, str]],
    scorable_keys: set[tuple[str, str]],
) -> list[dict[str, int | str | None]]:
    """按 participant-dimension 对齐评分，保留单边缺评状态。"""
    r1 = _index_rows(r1_rows, "R1", scorable_keys)
    r2 = _index_rows(r2_rows, "R2", scorable_keys)
    output = []
    for research_id, dimension in sorted(set(r1) | set(r2)):
        score1 = r1.get((research_id, dimension))
        score2 = r2.get((research_id, dimension))
        status = "BOTH_RATED" if score1 is not None and score2 is not None else ("R1_MISSING" if score1 is None else "R2_MISSING")
        output.append(
            {
                "research_id": research_id,
                "dimension": dimension,
                "r1_score": score1,
                "r2_score": score2,
                "agreement_status": status,
                "synthetic_flag": "TRUE",
            }
        )
    return output


def merge_rating_csv_files(
    r1_path: str | Path,
    r2_path: str | Path,
    task_path: str | Path,
    output_path: str | Path,
) -> int:
    """依据合成任务可评分状态合并 R1/R2 CSV 并写出一致性状态表。"""
    r1_rows = _read_csv(r1_path)
    r2_rows = _read_csv(r2_path)
    task_rows = _read_csv(task_path)
    if not task_rows:
        raise ValueError("任务表为空，无法判定可评分维度")
    if not TASK_DIMENSION_COLUMNS <= set(task_rows[0]):
        raise ValueError("任务表缺少评分维度列")
    scorable = {
        (row["research_id"], dimension)
        for row in task_rows
        for dimension in TASK_DIMENSION_COLUMNS
        if row.get(dimension) != "NOT_SCORABLE"
    }
    merged = merge_task_ratings(r1_rows, r2_rows, scorable)
    if not merged:
        raise ValueError("评分表没有可合并记录")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(merged[0]))
        writer.writeheader()
        writer.writerows(merged)
    return len(merged)


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _index_rows(
    rows: Iterable[dict[str, str]],
    rater: str,
    scorable_keys: set[tuple[str, str]],
) -> dict[tuple[str, str], int]:
    indexed: dict[tuple[str, str], int] = {}
    for row in rows:
        research_id = str(row.get("research_id", "")).strip()
        dimension = str(row.get("dimension", "")).strip()
        key = (research_id, dimension)
        if not research_id or dimension not in DIMENSIONS:
            raise ValueError(f"{rater}存在无效研究编号或维度：{key}")
        if key in indexed:
            raise ValueError(f"{rater}重复评分：{key}")
        if key not in scorable_keys:
            raise ValueError(f"不可评分维度被评分：{key}")
        try:
            score = int(row.get("score", ""))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{rater}存在非法分值：{row.get('score')!r}") from exc
        if str(score) != str(row.get("score", "")).strip() or score not in {0, 1, 2}:
            raise ValueError(f"{rater}存在非法分值：{row.get('score')!r}")
        indexed[key] = score
    return indexed
