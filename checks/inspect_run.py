"""저장된 실행 기록의 크기와 모델 처리 토큰을 확인한다."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    run_dir = args.run_dir
    messages = json.loads(
        (run_dir / "messages.json").read_text(encoding="utf-8")
    )

    print("메시지별 크기")
    for index, message in enumerate(messages, start=1):
        content = message.get("content") or ""
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)

        print(
            f"{index}: role={message.get('role')} / "
            f"content={len(content):,}자 / "
            f"tool_calls={len(message.get('tool_calls') or [])}개"
        )

    request_path = run_dir / "request.md"
    print("\n실제 요청 문서")
    print(request_path.read_text(encoding="utf-8"))

    response_paths = sorted(
        run_dir.glob("response-*.json"),
        key=lambda path: int(path.stem.split("-")[-1]),
    )

    print("\n모델 응답별 처리 정보")
    for path in response_paths:
        response = json.loads(path.read_text(encoding="utf-8"))
        message = response.get("message") or {}

        print(json.dumps({
            "file": path.name,
            "prompt_eval_count": response.get("prompt_eval_count"),
            "eval_count": response.get("eval_count"),
            "done_reason": response.get("done_reason"),
            "answer_chars": len(message.get("content") or ""),
            "tool_call_count": len(message.get("tool_calls") or []),
        }, ensure_ascii=False))

    print(
        "\n주의: 문자 수와 처리 토큰 수만으로 "
        "컨텍스트 잘림 여부를 확정할 수는 없습니다."
    )


if __name__ == "__main__":
    main()
