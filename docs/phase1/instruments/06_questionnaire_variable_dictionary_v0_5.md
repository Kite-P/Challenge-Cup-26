# 问卷变量字典 v0.5（候选）

**状态：**与 `05_questionnaire_v0_5_supervisor_review.md` 对应；未冻结、未批准实施。字段名沿用或映射现有合成流程标识，仅作讨论；实际平台字段须经批准后另行建立。

| 问卷题号 | 暂定字段 | 类型 | 适用路径/特别回答 | 分析用途与边界 |
|---|---|---|---|---|
| Q1 | `recent_research_task` | YES/NO/UNSURE/NA_REFUSE | 无任务时任务专属题目跳过 | 筛选回顾条件，不是入组门槛 |
| Q2 | `research_experience_type` | 单选类别 | Q1=YES | 最近任务类别描述，不等于科研能力 |
| Q3 | `research_experience_depth` | 多选任务阶段 | Q1=YES | 记录实际参与环节，不生成经历总分 |
| Q4 | `major_group` | 单选类别 | 全体可答；允许不确定/拒答 | 样本描述，专业细类范围待确认 |
| Q5 | `year_of_study` | 单选类别 | 全体可答；允许拒答 | 样本描述 |
| Q6 | `method_training` | 多选类别 | 全体可答 | 训练经历描述，不代表训练质量 |
| Q7 | `ai_used` | YES/NO/UNSURE/NO_TOOL/NA_APPL | Q1=YES；非YES路径跳过Q8–Q12、Q14–Q15 | AI使用事实；不得作为协作质量分 |
| Q8 | `ai_stage_*` | 多选阶段标记 | Q7=YES | 使用阶段分项描述 |
| Q9 | `ai_reason_check` | YES/NO/NO_RELEVANT_OUTPUT/NA_DK | Q7=YES | 是否要求理由/依据/条件；行为自报 |
| Q10 | `ai_evidence_check` | CHECK_EXISTENCE/CHECK_SUPPORT/COMPARE_SOURCE/NO_CHECK/NO_RELEVANT_OUTPUT/NA_DK | Q7=YES | 核查方式类别；不等同实际核验表现 |
| Q11 | `ai_output_handling` | ACCEPT/MODIFY/PARTIAL/REFERENCE_ONLY/REJECT/NOT_ENCOUNTERED/NA_DK | Q7=YES | 输出处理方式；采纳/拒绝方向不评分 |
| Q12 | `ai_disagreement_response` | COMPARE_BASIS/ASK_AGAIN/ASK_PERSON/ACCEPT/KEEP_VIEW/NOT_ENCOUNTERED/NA_DK | Q7=YES | 分歧处理描述；不推断稳定决策能力 |
| Q13 | `info_source_check` | SOURCE/DATE/SAMPLE/MEASURE/SUPPORT/CROSS_CHECK/NO_CHECK/NA_DK | Q1可无任务时作一般策略回答 | 自报信息判断优先策略；不是实际表现测验 |
| Q14 | `method_choice_occurred`、`ai_method_compare` | 任务是否有方法选择；AI是否受要求比较 | Q7=YES | 描述方法协作；不评价方法理解总分 |
| Q15 | `unverified_acceptance` | NEVER/SOMETIMES/OFTEN/NO_AI/NO_OUTPUT/NA_DK | Q7=YES | 未核验采纳自报，不作污名化或因果解释 |
| Q16 | `guidance_context` | COURSE/TEACHER/PEER/NONE/NA_DK | Q1=YES | 主要支持来源描述，不估计指导因果效果 |
| Q17（OPTIONAL） | `policy_awareness_optional` | 单选类别 | 可删；课程规则认知 | 当前合成schema未覆盖，非核心变量 |
| Q18 | `a9_first_action`、`a9_reason` | 单选+可选短文本 | 全体可答 | 简短中性情境策略；不是短任务分数 |
| Q19（OPTIONAL） | `open_risk_feedback_optional` | 可空短文本 | 可删；须做隐私和文本编码审阅 | 不默认进入结构化模型 |
| Q20（OPTIONAL） | `info_confidence_optional` | 5点自我感知 | 可删 | `SELF_PERCEPTION`，不能等同能力或与任务评分合并 |

## 统一候选缺失语义

`NA_SKIP`为按逻辑未展示；`NA_APPL`为已展示但情形不适用；`NA_DK`为不知道/记不清；`NA_REFUSE`为明确不愿回答；`NA_MISS`为展示后未答。`NO_AI`、`NO_OUTPUT`、`NO_CHECK`和`NOT_ENCOUNTERED`为题目实质回答，不能合并为零或一般缺失。标签及字段仍须在任何批准后的数据模式中复核。

## 与历史合成schema的关系

Phase 1F 合成数据字段只用于固定流程测试。Q17、Q19为OPTIONAL，Q18理由文本的未来编码也未进入历史固定schema。此字典不表示现有Python生成器已覆盖v0.5，更不授权创建真人数据库；schema更新时应另行版本化并保持旧合成基准可复现。
