"""合成数据流程的契约测试。"""

import unittest
from unittest.mock import patch
import json
import re
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
                    self.assertTrue(all(row.get("synthetic_version") == "phase2b_v06_contract_v2" for row in rows))

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

    def test_q2_unknown_and_refusal_are_distinct_simulated_answers(self):
        q2_states = {row["recent_task_type"] for row in self.bundle["survey"] if row["recent_research_task"] == "YES"}
        self.assertTrue({"NA_DK", "NA_REFUSE"} <= q2_states)

    def test_q13_no_experience_is_distinct_from_unknown(self):
        q13_states = {row["info_source_check_actions"] for row in self.bundle["survey"]}
        self.assertTrue({"NO_RELATED_EXPERIENCE", "NA_DK", "NA_REFUSE"} <= q13_states)

    def test_q10_separates_check_status_objects_and_methods(self):
        rows = self.bundle["survey"]
        self.assertTrue(any(row["ai_evidence_checked"] == "YES" for row in rows))
        self.assertTrue(any(row["ai_evidence_checked"] == "NO" for row in rows))
        object_codes = {"SOURCE_EXISTS", "CLAIM_SUPPORT", "DATE_SCOPE", "POPULATION_MEASURE", "DATA_CALCULATION", "CROSS_SOURCE", "OTHER"}
        method_codes = {"OPEN_ORIGINAL", "SEARCH_INDEPENDENT", "COMPARE_TEXT", "RECALCULATE", "CONSULT_QUALIFIED_PERSON", "OTHER"}
        for row in rows:
            objects, methods = row["ai_evidence_objects"], row["ai_evidence_methods"]
            if row["ai_evidence_checked"] == "YES":
                self.assertTrue(objects in {"NA_DK", "NA_REFUSE", "NA_MISS"} or set(objects.split("|")) <= object_codes)
                self.assertTrue(methods in {"NA_DK", "NA_REFUSE", "NA_MISS"} or set(methods.split("|")) <= method_codes)
                self.assertNotIn("NA_SKIP", (objects, methods))
            else:
                self.assertEqual((objects, methods), ("NA_SKIP", "NA_SKIP"))

    def test_q10_refusal_is_a_valid_status_not_an_invalid_answer(self):
        changed = deepcopy(self.bundle)
        row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
        row.update(ai_evidence_checked="NA_REFUSE", ai_evidence_objects="NA_SKIP", ai_evidence_methods="NA_SKIP")
        self.assertEqual(validate_bundle(changed), [])

    def test_q10_six_response_states_remain_distinct(self):
        states = ("YES", "NO", "NO_RELEVANT_OUTPUT", "NA_DK", "NA_REFUSE", "NA_MISS")
        for state in states:
            with self.subTest(state=state):
                changed = deepcopy(self.bundle)
                row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
                row["ai_evidence_checked"] = state
                row["ai_evidence_objects"] = "SOURCE_EXISTS" if state == "YES" else "NA_SKIP"
                row["ai_evidence_methods"] = "OPEN_ORIGINAL" if state == "YES" else "NA_SKIP"
                self.assertEqual(validate_bundle(changed), [])

    def test_q10_subitems_accept_multiselect_and_each_missing_state(self):
        markers = ("NA_DK", "NA_REFUSE", "NA_MISS")
        valid_object = "SOURCE_EXISTS|CLAIM_SUPPORT"
        valid_method = "OPEN_ORIGINAL|COMPARE_TEXT"
        for field in ("ai_evidence_objects", "ai_evidence_methods"):
            for marker in markers:
                with self.subTest(field=field, marker=marker):
                    changed = deepcopy(self.bundle)
                    row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
                    row["ai_evidence_checked"] = "YES"
                    row["ai_evidence_objects"] = valid_object
                    row["ai_evidence_methods"] = valid_method
                    row[field] = marker
                    self.assertEqual(validate_bundle(changed), [])

    def test_q10_rejects_refusal_mixed_with_substantive_multiselect(self):
        changed = deepcopy(self.bundle)
        row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
        row.update(ai_evidence_checked="YES", ai_evidence_objects="SOURCE_EXISTS|NA_REFUSE", ai_evidence_methods="OPEN_ORIGINAL")
        self.assertTrue(validate_bundle(changed))

    def test_q10_rejects_duplicate_or_unknown_subitem_codes(self):
        for value in ("SOURCE_EXISTS|SOURCE_EXISTS", "NOT_A_Q10_OPTION", "OPEN_ORIGINAL|NA_DK"):
            with self.subTest(value=value):
                changed = deepcopy(self.bundle)
                row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
                row.update(ai_evidence_checked="YES", ai_evidence_objects=value, ai_evidence_methods="OPEN_ORIGINAL")
                self.assertTrue(validate_bundle(changed))

    def test_q13_supports_multiple_information_check_actions(self):
        rows = self.bundle["survey"]
        self.assertTrue(any("|" in row["info_source_check_actions"] for row in rows))
        self.assertTrue(any(row["info_source_check_actions"] == "NO_RELATED_EXPERIENCE" for row in rows))

    def test_q13_accepts_each_exclusive_non_substantive_response(self):
        for value in ("NO_SPECIAL_CHECK", "NO_RELATED_EXPERIENCE", "NA_DK", "NA_REFUSE", "NA_MISS"):
            with self.subTest(value=value):
                changed = deepcopy(self.bundle)
                changed["survey"][0]["info_source_check_actions"] = value
                self.assertEqual(validate_bundle(changed), [])

    def test_q13_rejects_special_option_combined_with_action(self):
        for value in ("OPEN_ORIGINAL|NO_SPECIAL_CHECK", "CHECK_DATE|NO_RELATED_EXPERIENCE", "ASK_PERSON|NA_DK", "COMPARE_SOURCES|NA_REFUSE", "CHECK_METHOD|NA_MISS"):
            with self.subTest(value=value):
                changed = deepcopy(self.bundle)
                changed["survey"][0]["info_source_check_actions"] = value
                self.assertTrue(validate_bundle(changed))

    def test_q13_rejects_duplicate_and_unknown_options(self):
        for value in ("CHECK_DATE|CHECK_DATE", "NOT_A_Q13_OPTION", ""):
            with self.subTest(value=value):
                changed = deepcopy(self.bundle)
                changed["survey"][0]["info_source_check_actions"] = value
                self.assertTrue(validate_bundle(changed))

    def test_q14_distinguishes_personal_method_actions_from_ai_comparison(self):
        rows = self.bundle["survey"]
        self.assertTrue(any(row["method_choice_occurred"] == "YES" and row["ai_used"] == "NO" for row in rows))
        self.assertTrue(any(row["method_choice_occurred"] == "YES" and row["ai_used"] == "YES" for row in rows))
        for row in rows:
            if row["method_choice_occurred"] == "YES":
                self.assertNotEqual(row["method_decision_actions"], "NA_SKIP")
            else:
                self.assertEqual(row["method_decision_actions"], "NA_SKIP")
            if row["ai_used"] != "YES":
                self.assertEqual(row["ai_method_compare"], "NA_SKIP")
            else:
                self.assertIn(row["ai_method_compare"], {"YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"})

    def test_q14_ai_comparison_answer_is_independent_of_method_choice(self):
        for value in ("YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"):
            with self.subTest(value=value):
                changed = deepcopy(self.bundle)
                row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
                row.update(method_choice_occurred="NO", method_decision_actions="NA_SKIP", ai_method_compare=value)
                self.assertEqual(validate_bundle(changed), [])

    def test_q14_method_choice_refusal_and_missing_are_preserved(self):
        for state in ("NA_DK", "NA_REFUSE", "NA_MISS"):
            with self.subTest(state=state):
                changed = deepcopy(self.bundle)
                row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
                row.update(method_choice_occurred=state, method_decision_actions="NA_SKIP", ai_method_compare="NO")
                self.assertEqual(validate_bundle(changed), [])

    def test_q14_requires_ai_comparison_response_when_ai_user_was_asked(self):
        changed = deepcopy(self.bundle)
        row = next(row for row in changed["survey"] if row["ai_used"] == "YES")
        row.update(method_choice_occurred="NA_DK", method_decision_actions="NA_SKIP", ai_method_compare="NA_SKIP")
        self.assertTrue(validate_bundle(changed))

    def test_q16_training_need_is_separate_and_not_skipped_without_recent_task(self):
        rows = self.bundle["survey"]
        self.assertTrue(any(row["recent_research_task"] == "NO" and row["training_need"] != "NA_SKIP" for row in rows))
        self.assertTrue(any("|" in row["training_need"] for row in rows))
        self.assertTrue(any(row["training_need"] == "NO_ADDITIONAL_NEED" for row in rows))

    def test_q6_and_q16_multiselect_special_states_are_exclusive(self):
        changed = deepcopy(self.bundle)
        row = changed["survey"][0]
        row["method_training"] = "NONE|COURSE"
        self.assertTrue(validate_bundle(changed))
        changed = deepcopy(self.bundle)
        changed["survey"][0]["training_need"] = "RESEARCH_QUESTION|NA_REFUSE"
        self.assertTrue(validate_bundle(changed))

    def test_no_recent_research_task_does_not_remove_respondent_from_candidate_sample(self):
        self.assertEqual(len(self.bundle["survey"]), 240)
        self.assertTrue(any(row["recent_research_task"] == "NO" for row in self.bundle["survey"]))
        for row in self.bundle["survey"]:
            if row["recent_research_task"] != "YES":
                self.assertNotEqual(row["info_source_check_actions"], "NA_SKIP")
                self.assertNotEqual(row["training_need"], "NA_SKIP")

    def test_validator_rejects_q7_answer_when_q1_skips_it(self):
        changed = deepcopy(self.bundle)
        row = next(row for row in changed["survey"] if row["recent_research_task"] != "YES")
        row["ai_used"] = "YES"
        self.assertTrue(any("Q1" in error or "跳题" in error for error in validate_bundle(changed)))

    def test_questionnaire_contract_has_expected_fields(self):
        self.assertTrue({"ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "method_decision_actions", "training_need", "info_source_check_actions", "policy_awareness", "open_concern"} <= set(self.bundle["survey"][0]))

    def test_q1_to_q20_synthetic_item_field_coverage_is_explicit(self):
        expected = {"recent_research_task", "recent_task_type", "task_participation_stages", "major_group", "year_of_study", "method_training", "ai_used", "ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "info_source_check_actions", "method_choice_occurred", "method_decision_actions", "ai_method_compare", "unverified_acceptance", "training_need", "policy_awareness", "a9_first_action", "a9_reason", "open_concern", "info_confidence_optional"}
        fields = set(self.bundle["survey"][0])
        self.assertTrue(expected <= fields)
        schema = json.loads(Path("schemas/student_survey_schema.json").read_text(encoding="utf-8"))
        self.assertTrue(expected <= set(schema["properties"]))
        self.assertTrue(all(row["policy_awareness"] for row in self.bundle["survey"]))
        self.assertTrue(all(row["open_concern"] for row in self.bundle["survey"]))
        self.assertNotIn("ai_gave_sources", fields)
        self.assertNotIn("ai_gave_sources", schema["properties"])

    def test_survey_analyzer_uses_current_questionnaire_fields(self):
        import pandas as pd
        from src import analyze_student_survey_synthetic as analyzer

        frame = pd.DataFrame(self.bundle["survey"])
        with patch.object(analyzer, "read", return_value=frame), patch.object(analyzer, "count_table") as count, patch.object(analyzer, "multi_select_count_table") as multi_count:
            analyzer.main()
        fields = {call.args[1] for call in count.call_args_list}
        self.assertIn("recent_task_type", fields)
        multi_fields = {call.args[1] for call in multi_count.call_args_list}
        self.assertIn("task_participation_stages", multi_fields)
        self.assertIn("info_source_check_actions", multi_fields)
        self.assertNotIn("research_experience_type", fields)

    def test_multi_select_summary_counts_each_selected_option(self):
        import pandas as pd
        from src.synthetic_analysis_common import multi_select_count_table

        frame = pd.DataFrame({"choices": ["A|B", "B", "NA_SKIP"]})
        with patch("src.synthetic_analysis_common.write") as write:
            result = multi_select_count_table(frame, "choices", "unused.csv")
        counts = dict(zip(result["choices"], result["count"], strict=True))
        self.assertEqual(counts, {"B": 2, "A": 1})
        self.assertEqual(dict(zip(result["choices"], result["proportion_respondents"], strict=True))["B"], 2 / 3)
        write.assert_called_once()

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
                for field in ("ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance"):
                    self.assertIn(row[field], {"NA_SKIP", "NA_APPL", "NA_DK", "NA_MISS", "NOT_USED", "NO_RELEVANT_OUTPUT", "NOT_ENCOUNTERED"})

    def test_validator_returns_no_errors_for_generated_bundle(self):
        self.assertEqual(validate_bundle(self.bundle), [])

    def test_survey_contains_required_synthetic_fields(self):
        fields = set(self.bundle["survey"][0])
        self.assertTrue({"ai_stage_problem", "ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "info_source_check_actions", "method_decision_actions", "training_need", "a9_first_action", "recent_task_type", "task_participation_stages", "method_training", "major_group", "year_of_study", "school_type", "guidance_context", "unverified_acceptance", "info_confidence_optional"} <= fields)

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
        self.assertEqual(task["properties"]["synthetic_version"]["enum"], ["phase2b_v06_contract_v2"])

    def test_q10_q13_q14_schema_patterns_cover_only_declared_states(self):
        schema = json.loads(Path("schemas/student_survey_schema.json").read_text(encoding="utf-8"))
        properties = schema["properties"]
        self.assertIn("NA_REFUSE", properties["ai_evidence_checked"]["enum"])
        self.assertIn("NA_MISS", properties["ai_evidence_checked"]["enum"])
        samples = {
            "ai_evidence_objects": ("SOURCE_EXISTS|CLAIM_SUPPORT", "OTHER", "NA_DK", "NA_REFUSE", "NA_MISS", "NA_SKIP"),
            "ai_evidence_methods": ("OPEN_ORIGINAL|COMPARE_TEXT", "OTHER", "NA_DK", "NA_REFUSE", "NA_MISS", "NA_SKIP"),
            "info_source_check_actions": ("CHECK_DATE|ASK_PERSON", "NO_SPECIAL_CHECK", "NO_RELATED_EXPERIENCE", "NA_DK", "NA_REFUSE", "NA_MISS"),
            "method_decision_actions": ("UNDERSTOOD_PURPOSE|CONSIDERED_DATA", "OTHER", "NA_DK", "NA_REFUSE", "NA_MISS", "NA_SKIP"),
            "task_participation_stages": ("DEFINE_QUESTION|OTHER", "NA_DK", "NA_REFUSE", "NA_MISS", "NA_SKIP"),
            "method_training": ("COURSE|GUIDED_TASK", "NONE", "NA_DK", "NA_REFUSE", "NA_MISS"),
            "training_need": ("RESEARCH_QUESTION|AI_CHECKING|METHOD_SELECTION", "NO_ADDITIONAL_NEED", "NA_DK", "NA_REFUSE", "NA_MISS"),
        }
        for field, values in samples.items():
            pattern = re.compile(properties[field]["pattern"])
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertIsNotNone(pattern.fullmatch(value))
            self.assertIsNone(pattern.fullmatch("UNKNOWN_OPTION"))
        self.assertEqual(properties["ai_method_compare"]["enum"], ["YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS", "NA_SKIP"])
        self.assertEqual(properties["a9_first_action"]["enum"], ["CHECK_DEFINITION", "SEEK_OTHER_EVIDENCE", "DIRECT_EFFECT_CLAIM", "GENERALIZE_TO_ALL", "NA_DK", "NA_REFUSE", "NA_MISS"])

    def test_no_recent_task_skips_all_task_recall_items(self):
        fields = ("ai_used", "ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", "ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "method_choice_occurred", "method_decision_actions", "ai_method_compare", "unverified_acceptance")
        row = next(row for row in self.bundle["survey"] if row["recent_research_task"] == "NO")
        self.assertTrue(all(row[field] == "NA_SKIP" for field in fields))

    def test_ai_non_yes_routes_skip_q8_to_q12_and_q14_to_q15(self):
        row = next(row for row in self.bundle["survey"] if row["ai_used"] == "NO")
        self.assertTrue(all(row[field] == "NA_SKIP" for field in ("ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", "ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance")))

    def test_ai_unsure_skips_interaction_recall_items(self):
        row = next(row for row in self.bundle["survey"] if row["ai_used"] == "UNSURE")
        self.assertTrue(all(row[field] == "NA_SKIP" for field in ("ai_stage_problem", "ai_stage_information", "ai_stage_method", "ai_stage_limitation", "ai_reason_check", "ai_evidence_checked", "ai_evidence_objects", "ai_evidence_methods", "ai_output_handling", "ai_disagreement_response", "ai_method_compare", "unverified_acceptance")))

    def test_q10_no_relevant_output_is_distinct_from_not_checked(self):
        row = next(row for row in self.bundle["survey"] if row["ai_evidence_checked"] == "NO_RELEVANT_OUTPUT")
        self.assertEqual(row["ai_evidence_checked"], "NO_RELEVANT_OUTPUT")
        self.assertEqual(row["ai_evidence_objects"], "NA_SKIP")
        self.assertEqual(row["ai_evidence_methods"], "NA_SKIP")

    def test_no_method_choice_does_not_suppress_ai_comparison_question(self):
        row = next(row for row in self.bundle["survey"] if row["method_choice_occurred"] == "NO" and row["ai_used"] == "YES")
        self.assertIn(row["ai_method_compare"], {"YES", "NO", "NA_DK", "NA_REFUSE", "NA_MISS"})

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
