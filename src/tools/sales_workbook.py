"""매출 엑셀 생성, 원본 스킬을 이용한 재계산, 검증 결과 저장."""

import argparse
import json
import math
import re
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from markitdown import MarkItDown
from openpyxl import Workbook, load_workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.comments import Comment
from openpyxl.styles import Font, PatternFill

from src.skill_loader import activate_skill, discover_skills

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def set_text(cell, value):
    """사용자 문자열을 수식으로 해석하지 않고 텍스트로 기록한다."""
    cell.value = value
    cell.data_type = "s"


def is_whole_number(value):
    return Decimal(str(value)) == Decimal(str(value)).to_integral_value()


def number_format_for(*values):
    """정수만이면 #,##0, 소수가 있으면 끝점 없이 필요한 자리만 표시한다."""
    if all(is_whole_number(value) for value in values):
        return "#,##0"
    return "#,##0.##########"


def validate_input(sheet_name, source_note, records):
    if (
        not isinstance(sheet_name, str)
        or not sheet_name.strip()
        or len(sheet_name) > 31
        or re.search(r"[\[\]:*?/\\\x00-\x1f]", sheet_name)
        or sheet_name.startswith("'")
        or sheet_name.endswith("'")
    ):
        raise ValueError("유효한 31자 이하 시트 이름이 필요합니다.")

    if (
        not isinstance(source_note, str)
        or not source_note.strip()
        or len(source_note) > 3000
    ):
        raise ValueError("3000자 이하의 데이터 출처 설명이 필요합니다.")

    if not isinstance(records, list) or not 1 <= len(records) <= 1000:
        raise ValueError("records는 1~1000행의 목록이어야 합니다.")

    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise ValueError(f"{index}행은 객체여야 합니다.")

        month = record.get("month")
        if (
            not isinstance(month, str)
            or not month.strip()
            or len(month) > 100
        ):
            raise ValueError(f"{index}행에 100자 이하 month가 필요합니다.")

        for key in ["quantity", "unit_price"]:
            value = record.get(key)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0 <= value <= 1_000_000_000
            ):
                raise ValueError(
                    f"{index}행 {key}는 0~10억 범위의 유한한 숫자여야 합니다."
                )


def build_workbook(path, sheet_name, source_note, records):
    wb = Workbook()
    try:
        ws = wb.active
        ws.title = sheet_name
        ws.append(["월", "수량", "단가(원)", "금액(원)"])

        for row_number, record in enumerate(records, start=2):
            set_text(ws.cell(row_number, 1), record["month"])
            ws.cell(row_number, 2, record["quantity"])
            ws.cell(row_number, 3, record["unit_price"])
            ws.cell(row_number, 4, f"=B{row_number}*C{row_number}")

            for column in range(1, 4):
                ws.cell(row_number, column).comment = Comment(
                    source_note, "데이터 출처"
                )

        last_data_row = len(records) + 1
        total_row = last_data_row + 1

        ws.cell(total_row, 1, "합계")
        ws.cell(total_row, 4, f"=SUM(D2:D{last_data_row})")

        note_row = total_row + 2
        notes = [
            f"데이터 출처: {source_note}",
            (
                f"수정할 입력: A2:C{last_data_row} / "
                f"자동 계산: D2:D{total_row}"
            ),
            (
                "첫 번째 입력 행 예시: "
                f"{records[0]['month']}, "
                f"수량 {records[0]['quantity']}, "
                f"단가 {records[0]['unit_price']}원"
            ),
            "수량과 단가를 변경하면 금액과 합계가 다시 계산됩니다.",
        ]

        for row_number, text in enumerate(notes, start=note_row):
            set_text(ws.cell(row_number, 1), text)

        for row in ws.iter_rows():
            for cell in row:
                cell.font = Font(name="Arial", size=11, color="000000")

        for cell in ws[1]:
            cell.font = Font(
                name="Arial", size=11, bold=True, color="FFFFFF"
            )
            cell.fill = PatternFill("solid", fgColor="244062")

        for row in ws.iter_rows(
            min_row=2, max_row=last_data_row, min_col=1, max_col=3
        ):
            for cell in row:
                cell.font = Font(name="Arial", size=11, color="0000FF")
                cell.fill = PatternFill("solid", fgColor="FFF2CC")

        amount_format = number_format_for(
            *(
                value
                for record in records
                for value in (record["quantity"], record["unit_price"])
            )
        )
        for row_number, record in enumerate(records, start=2):
            ws.cell(row_number, 2).number_format = number_format_for(
                record["quantity"]
            )
            ws.cell(row_number, 3).number_format = number_format_for(
                record["unit_price"]
            )
            ws.cell(row_number, 4).number_format = amount_format
        ws.cell(total_row, 4).number_format = amount_format

        for cell in ws[total_row]:
            cell.font = Font(name="Arial", size=11, bold=True)
            cell.fill = PatternFill("solid", fgColor="D9E2F3")

        for column in ["A", "B", "C", "D"]:
            ws.column_dimensions[column].width = 18

        ws.freeze_panes = "A2"

        chart = BarChart()
        chart.type = "col"
        chart.title = "월별 매출"
        chart.x_axis.title = "월"
        chart.y_axis.title = "금액(원)"
        chart.legend = None
        chart.add_data(
            Reference(ws, min_col=4, min_row=1, max_row=last_data_row),
            titles_from_data=True,
        )
        chart.set_categories(
            Reference(ws, min_col=1, min_row=2, max_row=last_data_row)
        )
        chart.width = 18
        chart.height = 10
        ws.add_chart(chart, "F2")

        wb.save(path)
    finally:
        wb.close()


