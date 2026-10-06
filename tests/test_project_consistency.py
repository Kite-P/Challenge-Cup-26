"""一致性扫描器的规则级回归测试。"""

import unittest

from src.check_project_consistency import scan_text, scan_tracked_paths


class ProjectConsistencyTests(unittest.TestCase):
    def test_active_old_term_is_detected_but_historical_line_is_allowed(self):
        self.assertTrue(any("ACTIVE_OLD_TERM" in x for x in scan_text("当前核心构念：信息评价")))
        self.assertFalse(scan_text("HISTORICAL：当时使用信息评价"))

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
