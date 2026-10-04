"""合成数据流程的契约测试。"""

import unittest
import json
from pathlib import Path

from src.generate_synthetic_data import build_synthetic_bundle
from src.validate_synthetic_data import validate_bundle


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
                self.assertIn(row[dimension], {0, 1, 2})

    def test_all_rows_are_marked_synthetic(self):
        for key, rows in self.bundle.items():
            if key != "dimensions":
                self.assertTrue(all(row.get("synthetic_flag") == "TRUE" for row in rows))

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
                self.assertIn("type", spec, field)
                self.assertIn("nullable", spec, field)
                self.assertIn("description_zh", spec, field)
                self.assertIn("synthetic_only", spec, field)
                if "enum" in spec:
                    self.assertIn("allowed_values", spec, field)


if __name__ == "__main__":
    unittest.main()