def verify_workbook(path, sheet_name, records):
    """재계산한 파일을 읽기만 하며, 다시 저장하지 않는다."""
    formulas = load_workbook(path, data_only=False)
    try:
        values = load_workbook(path, data_only=True)
        try:
            problems = []
            checks = []

            if formulas.sheetnames != [sheet_name]:
                raise ValueError(
                    f"시트 이름 불일치: {formulas.sheetnames}"
                )

            ws = formulas[sheet_name]
            cached = values[sheet_name]
            last_data_row = len(records) + 1
            total_row = last_data_row + 1

            expected_values = {}
            expected_formulas = {}
            total = Decimal("0")

            for row_number, record in enumerate(records, start=2):
                amount = (
                    Decimal(str(record["quantity"]))
                    * Decimal(str(record["unit_price"]))
                )
                total += amount
                address = f"D{row_number}"
                expected_values[address] = amount
                expected_formulas[address] = (
                    f"=B{row_number}*C{row_number}"
                )

                actual_inputs = [
                    ws.cell(row_number, column).value
                    for column in range(1, 4)
                ]
                expected_inputs = [
                    record["month"],
                    record["quantity"],
                    record["unit_price"],
                ]
                if actual_inputs != expected_inputs:
                    problems.append(f"{row_number}행 입력 데이터 불일치")

            expected_values[f"D{total_row}"] = total
            expected_formulas[f"D{total_row}"] = (
                f"=SUM(D2:D{last_data_row})"
            )

            for address, expected in expected_values.items():
                actual = cached[address].value
                formula = ws[address].value

                numeric = (
                    isinstance(actual, (int, float))
                    and not isinstance(actual, bool)
                    and math.isfinite(actual)
                )
                value_ok = numeric and math.isclose(
                    actual,
                    float(expected),
                    rel_tol=1e-12,
                    abs_tol=1e-8,
                )
                formula_ok = (
                    ws[address].data_type == "f"
                    and formula == expected_formulas[address]
                )

                checks.append({
                    "cell": address,
                    "expected": str(expected),
                    "actual": actual,
                    "formula": formula,
                    "value_ok": value_ok,
                    "formula_ok": formula_ok,
                })

                if not value_ok:
                    problems.append(f"{address} 계산값 불일치")
                if not formula_ok:
                    problems.append(f"{address} 수식 불일치")

            formula_count = sum(
                cell.data_type == "f"
                for row in ws.iter_rows()
                for cell in row
            )
            if formula_count != len(records) + 1:
                problems.append("전체 수식 개수 불일치")

            chart_count = len(ws._charts)
            if chart_count != 1:
                problems.append("차트 개수가 1개가 아닙니다.")

            error_cells = [
                cell.coordinate
                for row in cached.iter_rows()
                for cell in row
                if cell.data_type == "e"
            ]
            if error_cells:
                problems.append(f"Excel 오류 셀 발견: {error_cells}")

            return {
                "passed": not problems,
                "problems": problems,
                "cells": checks,
                "formula_count": formula_count,
                "chart_count": chart_count,
                "visual_review": "미실시",
            }
        finally:
            values.close()
    finally:
        formulas.close()


