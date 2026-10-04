"""输出模拟岗位族和八个候选能力维度的描述。"""

import pandas as pd

from src.synthetic_analysis_common import read, write


def main() -> int:
    jobs = read("enterprise_jobs_synthetic.csv")
    labels = read("enterprise_job_labels_synthetic.csv")
    family = jobs.groupby("job_family").size().reset_index(name="count")
    write(family, "enterprise_job_family_distribution.csv")
    incidence = labels.groupby("dimension").label.mean().reset_index(name="simulated_incidence")
    write(incidence, "enterprise_ability_incidence.csv")
    matrix = labels.merge(jobs[["stable_job_record_key", "job_family", "year"]], on="stable_job_record_key", validate="many_to_one")
    write(matrix.groupby(["job_family", "dimension"]).label.mean().reset_index(name="simulated_incidence"), "enterprise_family_dimension_matrix.csv")
    write(matrix.groupby(["year", "dimension"]).label.mean().reset_index(name="simulated_incidence"), "enterprise_year_dimension.csv")
    print("企业端仅生成模拟结构画像，不代表真实企业需求。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
