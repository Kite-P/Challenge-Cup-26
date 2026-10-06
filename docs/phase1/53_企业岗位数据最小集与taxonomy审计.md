# 企业岗位数据最小集与 taxonomy 证据审计

状态：设计审计；`RECRUITMENT_DATA_NOT_YET_AVAILABLE`。没有下载、抓取、购买、联系数据方或编码任何真实岗位文本。

## Minimum Viable Dataset 字段

| 分类 | 字段候选 | 必要性/边界 |
|---|---|---|
| `REQUIRED` | 稳定记录键、岗位标题、职责/任职文本、发布日期或可说明的时间范围、来源/版本/许可元数据 | 不具备即无法去重、界定岗位或审计文本来源；若许可禁止保留原文则必须重新设计 |
| `HIGH_VALUE` | 行业、城市/区域、企业类型、岗位族、学历/经验要求 | 有助于界定覆盖与分层；缺失需报告，不用模型补事实 |
| `OPTIONAL` | 薪酬区间、招聘人数、AI/数字岗位子类、福利 | 仅来源允许且对RQ有用时使用；薪酬不作为主要能力证据 |
| `UNNEEDED` | 求职者简历、姓名/手机号/邮箱、账户标识、平台用户画像、与岗位无关企业敏感字段 | 不采集、不保留、不尝试推断 |

没有稳定记录键或合法用途授权时，不进入文本编码。岗位标题、发布日期范围和许可条件未知时，`PENDING`。

## 岗位族候选

以财经相关岗位为主：财务、会计、审计、金融、经济分析、数据分析、运营分析、咨询/研究及其他财经相关。仅依据岗位职责及行业/职能上下文判断，不能只凭标题关键词自动纳入。AI/数字岗位仅作可选细分，不能替代主总体。

## 当前八维 taxonomy 的证据来源分类

| 维度 | 证据来源标签 | 审计判断 |
|---|---|---|
| 信息检索与评估 | `LITERATURE_SUPPORTED`、`STUDENT_MAPPING_DRIVEN`、`PENDING_JOB_TEXT_VALIDATION` | 文献与学生侧构念相关，但企业职责语义须由授权文本验证 |
| 数据整理与分析 | `DESIGN_DERIVED`、`PENDING_JOB_TEXT_VALIDATION` | 逻辑上是财经岗位常见候选能力，但当前无岗位证据 |
| 研究方法与问题解决 | `DESIGN_DERIVED`、`STUDENT_MAPPING_DRIVEN`、`PENDING_JOB_TEXT_VALIDATION` | 方法问题解决可能适配咨询/分析岗，不应覆盖所有财经岗位 |
| 沟通与写作 | `DESIGN_DERIVED`、`PENDING_JOB_TEXT_VALIDATION` | 通用职责候选；学生短任务书面表达只能部分对应 |
| 团队协作 | `DESIGN_DERIVED`、`PENDING_JOB_TEXT_VALIDATION` | 需岗位职责证据，不能由团队项目经历直接等值 |
| 数字工具与 AI 应用 | `DESIGN_DERIVED`、`PENDING_JOB_TEXT_VALIDATION` | 工具名不等同能力；AI岗位独立可选，不代表总体需求 |
| 行业/岗位专业知识 | `DESIGN_DERIVED`、`PENDING_JOB_TEXT_VALIDATION` | 当前学生中性任务刻意不测专门知识，预期多为 `NO_DIRECT_MATCH` |
| 独立判断与责任 | `LITERATURE_SUPPORTED`、`STUDENT_MAPPING_DRIVEN`、`PENDING_JOB_TEXT_VALIDATION` | 学生决策论证与工作责任有本质差异，通常只能部分映射 |

上述支持均不是岗位文本实证结论。taxonomy 不冻结；出现重复、不可区分、文本缺乏证据或法律/许可限制时允许合并、拆分或删除。

## 未来编码可靠性

如获审批，按岗位族/来源分层抽取一部分记录进行独立双编码；比例与样本量在可用总体及资源明确后决定。先试编码、修订手册，再冻结版本；保留原始独立结果、分歧代码、仲裁理由。LLM 只能提出候选标签，不可自动成为最终编码；记录模型/提示版本和输入范围，人工逐条核验原文证据、拒绝无依据标签，并报告人机分歧。当前未执行编码。
