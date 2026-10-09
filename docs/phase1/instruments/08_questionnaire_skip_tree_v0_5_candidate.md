# 问卷 v0.5 正式候选跳题逻辑表

**状态：**`SUPERVISOR_REVIEW_CANDIDATE`、`NOT PILOTED`、`NOT APPROVED FOR DISTRIBUTION`。本表是 v0.5 唯一权威逐题路径；平台尚未建立，任何实现都须在导师及适用机构批准后复核。字段名为候选映射，不构成真人数据模式。

| 题号 | 展示条件 | 跳过条件 | 不适用条件 | 允许不知道 | 允许拒答 | 系统缺失编码 | 对应候选分析变量/字段 |
|---|---|---|---|---|---|---|---|
| Q1 | 所有符合总体范围的应答者 | 无 | 无 | 是，`UNSURE` | 是 | 展示未答 `NA_MISS` | `recent_research_task`；任务回顾筛选，不是入组门槛 |
| Q2 | Q1=YES | Q1非YES | 无 | 是，`NA_DK` | 是，`NA_REFUSE` | 未展示 `NA_SKIP` | `recent_task_type`；描述最近任务类型 |
| Q3 | Q1=YES | Q1非YES | 无 | 是，`NA_DK` | 是，`NA_REFUSE`；与多选项互斥 | 未展示 `NA_SKIP` | `task_participation_stages`；多选类别，不生成经历分 |
| Q4 | 所有人 | 无 | 无 | 是，单列“不确定” | 是，单列“不愿回答” | 展示未答 `NA_MISS` | `major_group`；专业大类描述 |
| Q5 | 所有人 | 无 | 无 | 不单列 | 是 | 展示未答 `NA_MISS` | `year_of_study`；年级描述 |
| Q6 | 所有人 | 无 | “尚未接触过”是实质选项，且与其他多选互斥 | 是，单列“记不清” | 是，单列“不愿回答”；均与多选项互斥 | 展示未答 `NA_MISS` | `method_training`；训练经历描述 |
| Q7 | Q1=YES | Q1非YES | 可选“该任务没有涉及生成式AI可参与的环节” | 是，记不清/不确定 | 是，明确“不愿回答” | 未展示 `NA_SKIP` | `ai_used`；区分YES/NO/UNSURE/NO_TOOL/NA_APPL/NA_REFUSE |
| Q8 | Q1=YES 且 Q7=YES | Q1非YES或Q7非YES | 题内“其他”可补充，但不得输入敏感信息 | 是，单列“记不清” | 是，单列“不愿回答”；与多选互斥 | 未展示 `NA_SKIP` | `ai_stage_*`；使用阶段分项 |
| Q9 | Q1=YES 且 Q7=YES | Q1非YES或Q7非YES | “任务中没有相关输出”为实质选项 | 是 | 是 | 未展示 `NA_SKIP` | `ai_reason_check`；追问理由/依据/条件 |
| Q10 | Q1=YES 且 Q7=YES | Q1非YES或Q7非YES | “没有相关输出”为实质选项 | 是 | 是 | 未展示 `NA_SKIP` | `ai_evidence_check`；核查方式自报 |
| Q11 | Q1=YES 且 Q7=YES | Q1非YES或Q7非YES | “没遇到可采用的建议/文字”为实质选项 | 是 | 是 | 未展示 `NA_SKIP` | `ai_output_handling`；输出处理自报 |
| Q12 | Q1=YES 且 Q7=YES | Q1非YES或Q7非YES | “没有遇到这种情况”为实质选项 | 是 | 是 | 未展示 `NA_SKIP` | `ai_disagreement_response`；分歧处理自报 |
| Q13 | 所有人 | 无 | “没有相关经历”是实质选项 | 是 | 是 | 展示未答 `NA_MISS` | `info_source_check`；一般资料判断策略自报，不是能力测验 |
| Q14 | Q1=YES 且 Q7=YES | Q1非YES或Q7非YES | “任务没有涉及方法选择”为实质选项 | 是 | 是 | 未展示 `NA_SKIP` | `method_choice_occurred`、`ai_method_compare`；仅描述AI方法比较行为 |
| Q15 | Q1=YES 且 Q7=YES | Q1非YES或Q7非YES | “没有遇到相关输出”为实质选项 | 是 | 是 | 未展示 `NA_SKIP` | `unverified_acceptance`；单项行为自报，不作污名化解释 |
| Q16 | Q1=YES | Q1非YES | Q1=YES但无可辨支持时可选“没有获得上述支持” | 是，记不清/不确定 | 是 | 未展示 `NA_SKIP` | `guidance_context`；最近任务支持情境 |
| Q17（OPTIONAL） | 所有人（保留时） | 若导师删题则不纳入问卷 | “没听说规则”为实质回答 | 是 | 是 | 未展示/删题 `NA_SKIP`；展示未答 `NA_MISS` | `policy_awareness_optional`；尚未进入模拟 schema，`NEEDS_LATER_IMPLEMENTATION` |
| Q18 | 所有人 | 无 | “暂不确定”为实质回答；选项不构成唯一正确答案 | 是 | 是 | 展示未答 `NA_MISS` | `a9_first_action`、`a9_reason`；中性情境策略，不与任务分数合并 |
| Q19（OPTIONAL） | 所有人（保留时） | 若导师删题则不纳入问卷 | “无相关看法/不确定”为允许回答 | 是 | 是 | 未展示/删题 `NA_SKIP`；展示后漏答 `NA_MISS` | `open_risk_feedback_optional`；尚未进入模拟 schema，`NEEDS_LATER_IMPLEMENTATION` |
| Q20（OPTIONAL） | 所有人（保留时） | 若导师删题则不纳入问卷 | 无 | 是，与拒答分开 | 是，与不知道分开 | 未展示/删题 `NA_SKIP`；展示后漏答 `NA_MISS` | `info_confidence_optional`；仅自我感知 |

## 缺失与特别回答编码

- `NA_SKIP`：按路径未展示；不是零分。
- `NA_APPL`：题目已展示但不适用。Q7 的具体含义为：最近任务存在，但没有生成式AI可参与的环节；不再用于表示 Q1 无合格任务。
- `NA_DK`：题目已展示，回答者不知道/记不清。
- `NA_REFUSE`：题目已展示，回答者明确拒答。
- `NA_MISS`：题目已展示且应答但未答（包括技术性未答）；不得事后改记为拒答。

“没有使用”“没有可用工具”“没有相关输出”“没有遇到该情形”“没有相关经历”是实质选项，不得改编码为上述系统缺失。多选题中的“不知道”“拒答”以及明确的“尚未接触”须互斥；不得同时勾选其他选项。

## 路径核对摘要

1. Q1=NO/UNSURE/NA_REFUSE：跳过 Q2、Q3、Q7–Q12、Q14–Q16；继续 Q4–Q6、Q13、Q17–Q20（保留时）。
2. Q1=YES 且 Q7=NO/UNSURE/NO_TOOL/NA_APPL/NA_REFUSE：跳过 Q8–Q12、Q14–Q15；继续 Q13、Q16–Q20（Q16仅Q1=YES）。
3. Q1=YES 且 Q7=YES：展示对应任务与AI回顾题；Q14仍允许选择“本任务没有方法选择”，Q10–Q12/Q15保留“没有相关输出/没有遇到”选项。
4. Q13不限定最近任务；Q18是独立中性情境；Q19按一般看法作答；这些题不要求近期任务或AI使用经历。

当前仅完成静态逻辑审查；未制作在线表单、未进行真人认知访谈/试填，也未收集回答。项目门禁保持 `PILOT_BLOCKED`。
