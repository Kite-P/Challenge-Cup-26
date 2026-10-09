# Phase 1H.1 合成流程代码

所有说明、注释和 docstring 使用中文。主流程为可复现的 `.py` 脚本，不以 Notebook 为唯一实现。

| 脚本 | 输入 | 输出/用途 | 依赖 |
|---|---|---|---|
| `generate_synthetic_data.py` | 固定随机种子 | 写入 `data/synthetic/` 五份模拟CSV | 标准库 |
| `validate_synthetic_data.py` | 五份模拟CSV | 主键、子集、跳题、AI边界和格式扫描 | 标准库 |
| `analyze_student_survey_synthetic.py` | 模拟问卷 | 问卷分项频数比例表 | pandas |
| `analyze_task_synthetic.py` | 模拟任务 | 完成情况、AI使用分层、五维描述 | pandas |
| `analyze_linked_student_task_synthetic.py` | 问卷与任务 | 关联样本、AI使用者过程、子样本选择比较 | pandas |
| `analyze_rater_agreement_synthetic.py` | 双评分数据 | 精确一致率、平均绝对差、维度分歧 | pandas |
| `analyze_enterprise_profile_synthetic.py` | 模拟岗位及标签 | 岗位族、八维画像与交叉描述 | pandas |
| `build_student_enterprise_mapping_synthetic.py` | 模拟企业标签与预设学生证据框架 | DIRECT/PARTIAL/NO_DIRECT_MATCH映射，不计算Gap Score | pandas |
| `plot_synthetic_results.py` | 两张模拟摘要表 | 带“【模拟数据】”标题的简单图 | pandas、matplotlib |
| `run_phase1e_synthetic_pipeline.py` | 全部模拟CSV | 顺序执行全流程并生成质量报告 | pandas、matplotlib |
| `rater_reliability.py` | 两名评分者的有序类别 | 加权 Cohen's kappa（线性/二次权重）与不可估状态 | 标准库 |
| `transform_survey_export_synthetic.py` | `data/synthetic/raw_like/` 中的平台中立虚构导出 | 列/选项/重复 ID 校验后映射到最小 canonical 字段 | 标准库 |
| `merge_task_ratings_synthetic.py` | R1、R2 分表及合成任务可评分字段 | 合并原评分，标记双评与单边漏评；拒绝重复/非法/不可评分维度 | 标准库 |
| `check_project_consistency.py` | 显式活跃文档与 Git 跟踪清单 | 扫描旧术语、危险状态、过期日期、绝对路径和误跟踪原始/二进制文件 | 标准库/Git CLI |
| `run_repo_checks.py` | 仓库工作区 | 依序执行一致性扫描、unittest、合成数据校验；可选 `--pipeline` 跑完整合成流水线 | 标准库，测试/流水线依赖使用现有环境 |

运行：`python -m src.run_phase1e_synthetic_pipeline`。脚本不连接网络、不运行Stata、不读取Parked项目。

Phase 1G 导入原型的输入均为 `PLATFORM_NEUTRAL_MOCK` 合成样例，无真人、企业或平台数据。规则扫描器不是通用合规证明；扫描清单/历史 allowlist 需随研究设计演进人工审阅。加权 kappa 输出仅为方法代码验证，非真实评分信度。

仓库核心检查命令：`python -m src.run_repo_checks`；需要连带运行完整 Phase 1E 合成流水线时使用 `python -m src.run_repo_checks --pipeline`。本轮执行时请将 `python` 替换为项目已验证解释器，不安装新依赖。
