"""计算0/1/2有序评分的加权Cohen's kappa。"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence


MISSING_RATINGS = {None, "", "NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS", "NA_REFUSE", "NOT_SCORABLE"}


def weighted_cohen_kappa(
    rater1: Sequence[object],
    rater2: Sequence[object],
    *,
    weighting: str = "quadratic",
    categories: tuple[int, ...] = (0, 1, 2),
) -> dict[str, float | int | str | None]:
    """返回双评完整配对的线性或二次加权 Cohen's kappa。

    只有R1/R2均有合法序数分值的维度进入计算。缺失与NOT_SCORABLE不作0分。
    当不存在配对评分或机会校正分母为零时，kappa返回None并说明原因。
    """
    if len(rater1) != len(rater2):
        raise ValueError("两位评分员的记录长度必须一致")
    if weighting not in {"linear", "quadratic"}:
        raise ValueError("weighting必须为'linear'或'quadratic'")
    if len(categories) < 2 or len(set(categories)) != len(categories):
        raise ValueError("categories必须包含至少两个不重复的评分类别")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in categories):
        raise ValueError("categories必须是整数类别")

    valid_categories = set(categories)
    paired: list[tuple[int, int]] = []
    for left, right in zip(rater1, rater2, strict=True):
        left_missing = _is_missing(left)
        right_missing = _is_missing(right)
        if left_missing or right_missing:
            continue
        if isinstance(left, bool) or isinstance(right, bool):
            raise ValueError("评分值不能为布尔值")
        if not isinstance(left, int) or not isinstance(right, int):
            raise ValueError("非缺失评分必须为整数类别")
        if left not in valid_categories or right not in valid_categories:
            raise ValueError("评分值不在声明的类别范围内")
        paired.append((left, right))

    if not paired:
        return {"kappa": None, "n_pairs": 0, "undefined_reason": "NO_PAIRED_RATINGS", "weighting": weighting}

    span = max(categories) - min(categories)
    observed_agreement = 0.0
    for left, right in paired:
        distance = abs(left - right) / span
        penalty = distance if weighting == "linear" else distance**2
        observed_agreement += 1.0 - penalty
    observed_agreement /= len(paired)

    left_counts = Counter(left for left, _ in paired)
    right_counts = Counter(right for _, right in paired)
    expected_agreement = 0.0
    n_pairs = len(paired)
    for left in categories:
        for right in categories:
            distance = abs(left - right) / span
            penalty = distance if weighting == "linear" else distance**2
            weight = 1.0 - penalty
            expected_agreement += (left_counts[left] / n_pairs) * (right_counts[right] / n_pairs) * weight

    denominator = 1.0 - expected_agreement
    if math.isclose(denominator, 0.0, abs_tol=1e-12):
        return {
            "kappa": None,
            "n_pairs": n_pairs,
            "undefined_reason": "NO_EXPECTED_DISAGREEMENT",
            "weighting": weighting,
        }

    kappa = (observed_agreement - expected_agreement) / denominator
    return {"kappa": kappa, "n_pairs": n_pairs, "undefined_reason": None, "weighting": weighting}


def _is_missing(value: object) -> bool:
    if value in MISSING_RATINGS:
        return True
    return isinstance(value, float) and math.isnan(value)
