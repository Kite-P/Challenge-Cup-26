# 分析变量注册表（候选）

状态：`ACTIVE_CANDIDATE`；字段尚未冻结，不能据此创建真人数据库。

| 变量域/候选字段 | 来源 | 数据类型/构造 | 分析层级 | 缺失与解释边界 |
|---|---|---|---|---|
| `research_id` | 获批后系统生成 | 随机字符串；无学校/身份编码 | 链接键（只有单独批准后启用） | 不含姓名学号；去标识不代表匿名 |
| `ai_used`、协作阶段/输出处理 | 问卷行为项 | 分类变量；不合成为协作质量总分 | PRIMARY 描述 | 跳题、未使用、不确定分开；频数不代表能力 |
| 信息辨识与评估行为 | 问卷题/任务证据 | 自报类别与行为评分分别保留 | PRIMARY 描述；任务 SECONDARY | 不称成熟量表或稳定能力 |
| 方法理解与适配 | 问卷/任务 | 情境选择、理由及限制分项 | SECONDARY | 单任务受材料和表达影响 |
| 独立研究决策能力 | 问卷/任务 | 采纳/修改/拒绝及理由，不按选择方向自动计分 | SECONDARY | 仅解释可观察决策，不等于排斥 AI |
| 研究经历类别/深度 | 问卷 | `LOW_RESEARCH_EXPOSURE`、`COURSE_BASED`、`FORMAL_PROJECT`候选及实际角色 | 描述/分层 | 不作能力评级或入组门槛 |
| task dimension rating | 评分表 | 有序 0–2、评分者/轮次长表 | SECONDARY | `NOT_OBSERVABLE` 不编码为 0；保留 R1/R2 原值 |
| 访谈主题编码 | 去标识访谈材料 | 定性代码和片段标识 | EXPLORATORY | 小样本不推断发生率；避免可识别引文 |
| 企业岗位主题 | 合法岗位文本 | 文本编码，含来源/许可/版本元数据 | SUPPLEMENT/RESERVE | 当前 `RECRUITMENT_DATA_NOT_YET_AVAILABLE`；不推断企业战略或缺口分数 |

缺失状态候选：`NOT_SHOWN`、`SKIPPED`、`REFUSED`、`NOT_APPLICABLE`、`DON’T_KNOW`、`TECHNICAL_MISSING`、`INVALID_RESPONSE`；代码表及与既有 schema 的映射需工具冻结时复核。

禁止字段包括姓名、学号、证件号、精确生日、私人账号/令牌、无关聊天历史及未经必要性审查的敏感信息。新增变量必须记录题项来源、构造逻辑、允许缺失、主/次/探索层级及禁止解释。
