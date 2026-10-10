# 问卷 v0.6 变量字典（候选）

| 题目 | 候选字段 | 类型/编码 | 展示边界 | 描述用途与限制 |
|---|---|---|---|---|
| Q1 | `recent_research_task` | 单选：YES/NO/UNSURE/NA_REFUSE | 全体 | 回忆路由；是否入组门槛待导师确认，未确认前不作为筛除依据或固定分层变量 |
| Q2–Q3 | `recent_task_type`,`task_participation_stages` | 单选/多选 | Q1=是 | 最近任务背景与参与环节，不以选项数评价能力；竞赛类别不指定赛事 |
| Q4–Q6 | `major_group`,`year_of_study`,`method_training` | 分类/去重多选 | 全体 | 人群描述；Q6“尚未接触过”及缺失状态互斥；专业映射待按当期目录和导师决定确认 |
| Q7–Q9 | `ai_used`,`ai_stage_*`,`ai_reason_check` | 分类/多选 | Q1=是；AI细项Q7=使用过 | AI参与环节与理由询问自报；Q8现有字段不能区分全部六类，见正文映射边界；不等同于质量或能力 |
| Q10 | `ai_evidence_checked` | YES/NO/NO_RELEVANT_OUTPUT/NA_DK/NA_REFUSE/NA_MISS | Q1=是且Q7=使用过 | 六种状态分开；漏答不能推成未核查 |
| Q10a | `ai_evidence_objects` | 去重多选；NA_DK/NA_REFUSE/NA_MISS/NA_SKIP | Q10=核查过时展示 | 核查对象：存在性、支持力、时间、对象/口径、定义/计算、交叉来源、其他；非“是”路径结构跳过 |
| Q10b | `ai_evidence_methods` | 去重多选；NA_DK/NA_REFUSE/NA_MISS/NA_SKIP | Q10=核查过时展示 | 核查方式：原始来源、独立检索、对照、重算、咨询、其他；与对象字段分离 |
| Q11–Q12 | `ai_output_handling`,`ai_disagreement_response` | 分类 | Q7=使用过 | 处理及分歧自报，不推断行为因果 |
| Q13 | `info_source_check_actions` | 去重多选；`NO_SPECIAL_CHECK`/`NO_RELATED_EXPERIENCE`/`NA_DK`/`NA_REFUSE`/`NA_MISS`各自互斥 | 全体 | “通常没有特别核查”与“没有相关经历”语义不同；不限定最近任务 |
| Q14 | `method_choice_occurred`,`method_decision_actions`,`ai_method_compare` | 单选/去重多选/单选 | 本人任务项Q1=是；AI比较按Q7=使用过展示，不以方法选择为条件 | 本人选择、实际决策行为及AI比较分开；`NO_METHOD_CHOICE`不作为答案码 |
| Q15 | `unverified_acceptance` | 有序分类 | Q7=使用过 | 回顾性自报，不是客观核验记录 |
| Q16 | `training_need` | 最多选3项 | 全体 | 培养需求直接测量；尚无真实分布 |
| Q17/Q19/Q20 | `policy_awareness`,`open_concern`,`info_confidence_optional` | 可选分类/文本/序数 | 全体 | OPTIONAL；模拟字段均保留；开放回答仅为明确标记的模拟文本；不得冒充量表或客观能力 |
| Q18 | `a9_first_action`,`a9_reason` | 情境选择/可选文本 | 全体 | 固定情境下策略，不是实际行为或知识考试成绩 |

缺失码：`NA_SKIP`未展示；`NA_APPL`展示但不适用；`NA_DK`不知道/记不清；`NA_REFUSE`拒答；`NA_MISS`漏答。多选以去重的类别集合保存，互斥选项不能与实质类别并存。Q8的六类选项映射：问题界定→`ai_stage_problem`；关键词/资料线索与资料整理/解释合并映射→`ai_stage_information`；方法比较→`ai_stage_method`；数据分析/检查计算及报告组织/表达没有独立字段；`ai_stage_limitation`没有Q8选项直接对应，不可据此声称六类已全部单独实现。平台中立导入原型目前只处理Q1/Q2/Q3/Q7。模拟Schema仅供软件验证，不表示正式数据结构已冻结。
