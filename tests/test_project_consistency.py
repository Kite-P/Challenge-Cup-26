"""一致性扫描器的规则级回归测试。"""

import unittest

from src.check_project_consistency import ACTIVE_DOCS, scan_text, scan_tracked_paths


class ProjectConsistencyTests(unittest.TestCase):
    def test_active_document_scan_targets_current_questionnaire_candidate(self):
        self.assertIn("docs/phase1/instruments/05_questionnaire_v0_6_supervisor_review.md", ACTIVE_DOCS)
        self.assertIn("docs/phase2/01_市调导向研究方案_v0_2.md", ACTIVE_DOCS)
        self.assertIn("docs/report/第十七届市调大赛_报告Master_v0_2.md", ACTIVE_DOCS)
        self.assertNotIn("docs/phase1/instruments/05_questionnaire_v0_4_review_ready.md", ACTIVE_DOCS)

    def test_active_document_scan_targets_phase1h_instrument_candidates(self):
        self.assertIn("docs/phase1/instruments/01_research_task_A_v0_5_supervisor_review.md", ACTIVE_DOCS)
        self.assertIn("docs/phase1/instruments/07_student_interview_v0_3_supervisor_review.md", ACTIVE_DOCS)
        self.assertIn("docs/phase1/instruments/08_teacher_interview_v0_3_supervisor_review.md", ACTIVE_DOCS)

    def test_active_document_scan_targets_phase1h_gate_and_master_draft(self):
        self.assertIn("docs/phase1/54_phase1h_gate.md", ACTIVE_DOCS)
        self.assertIn("docs/review/Phase1H_导师审阅包.md", ACTIVE_DOCS)
        self.assertIn("docs/report/大挑社会调查报告_Master_v0_1.md", ACTIVE_DOCS)

    def test_active_old_term_is_detected_but_historical_line_is_allowed(self):
        self.assertTrue(any("ACTIVE_OLD_TERM" in x for x in scan_text("当前核心构念：信息评价")))
        self.assertFalse(scan_text("HISTORICAL：当时使用信息评价"))
        self.assertFalse(scan_text("扫描词：信息评价、独立判断"))

    def test_forbidden_status_mentions_are_not_mistaken_for_active_status(self):
        self.assertFalse(scan_text("本Gate不把项目状态改为 PILOT_READY"))
        self.assertTrue(scan_text("当前项目状态为 PILOT_READY"))

    def test_historical_heading_classifies_section_contents(self):
        text = "## 旧版本历史\n历史文档中使用信息评价\n## 当前设计\n研究判断"
        findings = scan_text(text)
        self.assertEqual(sum("ACTIVE_OLD_TERM" in finding for finding in findings), 1)

    def test_unsafe_status_past_deadline_and_local_path_are_detected(self):
        text = "状态 PILOT_READY\n本届报名截止：2025年12月\n本地 D:\\Users\\someone\\project"
        codes = {finding.split(":")[0] for finding in scan_text(text)}
        self.assertTrue({"UNSAFE_READY_STATUS", "PAST_DEADLINE_AS_CURRENT", "LOCAL_ABSOLUTE_PATH"} <= codes)

    def test_current_year_mixed_with_historical_track_name_is_detected(self):
        self.assertTrue(any("YEAR_TRACK_MIXUP" in x for x in scan_text("2026年经·观当前赛道")))

    def test_raw_tracked_paths_and_binary_deliverables_are_detected(self):
        findings = scan_tracked_paths(["references/raw/paper.pdf", "data/private/records.csv", "docs/report.docx"])
        self.assertEqual(sum("RAW_PATH_TRACKED" in item for item in findings), 2)
        self.assertTrue(any("DANGEROUS_TRACKED_EXTENSION" in item for item in findings))


if __name__ == "__main__":
    unittest.main()
