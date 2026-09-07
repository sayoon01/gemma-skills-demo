"""스킬 로더와 Gemma 연결을 확인하고 요청·응답을 저장한다."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from src.ollama_client import OllamaClient
from src.skill_loader import activate_skill, discover_skills

ROOT = Path(__file__).resolve().parents[1]


def main():
    skill_root = ROOT / "vendor/anthropic-skills/skills/xlsx"
    catalog, errors = discover_skills([skill_root])

    if errors:
        raise RuntimeError(
            json.dumps(errors, ensure_ascii=False)
        )

    skill = activate_skill(catalog, "xlsx")
    client = OllamaClient()

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = ROOT / "outputs" / "skill-prompt" / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)

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
                "이번 요청은 작업 계획 작성만 수행합니다.\n"
                "파일 읽기, 코드 실행, 파일 저장 도구는 제공되지 않았습니다.\n"
                "파일을 생성하거나 검증했다고 주장하지 마세요."
            ),
        },
        {
            "role": "user",
            "content": (
                "시험용 월별 매출 엑셀을 만들 계획입니다.\n"
                "1월: 수량 10, 단가 1000원\n"
                "2월: 수량 20, 단가 1500원\n"
                "3월: 수량 15, 단가 2000원\n"
                "행별 금액, 총합, 월별 막대그래프가 필요합니다.\n"
                "xlsx 스킬에 따라 사용할 수식, 재계산 방법, "
                "검증 항목을 간결하게 설명하세요.\n"
                "지금은 계획만 작성하세요."
            ),
        },
    ]

    request_record = {
        "model": client.model,
        "skill": skill["name"],
        "skill_sha256": skill["sha256"],
        "messages": messages,
    }

    (run_dir / "request.json").write_text(
        json.dumps(request_record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    started = time.monotonic()
    print(f"모델: {client.model}", flush=True)
    print(f"스킬: {skill['name']}", flush=True)
    print("Gemma 응답 대기 중", flush=True)

    try:
        response = client.chat(messages)
        answer = response["message"].get("content", "")

        (run_dir / "response.json").write_text(
            json.dumps(response, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (run_dir / "answer.md").write_text(
            answer,
            encoding="utf-8",
        )

        complete = (
            bool(answer.strip())
            and response.get("done") is True
            and response.get("done_reason") == "stop"
        )

        result = {
            "status": "response_received" if complete else "needs_review",
            "elapsed_seconds": round(time.monotonic() - started, 2),
            "skill": skill["name"],
            "skill_sha256": skill["sha256"],
            "done_reason": response.get("done_reason"),
            "scope": "스킬 본문 전달 및 모델 응답 수신",
            "content_quality_reviewed": False,
            "file_generation_tested": False,
        }

        print("\nGemma 답변:\n")
        print(answer or "(빈 답변)")

    except Exception as exc:
        result = {
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
        }
        complete = False
        print("실패:", result["error"])

    (run_dir / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n실행 기록: {run_dir}")
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
