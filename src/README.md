# 模拟分析代码

所有说明、注释和 docstring 使用中文。主流程为可复现的 `.py` 脚本，不以 Notebook 为唯一实现。

| 脚本 | 输入 | 输出/用途 | 依赖 |
|---|---|---|---|
| `generate_synthetic_data.py` | 固定随机种子 | 写入 `data/synthetic/` 五份模拟CSV | 标准库 |
| `validate_synthetic_data.py` | 五份模拟CSV | 主键、子集、跳题、AI边界和格式扫描 | 标准库 |
| `analyze_student_survey_synthetic.py` | 模拟问卷 | 问卷分项频数比例表 | pandas |
| `analyze_task_synthetic.py` | 模拟任务 | 完成情况、AI使用分层、六维描述 | pandas |
| `analyze_linked_student_task_synthetic.py` | 问卷与任务 | 关联样本、AI使用者过程、子样本选择比较 | pandas |
| `analyze_rater_agreement_synthetic.py` | 双评分数据 | 精确一致率、平均绝对差、维度分歧 | pandas |
| `analyze_enterprise_profile_synthetic.py` | 模拟岗位及标签 | 岗位族、八维画像与交叉描述 | pandas |
| `build_student_enterprise_mapping_synthetic.py` | 模拟企业标签与预设学生证据框架 | DIRECT/PARTIAL/NO_DIRECT_MATCH映射，不计算Gap Score | pandas |
| `plot_synthetic_results.py` | 两张模拟摘要表 | 带“【模拟数据】”标题的简单图 | pandas、matplotlib |
| `run_phase1e_synthetic_pipeline.py` | 全部模拟CSV | 顺序执行全流程并生成质量报告 | pandas、matplotlib |

运行：`python -m src.run_phase1e_synthetic_pipeline`。脚本不连接网络、不运行Stata、不读取Parked项目。
