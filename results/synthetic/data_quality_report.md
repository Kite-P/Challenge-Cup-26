# 模拟数据质量检查报告

**本报告仅描述人工构造的流程测试数据，不得用于研究结论。**

| 文件 | 行数 | 字段数 | 主键/关联检查 | 缺失码统计 |
|---|---:|---:|---|---|
| 问卷 | 240 | 28 | research_id | 2349个显式缺失/跳题码 |
| 短任务 | 80 | 18 | research_id | 226个显式缺失/跳题码 |
| 评分 | 960 | 5 | research_id+rater_id+dimension | 0个显式缺失/跳题码 |
| 岗位 | 360 | 12 | stable_job_record_key | 95个显式缺失/跳题码 |
| 岗位标签 | 2880 | 5 | stable_job_record_key+dimension | 0个显式缺失/跳题码 |

- 任务编号均来自问卷：True。
- 评分编号均来自任务：True。
- 所有CSV行均有 `synthetic_flag=TRUE`；未设置真实身份映射表。
- 异常记录数：0。
- 缺失/跳题码：NA_SKIP、NA_APPL、NA_DK、NA_MISS；均未用空白或0代替。
