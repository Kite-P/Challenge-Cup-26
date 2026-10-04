"""生成问卷模拟数据的分项描述表。"""

from src.synthetic_analysis_common import count_table, read


def main() -> int:
    data = read("student_survey_synthetic.csv")
    specs = [("research_experience_type", "survey_experience_distribution.csv"), ("ai_used", "survey_ai_use.csv"),
             ("ai_stage_problem", "survey_ai_stages.csv"), ("ai_reason_check", "survey_reason_check.csv"),
             ("ai_evidence_check", "survey_evidence_handling.csv"), ("ai_output_handling", "survey_output_handling.csv"),
             ("ai_disagreement_response", "survey_conflict_handling.csv"), ("ai_method_compare", "survey_method_comparison.csv"),
             ("info_source_check", "survey_information_behavior.csv"), ("a9_first_action", "survey_a9_strategy.csv"),
             ("guidance_context", "survey_guidance_context.csv"), ("unverified_acceptance", "survey_unverified_acceptance.csv")]
    for field, output in specs:
        count_table(data, field, output)
    print(f"问卷模拟描述完成：{len(specs)}张分项表。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
