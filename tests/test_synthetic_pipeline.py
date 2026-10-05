"""合成数据流程的契约测试。"""

import unittest
import json
from copy import deepcopy
from pathlib import Path

from src.generate_synthetic_data import build_synthetic_bundle
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
                    self.assertTrue(all(row.get("synthetic_version") == "phase1f_validation_v1" for row in rows))

    def test_questionnaire_has_28_fields(self):
        self.assertEqual(len(self.bundle["survey"][0]), 28)

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
        self.assertTrue({"ai_stage_problem", "ai_reason_check", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "info_source_check", "a9_first_action", "research_experience_depth", "method_training", "major_group", "year_of_study", "school_type", "guidance_context", "unverified_acceptance", "info_confidence_optional"} <= fields)

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

    def test_no_recent_task_skips_all_task_recall_items(self):
        fields = ("ai_used", "ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", "ai_reason_check", "ai_gave_sources", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "method_choice_occurred", "ai_method_compare", "unverified_acceptance")
        row = next(row for row in self.bundle["survey"] if row["recent_research_task"] == "NO")
        self.assertTrue(all(row[field] == "NA_SKIP" for field in fields))

    def test_ai_no_uses_visible_not_used_option_and_skips_details(self):
        row = next(row for row in self.bundle["survey"] if row["ai_used"] == "NO")
        self.assertTrue(all(row[field] == "NOT_USED" for field in ("ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation")))
        self.assertTrue(all(row[field] == "NA_SKIP" for field in ("ai_reason_check", "ai_gave_sources", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance")))

    def test_ai_unsure_marks_seen_stage_question_unknown_and_skips_details(self):
        row = next(row for row in self.bundle["survey"] if row["ai_used"] == "UNSURE")
        self.assertTrue(all(row[field] == "NA_DK" for field in ("ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation")))
        self.assertTrue(all(row[field] == "NA_SKIP" for field in ("ai_reason_check", "ai_gave_sources", "ai_evidence_check", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance")))

    def test_no_sources_uses_displayed_no_relevant_output_option(self):
        row = next(row for row in self.bundle["survey"] if row["ai_gave_sources"] == "NO")
        self.assertEqual(row["ai_evidence_check"], "NO_RELEVANT_OUTPUT")

    def test_no_method_choice_uses_displayed_non_applicable_option(self):
        row = next(row for row in self.bundle["survey"] if row["method_choice_occurred"] == "NO" and row["ai_used"] == "YES")
        self.assertEqual(row["ai_method_compare"], "NO_METHOD_CHOICE")

    def test_no_experience_skips_depth_question(self):
        row = next(row for row in self.bundle["survey"] if row["research_experience_type"] == "NONE")
        self.assertEqual(row["research_experience_depth"], "NA_SKIP")

    def test_task_has_three_state_status(self):
        self.assertTrue({"COMPLETE", "PARTIAL", "ABORTED"} <= {row["task_status"] for row in self.bundle["task"]})

    def test_aborted_tasks_have_no_scores_or_ratings(self):
        aborted = {row["research_id"] for row in self.bundle["task"] if row["task_status"] == "ABORTED"}
        self.assertTrue(aborted)
        self.assertTrue(all(row[d] == "NOT_SCORABLE" for row in self.bundle["task"] if row["research_id"] in aborted for d in self.bundle["dimensions"]))
        self.assertFalse(any(row["research_id"] in aborted for row in self.bundle["ratings"]))

    def test_partial_tasks_only_score_observable_dimensions(self):
        partial = [row for row in self.bundle["task"] if row["task_status"] == "PARTIAL"]
        self.assertTrue(partial)
        self.assertTrue(all(any(row[d] in (0, 1, 2) for d in self.bundle["dimensions"]) and any(row[d] == "NOT_SCORABLE" for d in self.bundle["dimensions"]) for row in partial))

    def test_unscorable_task_dimensions_never_receive_ratings(self):
        task = {row["research_id"]: row for row in self.bundle["task"]}
        self.assertTrue(all(task[r["research_id"]][r["dimension"]] in (0, 1, 2) for r in self.bundle["ratings"]))

    def test_nonusers_never_have_ai_in_joint_decision_category(self):
        self.assertTrue(all(row["final_decision_owner"] != "STUDENT_AFTER_AI_INPUT" for row in self.bundle["task"] if row["ai_used_in_task"] == "NO"))

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


if __name__ == "__main__":
    unittest.main()
