"""输出双评分者流程的一致率、平均绝对差及分维度分歧。"""

import pandas as pd

from src.synthetic_analysis_common import read, write


def main() -> int:
    ratings = read("task_ratings_synthetic.csv")
    wide = ratings.pivot(index=["research_id", "dimension"], columns="rater_id", values="score").reset_index()
    wide["exact_agreement"] = wide.R1 == wide.R2
    wide["absolute_difference"] = (wide.R1 - wide.R2).abs()
    summary = wide.groupby("dimension").agg(exact_agreement_rate=("exact_agreement", "mean"), mean_absolute_difference=("absolute_difference", "mean"), disagreement_count=("exact_agreement", lambda value: int((~value).sum()))).reset_index()
    write(summary, "task_rater_agreement_by_dimension.csv")
    write(pd.DataFrame([{"metric": "exact_agreement_rate", "value": wide.exact_agreement.mean()}, {"metric": "mean_absolute_difference", "value": wide.absolute_difference.mean()}]), "task_rater_agreement_summary.csv")
    print("评分者流程指标：精确一致率、平均绝对差、分维度分歧数；未计算加权Kappa。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
