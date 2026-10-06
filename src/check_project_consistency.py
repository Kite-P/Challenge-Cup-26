"""检查活跃文档和 Git 跟踪清单中的已知一致性风险。"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Iterable


OLD_TERMS = re.compile(r"信息评价|信息判断|研究判断|独立判断|证据核验|information evaluation|research judgment", re.I)
ABSOLUTE_WINDOWS_PATH = re.compile(r"(?<![A-Za-z0-9])(?:[A-Z]:\\Users\\|[A-Z]:\\学习\\|[A-Z]:\\Downloads\\)", re.I)
ANON_CODE = re.compile(r"\bANON-[A-Z0-9]{6,}\b")
PAST_DEADLINE_AS_CURRENT = re.compile(r"(?:本届.{0,60}2025年|2025年.{0,60}本届)")
YEAR_TRACK_MIXUP = re.compile(r"(?:2026年.{0,30}经[·.]观|经[·.]观.{0,30}2026年)")
DANGEROUS_EXTENSIONS = {".pdf", ".docx", ".xlsx", ".zip", ".dta"}
HISTORICAL_DOCS = {
    "docs/phase0/06_current_competition_rules.md",
    "docs/competition/05_往届赛程参考_不得作为本届截止时间.md",
}
ACTIVE_DOCS = (
    "README.md",
    "docs/competition/01_比赛方向与赛道状态.md",
    "docs/review/当前项目状态_单页.md",
    "docs/review/当前活跃研究设计索引.md",
)


def scan_text(text: str, *, classification: str = "ACTIVE", path: str = "<memory>") -> list[str]:
    """对单份文本执行可单测的规则扫描；历史行需显式标注。"""
    findings: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        historical_line = classification == "HISTORICAL" or bool(re.search(r"HISTORICAL|历史版本|往届|当时|已被.*取代", line, re.I))
        if classification == "ACTIVE" and not historical_line and OLD_TERMS.search(line):
            findings.append(f"ACTIVE_OLD_TERM:{path}:{line_number}")
        if not historical_line and re.search(r"PILOT_READY|PHASE1_READY_FOR_COLLECTION", line):
            findings.append(f"UNSAFE_READY_STATUS:{path}:{line_number}")
        if not historical_line and PAST_DEADLINE_AS_CURRENT.search(line):
            findings.append(f"PAST_DEADLINE_AS_CURRENT:{path}:{line_number}")
        if not historical_line and YEAR_TRACK_MIXUP.search(line):
            findings.append(f"YEAR_TRACK_MIXUP:{path}:{line_number}")
        if ABSOLUTE_WINDOWS_PATH.search(line):
            findings.append(f"LOCAL_ABSOLUTE_PATH:{path}:{line_number}")
        if classification == "ACTIVE" and not historical_line and ANON_CODE.search(line):
            findings.append(f"RANDOM_ANON_CODE:{path}:{line_number}")
    return findings


def scan_tracked_paths(paths: Iterable[str]) -> list[str]:
    """报告意外跟踪的原始目录或大型本地交付格式。"""
    findings = []
    for item in paths:
        normalized = item.replace("\\", "/").lower()
        if normalized.startswith(("references/raw/", "data/raw/", "data/private/")):
            findings.append(f"RAW_PATH_TRACKED:{item}")
        if Path(normalized).suffix in DANGEROUS_EXTENSIONS:
            findings.append(f"DANGEROUS_TRACKED_EXTENSION:{item}")
    return findings


def scan_repository(root: str | Path = ".") -> list[str]:
    """扫描显式活跃文档清单与 Git 索引，不递归改写任何文件。"""
    base = Path(root)
    findings = []
    for relative in (*ACTIVE_DOCS, *HISTORICAL_DOCS):
        path = base / relative
        if not path.exists():
            findings.append(f"ACTIVE_DOC_MISSING:{relative}")
            continue
        classification = "HISTORICAL" if relative in HISTORICAL_DOCS else "ACTIVE"
        findings.extend(scan_text(path.read_text(encoding="utf-8"), classification=classification, path=relative))
    try:
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=base, check=True, capture_output=True
        )
        tracked = result.stdout.decode("utf-8").split("\0")
        findings.extend(scan_tracked_paths(item for item in tracked if item))
    except (OSError, subprocess.CalledProcessError):
        findings.append("GIT_INDEX_UNAVAILABLE")
    return findings


if __name__ == "__main__":
    results = scan_repository()
    if results:
        print("\n".join(results))
        raise SystemExit(1)
    print("CONSISTENCY_SCAN_PASS")
