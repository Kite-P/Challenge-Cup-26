"""生成问卷模拟数据的分项描述表。"""

from src.synthetic_analysis_common import count_table, multi_select_count_table, read


def main() -> int:
    data = read("student_survey_synthetic.csv")
    specs = [("recent_task_type", "survey_recent_task_type.csv"),
             ("ai_used", "survey_ai_use.csv"),
             ("ai_stage_problem", "survey_ai_stages.csv"), ("ai_reason_check", "survey_reason_check.csv"),
             ("ai_output_handling", "survey_output_handling.csv"),
             ("ai_disagreement_response", "survey_conflict_handling.csv"), ("ai_method_compare", "survey_method_comparison.csv"),
             ("ai_evidence_checked", "survey_evidence_check_status.csv"),
             ("a9_first_action", "survey_a9_strategy.csv"), ("guidance_context", "survey_guidance_context.csv"),
             ("unverified_acceptance", "survey_unverified_acceptance.csv")]
    for field, output in specs:
        count_table(data, field, output)
    multi_specs = [("task_participation_stages", "survey_task_participation.csv"),
                   ("info_source_check_actions", "survey_information_behavior.csv"), ("ai_evidence_objects", "survey_evidence_check_objects.csv"),
                   ("ai_evidence_methods", "survey_evidence_check_methods.csv"), ("method_decision_actions", "survey_method_decision_actions.csv"),
                   ("training_need", "survey_training_needs.csv")]
    for field, output in multi_specs:
        multi_select_count_table(data, field, output)
    print(f"问卷模拟描述完成：{len(specs) + len(multi_specs)}张分项表。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
