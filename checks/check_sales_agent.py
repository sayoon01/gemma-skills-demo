"""Gemma가 매출 엑셀 도구를 호출하는 전체 흐름을 검증한다."""

import argparse
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.ollama_client import OllamaClient
from src.skill_loader import activate_skill, discover_skills
from src.tools.sales_workbook import create_sales_workbook

ROOT = Path(__file__).resolve().parents[1]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_sales_workbook",
            "description": (
                "입력된 월별 수량과 단가로 Excel 파일을 생성합니다. "
                "금액과 합계를 수식으로 작성하고 막대그래프를 추가합니다. "
                "LibreOffice로 재계산한 뒤 계산값과 수식을 검증합니다. "
                "실행 결과에 실제 파일 경로와 검증 상태가 포함됩니다."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sheet_name": {
                        "type": "string",
                        "description": "사용자가 지정한 시트 이름",
                    },
                    "source_note": {
                        "type": "string",
                        "description": "사용자가 제공한 데이터 출처 설명",
                    },
                    "records": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 1000,
                        "items": {
                            "type": "object",
                            "properties": {
                                "month": {"type": "string"},
                                "quantity": {"type": "number"},
                                "unit_price": {"type": "number"},
                            },
                            "required": [
                                "month",
                                "quantity",
                                "unit_price",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "sheet_name",
                    "source_note",
                    "records",
                ],
                "additionalProperties": False,
            },
        },
    }
]


