# Phase 1E 独立复核与纠错记录

**复核范围：**模拟流程契约、跳题路径、任务状态和评分分析口径。原 Phase 1E commit 保持不变；本轮在 Phase 1F 修复，不改写历史提交。复核使用固定模拟种子，不涉及真人资料。

## 发现与修复

| 严重度 | 独立复核发现 | 修复/防回归 |
|---|---|---|
| BLOCKER | 0 | — |
| IMPORTANT | 2 | 严格跳题模拟原先可能让未确认使用者回答未展示的“未核验采纳”题；按 YES/NO/UNSURE 和无近期任务路径修正，并增加反例验证。PARTIAL/ABORTED的不可评分维度及其进入均值/评分者一致性口径不够严格；引入状态、`NOT_SCORABLE`、配对评分限制和分析资格规则。 |
| MINOR | 1 | 早期报告把问卷字段数写为 26；当前生成结构实际为 28。保留历史错误的上下文标记，在当前结果报告实际数量。 |

关键语义：无近期任务时回顾题 `NA_SKIP`；A1=NO时阶段题使用可见固定选项 `NOT_USED`、细节题跳过；A1=UNSURE时已展示的阶段题可为 `NA_DK`，但使用尚未确认的细节跳过；无相关 AI 输出使用 `NO_RELEVANT_OUTPUT`，没有方法选择时使用 `NO_METHOD_CHOICE`。0表示有可评分作答但未呈现行为，`NOT_SCORABLE`表示证据不足。

## 独立复核后状态

修复后 BLOCKER、IMPORTANT、MINOR 未关闭项均为 0（由31项单元测试和完整模拟流水线验证）；模拟数据版本为 `phase1f_validation_v1`。本记录不是工具效度证据，不改变研究设计审批或真人研究状态。详见 `results/synthetic/data_quality_report.md` 和 [Phase 1F Gate](40_phase1f_gate.md)。
