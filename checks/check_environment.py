"""실행 환경을 확인하고 결과를 JSON으로 저장한다."""

import importlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PACKAGES = {
    "requests": "requests",
    "yaml": "PyYAML",
    "pandas": "pandas",
    "openpyxl": "openpyxl",
    "markitdown": "markitdown",
}


def check_package(module_name, distribution_name):
    """모듈을 실제로 불러오고 설치된 패키지 버전을 확인한다."""
    try:
        importlib.import_module(module_name)
        return {
            "ok": True,
            "version": version(distribution_name),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def check_libreoffice():
    """LibreOffice 버전 명령이 정상 실행되는지 확인한다."""
    executable = shutil.which("libreoffice") or shutil.which("soffice")

    if not executable:
        return {
            "ok": False,
            "error": "LibreOffice 실행 파일을 찾을 수 없습니다",
        }

    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )

        return {
            "ok": result.returncode == 0,
            "version": result.stdout.strip(),
            "returncode": result.returncode,
            "stderr": result.stderr.strip(),
        }

    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main():
    packages = {
        module_name: check_package(module_name, distribution_name)
        for module_name, distribution_name in PACKAGES.items()
    }

    skill_paths = {
        "xlsx": (
            ROOT
            / "vendor"
            / "anthropic-skills"
            / "skills"
            / "xlsx"
            / "SKILL.md"
        ),
        "deep-research": (
            ROOT
            / "vendor"
            / "deep-research"
            / "SKILL.md"
        ),
        "xlsx_recalc": (
            ROOT
            / "vendor"
            / "anthropic-skills"
            / "skills"
            / "xlsx"
            / "scripts"
            / "recalc.py"
        ),
    }

    skill_files = {
        name: path.is_file()
        for name, path in skill_paths.items()
    }

    libreoffice = check_libreoffice()

    passed = (
        all(item["ok"] for item in packages.values())
        and libreoffice["ok"]
        and all(skill_files.values())
    )

    checked_at = datetime.now(timezone.utc)

    report = {
        "checked_at": checked_at.isoformat(),
        "check_scope": [
            "Python 패키지의 실제 import 및 버전 확인",
            "LibreOffice 버전 명령 실행",
            "스킬 정의 파일과 재계산 스크립트 존재 확인",
        ],
        "python": platform.python_version(),
        "os": platform.system(),
        "architecture": platform.machine(),
        "virtual_environment": sys.prefix != sys.base_prefix,
        "packages": packages,
        "libreoffice": libreoffice,
        "skill_files": skill_files,
        "status": "passed" if passed else "failed",
        "not_verified_by_this_check": [
            "Gemma API 연결 및 도구 호출",
            "스킬 전체 규격 및 참조 파일 유효성",
            "실제 엑셀 생성 및 수식 재계산",
            "markitdown을 이용한 실제 파일 변환",
        ],
    }

    output_dir = ROOT / "outputs" / "environment"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = checked_at.strftime("%Y%m%dT%H%M%S%fZ")
    output_file = output_dir / f"{timestamp}.json"

    report_text = json.dumps(
        report,
        ensure_ascii=False,
        indent=2,
    )

    output_file.write_text(
        report_text + "\n",
        encoding="utf-8",
    )

    print(report_text)
    print(f"\n검사 결과 저장: {output_file}")

    if passed:
        print("환경 검사 통과")
    else:
        print("환경 검사 실패: 위 결과의 실패 항목을 확인하세요.")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