def save_json(path, value):
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Gemma의 매출 엑셀 도구 호출 시험"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "examples/sales-demo.json",
    )
    args = parser.parse_args()

    output_root = ROOT / "outputs" / "sales-agent"
    output_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="run-", dir=output_root))

    messages = []
    executions = []
    final_answer = ""
    final_complete = False

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "failed",
        "model_used": True,
        "visual_review": "미실시",
        "scope": "Gemma 도구 요청부터 엑셀 생성·재계산·검증까지",
        "run_dir": str(run_dir),
    }

    try:
        source_data = json.loads(
            args.input.read_text(encoding="utf-8-sig")
        )
        if not isinstance(source_data, dict):
            raise ValueError("입력 JSON은 객체여야 합니다.")

        required_keys = {"sheet_name", "source_note", "records"}
        if set(source_data) != required_keys:
            raise ValueError(
                "입력 JSON에는 sheet_name, source_note, records가 필요합니다."
            )

        save_json(run_dir / "input.json", source_data)

        catalog, errors = discover_skills([
            ROOT / "vendor/anthropic-skills/skills/xlsx"
        ])
        if errors:
            raise ValueError(f"스킬 검사 실패: {errors}")

        skill = activate_skill(catalog, "xlsx")
        client = OllamaClient()

        report["model"] = client.model
        report["skill"] = skill["name"]
        report["skill_sha256"] = skill["sha256"]

        messages = [
            {
                "role": "system",
                "content": (
                    "한국어로 답변하세요.\n"
                    "사용자가 xlsx 스킬을 명시적으로 선택했습니다.\n"
                    f"스킬 기준 경로: {skill['base_dir']}\n"
                    "<skill>\n"
                    f"{skill['body']}\n"
                    "</skill>\n"
                    "이번 작업은 제공된 create_sales_workbook 도구로 "
                    "실제 엑셀 파일을 생성하는 것입니다.\n"
                    "도구는 파일 생성, 재계산, 자동 검증을 수행합니다.\n"
                    "사용자의 입력 데이터와 출처 설명을 그대로 전달하세요.\n"
                    "도구를 한 번 호출하고, 반환 결과를 확인한 후 답변하세요.\n"
                    "status가 passed일 때만 자동 검증 성공이라고 보고하세요.\n"
                    "실제 반환된 workbook 경로를 최종 답변에 포함하세요.\n"
                    "Excel 화면을 직접 확인했다고 주장하지 마세요."
                ),
            },
            {
                "role": "user",
                "content": (
                    "아래 데이터로 수식과 월별 막대그래프를 포함한 "
                    "엑셀 파일을 실제로 생성하고 검증해 주세요.\n"
                    "시트 이름, 데이터, 출처 설명을 변경하지 마세요.\n"
                    + json.dumps(source_data, ensure_ascii=False, indent=2)
                ),
            },
        ]

        save_json(run_dir / "request.json", {
            "model": client.model,
            "skill_sha256": skill["sha256"],
            "messages": messages,
            "tools": TOOLS,
        })

        print(f"모델: {client.model}", flush=True)
        print(f"실행 기록: {run_dir}", flush=True)

        for turn in range(1, 5):
            print(f"\n[{turn}/4] Gemma 응답 대기", flush=True)
            response = client.chat(messages, tools=TOOLS)

            save_json(run_dir / f"response-{turn}.json", response)

            message = response["message"]
            calls = message.get("tool_calls") or []
            messages.append(message)

            if not calls:
                final_answer = message.get("content") or ""
                final_complete = (
                    bool(final_answer.strip())
                    and response.get("done") is True
                    and response.get("done_reason") == "stop"
                )
                report["done_reason"] = response.get("done_reason")
                break

            if executions:
                raise RuntimeError(
                    "이미 도구를 실행했는데 추가 실행을 요청했습니다. "
                    "중복 파일 생성을 막기 위해 중단합니다."
                )

            if len(calls) != 1:
                raise RuntimeError("이번 시험은 도구 호출 한 개만 허용합니다.")

            function = calls[0]["function"]
            name = function["name"]
            arguments = function.get("arguments", {})

            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            if name != "create_sales_workbook":
                raise ValueError(f"등록되지 않은 도구: {name}")

            if not isinstance(arguments, dict):
                raise ValueError("도구 인자는 객체여야 합니다.")

            # 모델이 입력을 누락하거나 임의 변경했는지 검사합니다.
            if arguments != source_data:
                save_json(run_dir / "rejected-arguments.json", arguments)
                raise ValueError(
                    "모델이 요청한 도구 인자가 원본 입력과 다릅니다. "
                    "파일을 생성하지 않았습니다."
                )

            print(f"실제 도구 실행: {name}", flush=True)
            tool_result = create_sales_workbook(**arguments)

            executions.append({
                "name": name,
                "arguments": arguments,
                "result": tool_result,
            })
            save_json(run_dir / "tool-executions.json", executions)

            messages.append({
                "role": "tool",
                "tool_name": name,
                "content": json.dumps(tool_result, ensure_ascii=False),
            })

        else:
            raise RuntimeError("4회 안에 최종 답변이 완료되지 않았습니다.")

        tool_passed = (
            len(executions) == 1
            and executions[0]["result"].get("status") == "passed"
        )

        workbook = (
            executions[0]["result"].get("workbook")
            if executions else None
        )
        path_reflected = bool(workbook and workbook in final_answer)

        report.update({
            "tool_execution_count": len(executions),
            "tool_passed": tool_passed,
            "final_response_complete": final_complete,
            "workbook_path_in_answer": path_reflected,
            "workbook": workbook,
            "status": (
                "passed"
                if tool_passed and final_complete and path_reflected
                else "needs_review"
            ),
        })

        print("\nGemma 최종 답변:\n")
        print(final_answer or "(빈 답변)")

    except Exception as exc:
        report["status"] = "failed"
        report["error"] = f"{type(exc).__name__}: {exc}"
        print("\n실행 실패:", report["error"])

    finally:
        report["finished_at"] = datetime.now(timezone.utc).isoformat()
        report["tool_execution_count"] = len(executions)

        save_json(run_dir / "messages.json", messages)
        save_json(run_dir / "tool-executions.json", executions)
        save_json(run_dir / "result.json", report)
        (run_dir / "answer.md").write_text(
            final_answer, encoding="utf-8"
        )

    print("\n최종 검사 결과:")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n실행 기록: {run_dir}")

    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
