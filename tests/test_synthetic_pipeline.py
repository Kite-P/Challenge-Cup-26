"""合成数据流程的契约测试。"""

import unittest
from unittest.mock import patch
import json
from copy import deepcopy
from pathlib import Path

from src.generate_synthetic_data import DIMENSIONS, build_synthetic_bundle
from src.rater_reliability import weighted_cohen_kappa
from src.validate_synthetic_data import quality_summary, validate_bundle


class SyntheticPipelineTests(unittest.TestCase):
    """检查固定种子、关联边界与模拟数据标记。"""

    @classmethod
    def setUpClass(cls):
        cls.bundle = build_synthetic_bundle(seed=20261004, n_survey=240, n_task=80, n_jobs=360)

    def test_fixed_seed_is_deterministic(self):
        self.assertEqual(self.bundle, build_synthetic_bundle(seed=20261004, n_survey=240, n_task=80, n_jobs=360))

    def test_survey_research_id_unique(self):
        ids = [row["research_id"] for row in self.bundle["survey"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_task_is_survey_subset(self):
        survey = {row["research_id"] for row in self.bundle["survey"]}
        self.assertTrue({row["research_id"] for row in self.bundle["task"]} <= survey)

    def test_ratings_are_task_subset(self):
        task = {row["research_id"] for row in self.bundle["task"]}
        self.assertTrue({row["research_id"] for row in self.bundle["ratings"]} <= task)

    def test_enterprise_record_key_unique(self):
        keys = [row["stable_job_record_key"] for row in self.bundle["jobs"]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_task_scores_are_bounded(self):
        for row in self.bundle["task"]:
            for dimension in self.bundle["dimensions"]:
                self.assertIn(row[dimension], {0, 1, 2, "NOT_SCORABLE"})

    def test_all_rows_are_marked_synthetic(self):
        for key, rows in self.bundle.items():
            if key != "dimensions":
                self.assertTrue(all(row.get("synthetic_flag") == "TRUE" for row in rows))
                if rows:
                    self.assertTrue(all(row.get("synthetic_version") == "phase1h1_five_dimension_v1" for row in rows))

    def test_active_task_dimensions_are_exactly_five(self):
        self.assertEqual(DIMENSIONS, ("problem_definition", "information_evaluation", "method_fit", "limitation_boundary", "independent_decision"))
        self.assertEqual(set(self.bundle["dimensions"]), set(DIMENSIONS))
        self.assertNotIn("reasoning_quality", self.bundle["task"][0])

    def test_complete_partial_and_aborted_scoring_contract(self):
        complete = [row for row in self.bundle["task"] if row["task_status"] == "COMPLETE"]
        partial = [row for row in self.bundle["task"] if row["task_status"] == "PARTIAL"]
        aborted = [row for row in self.bundle["task"] if row["task_status"] == "ABORTED"]
        self.assertTrue(complete and partial and aborted)
        self.assertTrue(all(all(row[field] in {0, 1, 2} for field in DIMENSIONS) for row in complete))
        self.assertTrue(all(1 <= sum(row[field] in {0, 1, 2} for field in DIMENSIONS) < len(DIMENSIONS) for row in partial))
        self.assertTrue(all(row[field] == "NOT_SCORABLE" for row in aborted for field in DIMENSIONS))
        self.assertTrue(all(row["final_decision_owner"] == "NOT_REACHED" for row in aborted))

    def test_questionnaire_q1_q7_skip_paths_are_consistent(self):
        recent_states = {row["recent_research_task"] for row in self.bundle["survey"]}
        self.assertTrue({"YES", "NO", "UNSURE", "NA_REFUSE"} <= recent_states)
        q7_states = {row["ai_used"] for row in self.bundle["survey"] if row["recent_research_task"] == "YES"}
        self.assertTrue({"YES", "NO", "UNSURE", "NO_TOOL", "NA_APPL", "NA_REFUSE"} <= q7_states)
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_validator_rejects_q7_answer_when_q1_skips_it(self):
        changed = deepcopy(self.bundle)
        row = next(row for row in changed["survey"] if row["recent_research_task"] != "YES")
        row["ai_used"] = "YES"
        self.assertTrue(any("Q1" in error or "跳题" in error for error in validate_bundle(changed)))

    def test_questionnaire_has_28_fields(self):
        self.assertEqual(len(self.bundle["survey"][0]), 28)

    def test_survey_analyzer_uses_v05_task_fields(self):
        import pandas as pd
        from src import analyze_student_survey_synthetic as analyzer

        frame = pd.DataFrame(self.bundle["survey"])
        with patch.object(analyzer, "read", return_value=frame), patch.object(analyzer, "count_table") as count:
            analyzer.main()
        fields = {call.args[1] for call in count.call_args_list}
        self.assertIn("recent_task_type", fields)
        self.assertIn("task_participation_stages", fields)
        self.assertNotIn("research_experience_type", fields)

    def test_quality_summary_counts_complete_tasks_only_as_analysis_eligible(self):
        metrics = quality_summary(self.bundle)
        complete = sum(row["task_status"] == "COMPLETE" for row in self.bundle["task"])
        self.assertEqual(metrics["analysis_eligible_count"], complete)
        self.assertEqual(metrics["anomaly_count"], 0)

    def test_all_rating_rows_are_actual_ratings(self):
        self.assertTrue(self.bundle["ratings"])
        self.assertTrue(all(row["rating_status"] == "RATED" for row in self.bundle["ratings"]))

    def test_nonusers_have_no_effective_ai_process_answers(self):
        for row in self.bundle["survey"]:
            if row["ai_used"] != "YES":
                for field in ("ai_reason_check", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance"):
                    self.assertIn(row[field], {"NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS", "NOT_USED", "NO_RELEVANT_OUTPUT", "NOT_ENCOUNTERED"})

    def test_validator_returns_no_errors_for_generated_bundle(self):
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_survey_contains_required_synthetic_fields(self):
        fields = set(self.bundle["survey"][0])
        self.assertTrue({"ai_stage_problem", "ai_reason_check", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "info_source_check", "a9_first_action", "recent_task_type", "task_participation_stages", "method_training", "major_group", "year_of_study", "school_type", "guidance_context", "unverified_acceptance", "info_confidence_optional"} <= fields)

    def test_missing_codes_are_distinguished(self):
        codes = {value for row in self.bundle["survey"] for value in row.values()}
        self.assertTrue({"NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS"} <= codes)

    def test_job_labels_use_simulated_ground_truth_and_eight_dimensions(self):
        self.assertEqual(len(self.bundle["labels"]), len(self.bundle["jobs"]) * 8)
        self.assertTrue(all(row["label_source"] == "SIMULATED_GROUND_TRUTH" for row in self.bundle["labels"]))

    def test_validator_rejects_invalid_task_score(self):
        altered = {key: [dict(row) for row in value] if isinstance(value, list) and key != "dimensions" else value for key, value in self.bundle.items()}
        altered["task"][0]["problem_definition"] = 3
        self.assertTrue(any("评分超出" in error for error in validate_bundle(altered)))

    def test_validator_rejects_legacy_reasoning_quality_score(self):
        altered = deepcopy(self.bundle)
        altered["task"][0]["reasoning_quality"] = 2
        self.assertTrue(any("reasoning_quality" in error for error in validate_bundle(altered)))

    def test_validator_rejects_wrong_synthetic_flag(self):
        changed = deepcopy(self.bundle)
        changed["jobs"][0]["synthetic_flag"] = "FALSE"
        self.assertTrue(any("未标记为模拟" in error for error in validate_bundle(changed)))

    def test_validator_rejects_wrong_synthetic_version(self):
        changed = deepcopy(self.bundle)
        changed["survey"][0]["synthetic_version"] = "unexpected_version"
        self.assertTrue(any("版本缺失或不匹配" in error for error in validate_bundle(changed)))

    def test_validator_rejects_duplicate_stable_job_key(self):
        changed = deepcopy(self.bundle)
        changed["jobs"][1]["stable_job_record_key"] = changed["jobs"][0]["stable_job_record_key"]
        self.assertTrue(any("stable_job_record_key 不唯一" in error for error in validate_bundle(changed)))

    def test_validator_rejects_duplicate_research_id(self):
        changed = deepcopy(self.bundle)
        changed["survey"][1]["research_id"] = changed["survey"][0]["research_id"]
        self.assertTrue(any("research_id 不唯一" in error for error in validate_bundle(changed)))

    def test_two_raters_have_some_disagreement(self):
        paired = {}
        for row in self.bundle["ratings"]:
            paired.setdefault((row["research_id"], row["dimension"]), {})[row["rater_id"]] = row["score"]
        self.assertTrue(any(pair["R1"] != pair["R2"] for pair in paired.values()))

    def test_all_schemas_parse_and_describe_fields(self):
        paths = Path("schemas").glob("*.json")
        schemas = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
        self.assertEqual(len(schemas), 5)
        for schema in schemas:
            self.assertTrue(schema["properties"])
            for field, spec in schema["properties"].items():
                self.assertTrue("type" in spec or "oneOf" in spec, field)
                self.assertIn("nullable", spec, field)
                self.assertIn("description_zh", spec, field)
                self.assertIn("synthetic_only", spec, field)
                if "enum" in spec:
                    self.assertIn("allowed_values", spec, field)

    def test_task_schema_is_five_dimensional_and_versioned(self):
        task = json.loads(Path("schemas/student_task_schema.json").read_text(encoding="utf-8"))
        ratings = json.loads(Path("schemas/task_ratings_schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(task["required"]) & set(DIMENSIONS), set(DIMENSIONS))
        self.assertNotIn("reasoning_quality", task["properties"])
        self.assertNotIn("reasoning_quality", ratings["properties"]["dimension"]["enum"])
        self.assertEqual(task["properties"]["synthetic_version"]["enum"], ["phase1h1_five_dimension_v1"])

    def test_no_recent_task_skips_all_task_recall_items(self):
        fields = ("ai_used", "ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", "ai_reason_check", "ai_gave_sources", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "method_choice_occurred", "ai_method_compare", "unverified_acceptance")
        row = next(row for row in self.bundle["survey"] if row["recent_research_task"] == "NO")
        self.assertTrue(all(row[field] == "NA_SKIP" for field in fields))

    def test_ai_non_yes_routes_skip_q8_to_q12_and_q14_to_q15(self):
        row = next(row for row in self.bundle["survey"] if row["ai_used"] == "NO")
        self.assertTrue(all(row[field] == "NA_SKIP" for field in ("ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", "ai_reason_check", "ai_gave_sources", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance", "method_choice_occurred")))

    def test_ai_unsure_skips_interaction_recall_items(self):
        row = next(row for row in self.bundle["survey"] if row["ai_used"] == "UNSURE")
        self.assertTrue(all(row[field] == "NA_SKIP" for field in ("ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", "ai_reason_check", "ai_gave_sources", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance", "method_choice_occurred")))

    def test_no_sources_uses_displayed_no_relevant_output_option(self):
        row = next(row for row in self.bundle["survey"] if row["ai_gave_sources"] == "NO")
        self.assertEqual(row["ai_evidence_check"], "NO_RELEVANT_OUTPUT")

    def test_no_method_choice_uses_displayed_non_applicable_option(self):
        row = next(row for row in self.bundle["survey"] if row["method_choice_occurred"] == "NO" and row["ai_used"] == "YES")
        self.assertEqual(row["ai_method_compare"], "NO_METHOD_CHOICE")

    def test_no_recent_task_skips_task_type_and_participation(self):
        row = next(row for row in self.bundle["survey"] if row["recent_research_task"] != "YES")
        self.assertEqual(row["recent_task_type"], "NA_SKIP")
        self.assertEqual(row["task_participation_stages"], "NA_SKIP")

    def test_task_has_three_state_status(self):
        self.assertTrue({"COMPLETE", "PARTIAL", "ABORTED"} <= {row["task_status"] for row in self.bundle["task"]})

    def test_aborted_tasks_have_no_scores_or_ratings(self):
        aborted = {row["research_id"] for row in self.bundle["task"] if row["task_status"] == "ABORTED"}
        self.assertTrue(aborted)
        self.assertTrue(all(row[d] == "NOT_SCORABLE" for row in self.bundle["task"] if row["research_id"] in aborted for d in self.bundle["dimensions"]))
        self.assertFalse(any(row["research_id"] in aborted for row in self.bundle["ratings"]))
        self.assertTrue(all(row["final_decision_owner"] == "NOT_REACHED" for row in self.bundle["task"] if row["research_id"] in aborted))

    def test_partial_tasks_only_score_observable_dimensions(self):
        partial = [row for row in self.bundle["task"] if row["task_status"] == "PARTIAL"]
        self.assertTrue(partial)
        self.assertTrue(all(any(row[d] in (0, 1, 2) for d in self.bundle["dimensions"]) and any(row[d] == "NOT_SCORABLE" for d in self.bundle["dimensions"]) for row in partial))

    def test_unscorable_task_dimensions_never_receive_ratings(self):
        task = {row["research_id"]: row for row in self.bundle["task"]}
        self.assertTrue(all(task[r["research_id"]][r["dimension"]] in (0, 1, 2) for r in self.bundle["ratings"]))

    def test_nonusers_never_have_ai_in_joint_decision_category(self):
        self.assertTrue(all(row["final_decision_owner"] != "STUDENT_AFTER_AI_INPUT" for row in self.bundle["task"] if row["ai_used_in_task"] == "NO"))

    def test_enterprise_taxonomy_remains_eight_dimensions(self):
        self.assertEqual(len({row["dimension"] for row in self.bundle["labels"]}), 8)

    def test_validator_rejects_unshown_question_as_unknown(self):
        changed = deepcopy(self.bundle)
        row = next(row for row in changed["survey"] if row["ai_used"] == "NO")
        row["ai_reason_check"] = "NA_DK"
        self.assertTrue(any("跳题" in error or "未展示" in error for error in validate_bundle(changed)))

    def test_validator_rejects_score_on_aborted_task(self):
        changed = deepcopy(self.bundle)
        row = next(row for row in changed["task"] if row["task_status"] == "ABORTED")
        row["problem_definition"] = 0
        self.assertTrue(any("不可评分" in error or "ABORTED" in error for error in validate_bundle(changed)))

    def test_weighted_kappa_full_agreement_is_one(self):
        result = weighted_cohen_kappa([0, 1, 2], [0, 1, 2])
        self.assertEqual(result["n_pairs"], 3)
        self.assertAlmostEqual(result["kappa"], 1.0)
        self.assertIsNone(result["undefined_reason"])

    def test_weighted_kappa_ignores_unpaired_missing_ratings(self):
        result = weighted_cohen_kappa([0, None, 2, "NA_SKIP"], [0, 1, 2, 1])
        self.assertEqual(result["n_pairs"], 2)
        self.assertAlmostEqual(result["kappa"], 1.0)

    def test_weighted_kappa_reports_undefined_for_single_category(self):
        result = weighted_cohen_kappa([1, 1, 1], [1, 1, 1])
        self.assertIsNone(result["kappa"])
        self.assertEqual(result["undefined_reason"], "NO_EXPECTED_DISAGREEMENT")

    def test_weighted_kappa_matches_known_quadratic_example(self):
        result = weighted_cohen_kappa([0, 0, 1, 1], [0, 1, 1, 2])
        self.assertAlmostEqual(result["kappa"], 0.5)

    def test_weighted_kappa_rejects_invalid_score_and_length(self):
        with self.assertRaises(ValueError):
            weighted_cohen_kappa([0, 3], [0, 2])
        with self.assertRaises(ValueError):
            weighted_cohen_kappa([0], [0, 1])


if __name__ == "__main__":
    unittest.main()
