"""输出双评分者流程的一致率、平均绝对差及分维度分歧。"""

import pandas as pd

from src.rater_reliability import weighted_cohen_kappa
from src.synthetic_analysis_common import read, write


def main() -> int:
    ratings = read("task_ratings_synthetic.csv")
    ratings["score"] = ratings["score"].astype("int64")
    wide = ratings.pivot(index=["research_id", "dimension"], columns="rater_id", values="score").reset_index()
    wide = wide.dropna(subset=["R1", "R2"])
    wide["exact_agreement"] = wide.R1 == wide.R2
    wide["absolute_difference"] = (wide.R1 - wide.R2).abs()
    summary = wide.groupby("dimension").agg(exact_agreement_rate=("exact_agreement", "mean"), mean_absolute_difference=("absolute_difference", "mean"), disagreement_count=("exact_agreement", lambda value: int((~value).sum()))).reset_index()
    kappa_rows = []
    for dimension, frame in wide.groupby("dimension"):
        result = weighted_cohen_kappa(frame["R1"].tolist(), frame["R2"].tolist(), weighting="quadratic")
        kappa_rows.append({
            "dimension": dimension,
            "weighted_kappa_quadratic": result["kappa"],
            "weighted_kappa_n_pairs": result["n_pairs"],
            "weighted_kappa_undefined_reason": result["undefined_reason"],
        })
    summary = summary.merge(pd.DataFrame(kappa_rows), on="dimension", how="left")
    write(summary, "task_rater_agreement_by_dimension.csv")
    write(pd.DataFrame([{"metric": "exact_agreement_rate", "value": wide.exact_agreement.mean()}, {"metric": "mean_absolute_difference", "value": wide.absolute_difference.mean()}]), "task_rater_agreement_summary.csv")
    print("评分者模拟流程指标：精确一致率、平均绝对差、分维度分歧数和二次加权Cohen's kappa；不得视为真人评分信度。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
