"""仅使用虚构 CSV 验证平台中立导入边界。"""

import unittest
import tempfile
import shutil
from pathlib import Path

from src.merge_task_ratings_synthetic import merge_task_ratings, merge_rating_csv_files
from src.transform_survey_export_synthetic import transform_csv, transform_survey_export
from src.validate_synthetic_data import validate_files


class SyntheticImportTests(unittest.TestCase):
    def test_questionnaire_maps_mock_export_values(self):
        rows = [{"平台响应ID": "MOCK-1", "Q1_最近是否参与研究型学习任务": "是", "Q2_最近任务类型": "课程研究作业/课程论文", "Q3_实际参与环节": "确定或缩小研究问题|分析材料/数据", "Q7_最近任务AI使用": "没有使用"}]
        result = transform_survey_export(rows)
        self.assertEqual(result[0]["research_id"], "SYN-MOCK-1")
        self.assertEqual(result[0]["recent_research_task"], "YES")
        self.assertEqual(result[0]["ai_used"], "NO")
        self.assertEqual(result[0]["recent_task_type"], "COURSE_RESEARCH")
        self.assertEqual(result[0]["task_participation_stages"], "DEFINE_QUESTION|ANALYZE_DATA")
        self.assertEqual(result[0]["synthetic_flag"], "TRUE")

    def test_questionnaire_rejects_missing_column_unknown_option_and_duplicate_id(self):
        with self.assertRaisesRegex(ValueError, "缺少必需列"):
            transform_survey_export([{"平台响应ID": "MOCK-1"}])
        row = {"平台响应ID": "MOCK-1", "Q1_最近是否参与研究型学习任务": "也许", "Q2_最近任务类型": "课程研究作业/课程论文", "Q3_实际参与环节": "确定或缩小研究问题", "Q7_最近任务AI使用": "没有使用"}
        with self.assertRaisesRegex(ValueError, "未知选项"):
            transform_survey_export([row])
        valid = {**row, "Q1_最近是否参与研究型学习任务": "是"}
        with self.assertRaisesRegex(ValueError, "重复响应ID"):
            transform_survey_export([valid, valid])

    def test_csv_reader_handles_utf8_bom_empty_skipped_field_and_writes_canonical_output(self):
        source = Path("data/synthetic/raw_like/survey_export_mock.csv")
        with tempfile.TemporaryDirectory() as temporary:
            bom_source = Path(temporary) / "with_bom.csv"
            target = Path(temporary) / "canonical.csv"
            bom_source.write_text("\ufeff" + source.read_text(encoding="utf-8"), encoding="utf-8")
            count = transform_csv(bom_source, target)
            text = target.read_text(encoding="utf-8")
            self.assertEqual(count, 3)
            self.assertNotIn("\ufeff", text)
            self.assertIn("NA_SKIP", text)
            self.assertIn("TRUE", text)
            self.assertNotIn("平台提交时间", text)

    def test_questionnaire_rejects_unregistered_column(self):
        row = {"平台响应ID": "MOCK-1", "Q1_最近是否参与研究型学习任务": "是", "Q2_最近任务类型": "课程研究作业/课程论文", "Q3_实际参与环节": "确定或缩小研究问题", "Q7_最近任务AI使用": "没有使用", "设备指纹": "x"}
        with self.assertRaisesRegex(ValueError, "未登记列"):
            transform_survey_export([row])

    def test_q2_uses_generic_competition_wording_without_challenge_cup_label(self):
        row = {"平台响应ID": "MOCK-2", "Q1_最近是否参与研究型学习任务": "是", "Q2_最近任务类型": "学术科技竞赛中的研究任务（不指定具体赛事）", "Q3_实际参与环节": "确定或缩小研究问题", "Q7_最近任务AI使用": "没有使用"}
        result = transform_survey_export([row])
        self.assertEqual(result[0]["recent_task_type"], "COMPETITION_RESEARCH")
        row["平台响应ID"] = "MOCK-3"
        row["Q2_最近任务类型"] = "挑战杯或其他学术科技竞赛中的研究任务"
        with self.assertRaisesRegex(ValueError, "未知选项"):
            transform_survey_export([row])

    def test_questionnaire_rejects_task_answers_when_q1_skips_them(self):
        row = {"平台响应ID": "MOCK-1", "Q1_最近是否参与研究型学习任务": "否", "Q2_最近任务类型": "课程研究作业/课程论文", "Q3_实际参与环节": "确定或缩小研究问题", "Q7_最近任务AI使用": "使用过"}
        with self.assertRaisesRegex(ValueError, "Q1非是路径"):
            transform_survey_export([row])

    def test_rating_merge_flags_missing_duplicate_invalid_and_unscorable(self):
        r1 = [{"research_id": "SYN-1", "dimension": "information_evaluation", "score": "2"}]
        r2 = [{"research_id": "SYN-1", "dimension": "information_evaluation", "score": "1"}]
        merged = merge_task_ratings(r1, r2, {("SYN-1", "information_evaluation")})
        self.assertEqual(merged[0]["agreement_status"], "BOTH_RATED")
        self.assertEqual(merged[0]["r1_score"], 2)
        self.assertEqual(merged[0]["r2_score"], 1)
        self.assertEqual(merge_task_ratings(r1, [], {("SYN-1", "information_evaluation")})[0]["agreement_status"], "R2_MISSING")
        with self.assertRaisesRegex(ValueError, "重复评分"):
            merge_task_ratings(r1 + r1, r2, {("SYN-1", "information_evaluation")})
        with self.assertRaisesRegex(ValueError, "非法分值"):
            merge_task_ratings([{**r1[0], "score": "4"}], r2, {("SYN-1", "information_evaluation")})
        with self.assertRaisesRegex(ValueError, "不可评分维度被评分"):
            merge_task_ratings(r1, [], set())

    def test_rating_csv_files_merge_against_synthetic_task_scorability(self):
        task_row = {
            "research_id": "SYN-MOCK-001",
            "problem_definition": "NOT_SCORABLE",
            "information_evaluation": "1",
            "method_fit": "2",
            "limitation_boundary": "NOT_SCORABLE",
            "independent_decision": "NOT_SCORABLE",
        }
        with tempfile.TemporaryDirectory() as temporary:
            task_path = Path(temporary) / "task.csv"
            with task_path.open("w", encoding="utf-8", newline="") as stream:
                import csv

                writer = csv.DictWriter(stream, fieldnames=list(task_row))
                writer.writeheader()
                writer.writerow(task_row)
            output = Path(temporary) / "merged.csv"
            count = merge_rating_csv_files(
                "data/synthetic/raw_like/ratings_r1_mock.csv",
                "data/synthetic/raw_like/ratings_r2_mock.csv",
                task_path,
                output,
            )
            result = output.read_text(encoding="utf-8")
            self.assertEqual(count, 2)
            self.assertIn("BOTH_RATED", result)
            self.assertIn("R2_MISSING", result)

    def test_validator_rejects_phone_and_email_patterns_in_synthetic_exports(self):
        source_dir = Path("data/synthetic")
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary)
            for source in source_dir.glob("*.csv"):
                shutil.copy2(source, copied / source.name)
            survey_path = copied / "student_survey_synthetic.csv"
            original = survey_path.read_text(encoding="utf-8-sig")
            for suspicious in ("13800138000", "fictional.user@example.test"):
                survey_path.write_text(original.replace(",COURSE,", f",{suspicious},", 1), encoding="utf-8")
                self.assertTrue(any("手机号或邮箱" in error for error in validate_files(copied)))


if __name__ == "__main__":
    unittest.main()
