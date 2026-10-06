"""按固定顺序运行仓库一致性、单元测试与合成数据校验。"""

from __future__ import annotations

import argparse
import subprocess
import sys


def run(command: list[str], label: str) -> bool:
    print(f"\n=== {label} ===", flush=True)
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        print(f"{label}_FAIL exit={completed.returncode}", flush=True)
        return False
    print(f"{label}_PASS", flush=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", action="store_true", help="附加执行完整 Phase 1E 合成流水线")
    args = parser.parse_args()
    checks = [
        ([sys.executable, "-m", "src.check_project_consistency"], "一致性扫描"),
        ([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], "单元测试"),
        ([sys.executable, "-m", "src.validate_synthetic_data"], "合成数据校验"),
    ]
    if args.pipeline:
        checks.append(([sys.executable, "-m", "src.run_phase1e_synthetic_pipeline"], "完整合成流水线"))
    for command, label in checks:
        if not run(command, label):
            return 1
    print("REPO_CHECKS_PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
