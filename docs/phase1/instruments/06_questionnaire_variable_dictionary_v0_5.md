# 问卷变量字典 v0.5（候选）

**状态：**与完整问卷和唯一权威跳题表同步；未冻结、未批准实施。此字典定义分析变量及当前模拟字段；平台正式字段仍须在审批后复核。

| 题号 | 分析变量 | 当前模拟字段 | 适用路径/回答编码 | 分析用途与边界 |
|---|---|---|---|---|
| Q1 | 最近12个月是否有研究型任务 | `recent_research_task` | YES/NO/UNSURE/NA_REFUSE | 回顾筛选，不是入组门槛；Q1非YES时相关任务题为`NA_SKIP` |
| Q2 | 最近任务类型 | `recent_task_type` | Q1=YES；类型类别/NA_DK/NA_REFUSE | 近期任务描述，不等同科研能力或经历等级 |
| Q3 | 最近任务实际参与环节 | `task_participation_stages` | Q1=YES；多选编码以`|`连接/NA_DK/NA_REFUSE | 记录实际参与环节，不生成经历总分；两种特别回答与多选互斥 |
| Q4 | 专业大类 | `major_group` | 全体；不确定与拒答分开 | 样本描述；具体专业范围仍待确认 |
| Q5 | 本科年级 | `year_of_study` | 全体；允许拒答 | 样本描述 |
| Q6 | 研究方法、资料评价或数据分析训练 | `method_training` | 全体；尚未接触/记不清/拒答互斥 | 背景描述，不代表训练质量 |
| Q7 | 最近任务中的生成式AI使用 | `ai_used` | Q1=YES；YES/NO/UNSURE/NO_TOOL/NA_APPL/NA_REFUSE；否则NA_SKIP | 事实自报，不作协作质量分；NA_APPL指任务存在但无AI可参与环节 |
| Q8 | AI使用阶段 | `ai_stage_problem`、`ai_stage_information`、`ai_stage_method`、`ai_stage_limitation` | Q7=YES；多选/记不清/拒答；否则NA_SKIP | 分项描述使用环节，不形成频率总分 |
| Q9 | 是否追问AI理由/依据/条件 | `ai_reason_check` | Q7=YES；YES/NO/NO_RELEVANT_OUTPUT/NA_DK/NA_REFUSE | 行为自报，不等同实际核验表现 |
| Q10 | AI输出核查方式 | `ai_evidence_check` | Q7=YES；核查类别/NO_CHECK/NO_RELEVANT_OUTPUT/NA_DK/NA_REFUSE | 分类描述，不评为个人能力 |
| Q11 | AI输出处理方式 | `ai_output_handling` | Q7=YES；处理类别/NOT_ENCOUNTERED/NA_DK/NA_REFUSE | 采纳、修改、部分使用、拒绝均不预设好坏 |
| Q12 | AI建议与原判断冲突时的处理 | `ai_disagreement_response` | Q7=YES；处理类别/NOT_ENCOUNTERED/NA_DK/NA_REFUSE | 行为自报，不推断稳定决策能力 |
| Q13 | 一般资料判断优先策略 | `info_source_check` | 全体；含无相关经历/NA_DK/NA_REFUSE | 不限定最近任务；仅作自报描述，不是表现测验 |
| Q14 | 最近任务是否涉及方法选择及AI方法比较 | `method_choice_occurred`、`ai_method_compare` | Q1=YES且Q7=YES；否则NA_SKIP | 任务方法协作描述；不作为方法理解分数 |
| Q15 | 未核验采纳AI输出自报 | `unverified_acceptance` | Q1=YES且Q7=YES；否则NA_SKIP | 单项行为描述，不作污名化或因果解释 |
| Q16 | 最近任务中主要支持来源 | `guidance_context` | Q1=YES；否则NA_SKIP；可回答无支持/不确定/拒答 | 支持情境描述，不估计指导因果效果 |
| Q17（OPTIONAL） | 课程/项目AI规则认知 | 候选字段`policy_awareness_optional`；当前模拟schema未实现 | 全体可答；如保留 | `NEEDS_LATER_IMPLEMENTATION`；不阻断静态工具审阅 |
| Q18 | 中性情境中的先行策略与可选理由 | `a9_first_action`、`a9_reason` | 全体；单题策略、不评分；可选择不确定/拒答 | 多种策略可合理，不设唯一正确答案，不与短任务分数合并 |
| Q19（OPTIONAL） | 对AI使用风险的一般看法 | 候选字段`open_risk_feedback_optional`；当前模拟schema未实现 | 全体，不要求实际使用经历 | `NEEDS_LATER_IMPLEMENTATION`；自由文本编码须另行审核，不默认进模型 |
| Q20（OPTIONAL） | 信息判断自我感知 | `info_confidence_optional` | 全体；不确定与拒答分开 | `SELF_PERCEPTION`；不得视为实际能力或与任务评分合并 |

## 当前模拟字段与范围

固定种子模拟流程覆盖 Q1–Q16、Q18、Q20 中的最小字段；Q17、Q19是可删OPTIONAL字段，当前没有模拟字段，标记为 `NEEDS_LATER_IMPLEMENTATION`。Q2/Q3现映射为 `recent_task_type` 和 `task_participation_stages`，Q16受Q1控制；不得再把Q2/Q3误映射为泛化科研经历或经历深度。模拟数据只供软件流程测试，全部标为 `SYNTHETIC ONLY`。

## 缺失语义

`NA_SKIP`=未展示；`NA_APPL`=已展示但不适用；`NA_DK`=展示且不知道/记不清；`NA_REFUSE`=展示且明确拒答；`NA_MISS`=展示且漏答。实质选项（如`NO_TOOL`、`NO_RELEVANT_OUTPUT`、`NOT_ENCOUNTERED`）不得被替换为缺失码或0。详见 [`08_questionnaire_skip_tree_v0_5_candidate.md`](08_questionnaire_skip_tree_v0_5_candidate.md)。
