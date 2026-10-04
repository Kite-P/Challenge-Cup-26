"""可选生成带有醒目标记的简单模拟图。"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.synthetic_analysis_common import RESULTS


def main() -> int:
    plt.rcParams["font.family"] = "Microsoft YaHei"
    target = RESULTS / "figures"
    target.mkdir(parents=True, exist_ok=True)
    for filename, category, title in (("survey_ai_use.csv", "ai_used", "AI使用事实分布"), ("enterprise_job_family_distribution.csv", "job_family", "模拟岗位族分布")):
        data = pd.read_csv(RESULTS / filename)
        ax = data.plot.bar(x=category, y="count", legend=False)
        ax.set_title(f"【模拟数据】{title}")
        ax.set_xlabel(category)
        ax.set_ylabel("模拟记录数")
        plt.tight_layout()
        plt.savefig(target / f"{filename.removesuffix('.csv')}.png", dpi=140)
        plt.close()
    print("已生成2张标题明确标注模拟数据的图。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