def create_sales_workbook(sheet_name, source_note, records):
    """입력 검증부터 파일 생성·재계산·검증까지 실행한다."""
    output_root = ROOT / "outputs" / "sales"
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=output_root))
    workbook_path = run_dir / "sales.xlsx"

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "run_dir": str(run_dir),
        "workbook": str(workbook_path),
        "visual_review": "미실시",
        "model_used": False,
        "scope": "엑셀 도구 자체의 생성·재계산·자동 검증",
    }

    try:
        validate_input(sheet_name, source_note, records)

        write_json(run_dir / "input.json", {
            "sheet_name": sheet_name,
            "source_note": source_note,
            "records": records,
        })

        catalog, errors = discover_skills([
            ROOT / "vendor/anthropic-skills/skills/xlsx"
        ])
        if errors:
            raise ValueError(f"스킬 검사 실패: {errors}")

        skill = activate_skill(catalog, "xlsx")
        report["skill_sha256"] = skill["sha256"]

        recalc_script = Path(skill["base_dir"]) / "scripts/recalc.py"
        if not recalc_script.is_file():
            raise FileNotFoundError(recalc_script)

        # 소켓 제한이 있으면 보조 코드의 자동 우회 경로를 실행하지 않는다.
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM):
                pass
        except OSError as exc:
            raise RuntimeError(
                f"소켓 제한으로 재계산을 중단했습니다: {exc}"
            ) from exc

        print("[1/4] 엑셀 생성", flush=True)
        build_workbook(workbook_path, sheet_name, source_note, records)

        print("[2/4] 원본 recalc.py로 재계산", flush=True)
        result = subprocess.run(
            [
                sys.executable,
                str(recalc_script),
                str(workbook_path),
                "60",
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )

        (run_dir / "recalc-stdout.txt").write_text(
            result.stdout, encoding="utf-8"
        )
        (run_dir / "recalc-stderr.txt").write_text(
            result.stderr, encoding="utf-8"
        )

        report["recalc_returncode"] = result.returncode

        try:
            recalc_report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "재계산 출력이 JSON이 아닙니다. recalc 로그를 확인하세요."
            ) from exc

        report["recalc"] = recalc_report

        if (
            result.returncode != 0
            or not isinstance(recalc_report, dict)
            or "error" in recalc_report
            or recalc_report.get("status") != "success"
            or recalc_report.get("total_errors") != 0
        ):
            raise RuntimeError("재계산 실패 또는 수식 오류가 발견됐습니다.")

        print("[3/4] 입력값·수식·계산값·차트 존재 검증", flush=True)
        verification = verify_workbook(
            workbook_path, sheet_name, records
        )
        report["verification"] = verification

        if not verification["passed"]:
            raise RuntimeError(
                "; ".join(verification["problems"])
            )

        print("[4/4] markitdown으로 실제 파일 읽기", flush=True)
        converted = MarkItDown().convert(str(workbook_path))
        preview = converted.text_content

        if not preview or not preview.strip():
            raise RuntimeError("markitdown 변환 결과가 비어 있습니다.")

        (run_dir / "preview.md").write_text(
            preview, encoding="utf-8"
        )
        report["markitdown"] = {
            "status": "success",
            "text_length": len(preview),
        }
        report["status"] = "passed"

    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"

    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        write_json(run_dir / "result.json", report)

    return report


def main():
    parser = argparse.ArgumentParser(
        description="시험 데이터를 이용한 매출 엑셀 생성 및 검증"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "examples/sales-demo.json",
        help="sheet_name, source_note, records가 들어 있는 JSON 파일",
    )
    args = parser.parse_args()

    try:
        data = json.loads(args.input.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("입력 JSON은 객체여야 합니다.")
    except (OSError, ValueError) as exc:
        print(f"입력 파일 오류: {exc}", file=sys.stderr)
        return 1

    report = create_sales_workbook(
        sheet_name=data.get("sheet_name"),
        source_note=data.get("source_note"),
        records=data.get("records"),
    )

    print("\n실행 결과:")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n결과 폴더: {report['run_dir']}")

    if report["status"] == "passed":
        print("자동 검증 통과. Excel에서 차트와 표시 상태를 확인하세요.")
        return 0

    print("실행 실패. result.json과 재계산 로그를 확인하세요.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
