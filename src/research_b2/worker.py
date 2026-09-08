"""B2 독립 Gemma4 Research Worker.

Worker의 행동 규칙은 Python 코드가 아니라
runtime/b2/worker.md 및 evidence-policy.md에서 로드한다.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from src.ollama_client import OllamaClient
from src.skill_loader import (
    DEFAULT_SEARCH_ROOTS,
    activate_skill,
    discover_skills,
)

from .contracts import load_b2_contracts
from .tools import ToolRuntime


ROOT = Path(__file__).resolve().parents[2]


def save_json(
    path: Path,
    data: Any,
) -> None:
    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )


def canonical_url(
    url: str,
) -> str:
    value = (
        url
        or ""
    ).strip()

    if not value:
        return ""

    parts = urlsplit(value)

    path = parts.path

    if path != "/":
        path = path.rstrip("/")

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            parts.query,
            "",
        )
    )


def _repair_invalid_json_escapes(
    value: str,
) -> str:
    r"""JSON string 안의 비표준 단일 backslash만 보정한다.

    예:
    \pi  -> \\pi
    \_   -> \\_

    JSON 표준 escape는 그대로 둔다:
    \", \\, \/, \b, \f, \n, \r, \t, \u
    """

    return re.sub(
        r'\\(?!["\\/bfnrtu])',
        r'\\\\',
        value,
    )


def _load_json_object(
    value: str,
) -> dict[str, Any]:
    """일반 JSON parse 후 escape 오류만 보정해 한 번 재시도한다."""

    try:
        parsed = json.loads(
            value
        )

    except json.JSONDecodeError:
        repaired = (
            _repair_invalid_json_escapes(
                value
            )
        )

        parsed = json.loads(
            repaired,
            strict=False,
        )

    if not isinstance(
        parsed,
        dict,
    ):
        raise ValueError(
            "Worker JSON 최상위는 객체여야 합니다."
        )

    return parsed


def extract_json_object(
    text: str,
) -> dict[str, Any]:
    """Gemma 응답에서 JSON object를 추출한다."""

    value = (
        text
        or ""
    ).strip()

    if not value:
        raise ValueError(
            "Worker 최종 응답이 비어 있습니다."
        )

    if value.startswith("```"):
        value = re.sub(
            r"^```(?:json)?\s*",
            "",
            value,
            flags=re.IGNORECASE,
        )

        value = re.sub(
            r"\s*```$",
            "",
            value,
        )

        value = value.strip()

    try:
        return _load_json_object(
            value
        )

    except (
        json.JSONDecodeError,
        ValueError,
    ):
        pass

    start = value.find("{")
    end = value.rfind("}")

    if (
        start >= 0
        and end > start
    ):
        candidate = value[
            start:end + 1
        ]

        return _load_json_object(
            candidate
        )

    raise ValueError(
        "Worker 최종 응답에서 "
        "JSON 객체를 찾지 못했습니다."
    )


def collect_worker_source_urls(
    worker_result: dict[str, Any],
) -> list[str]:
    urls: list[str] = []

    claims = (
        worker_result.get("claims")
        or []
    )

    if not isinstance(
        claims,
        list,
    ):
        return urls

    for claim in claims:
        if not isinstance(
            claim,
            dict,
        ):
            continue

        sources = (
            claim.get("sources")
            or []
        )

        if not isinstance(
            sources,
            list,
        ):
            continue

        for source in sources:
            if not isinstance(
                source,
                dict,
            ):
                continue

            if (
                source.get("source_kind")
                != "web"
            ):
                continue

            url = (
                source.get("url")
                or ""
            ).strip()

            if url:
                urls.append(url)

    return urls


def collect_successful_fetch_urls(
    tool_logs: list[dict[str, Any]],
) -> set[str]:
    urls: set[str] = set()

    for log in tool_logs:
        if log.get("name") != "fetch_page":
            continue

        if log.get("ok") is not True:
            continue

        arguments = (
            log.get("arguments")
            or {}
        )

        requested_url = (
            arguments.get("url")
            or ""
        )

        if requested_url:
            urls.add(
                canonical_url(
                    requested_url
                )
            )

        result = (
            log.get("result")
            or {}
        )

        data = (
            result.get("data")
            or {}
        )

        final_url = (
            data.get("url")
            or ""
        )

        if final_url:
            urls.add(
                canonical_url(
                    final_url
                )
            )

    return urls


def verify_worker_sources(
    worker_result: dict[str, Any],
    tool_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    cited_urls = (
        collect_worker_source_urls(
            worker_result
        )
    )

    fetched_urls = (
        collect_successful_fetch_urls(
            tool_logs
        )
    )

    verified: list[str] = []
    unverified: list[str] = []

    for url in cited_urls:
        canonical = canonical_url(
            url
        )

        if canonical in fetched_urls:
            verified.append(url)
        else:
            unverified.append(url)

    return {
        "worker_web_source_count":
            len(cited_urls),
        "verified_web_source_count":
            len(verified),
        "unverified_web_source_count":
            len(unverified),
        "verified_urls":
            verified,
        "unverified_urls":
            unverified,
        "all_worker_web_sources_verified":
            len(unverified) == 0,
    }


def build_worker_system_prompt(
    contracts: dict[str, str],
) -> str:
    return (
        contracts["worker"]
        + "\n\n"
        + contracts["evidence-policy"]
    )


def run_worker(
    *,
    assignment: str,
    skill_name: str = "deep-research",
    max_turns: int = 6,
    output_root: Path | None = None,
) -> dict[str, Any]:
    if not assignment.strip():
        raise ValueError(
            "assignment가 비어 있습니다."
        )

    if not 1 <= max_turns <= 20:
        raise ValueError(
            "max_turns는 1~20이어야 합니다."
        )

    catalog, discovery_errors = (
        discover_skills(
            DEFAULT_SEARCH_ROOTS
        )
    )

    skill = activate_skill(
        catalog,
        skill_name,
    )

    contracts = load_b2_contracts()

    client = OllamaClient()

    tools = ToolRuntime()

    if output_root is None:
        output_root = (
            ROOT
            / "outputs"
            / "research-b2"
            / "worker-smoke"
        )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="run-",
            dir=output_root,
        )
    )

    messages = [
        {
            "role": "system",
            "content":
                build_worker_system_prompt(
                    contracts
                ),
        },
        {
            "role": "user",
            "content": (
                "# Research Assignment\n\n"
                + assignment.strip()
            ),
        },
    ]

    started = time.monotonic()

    tool_logs: list[
        dict[str, Any]
    ] = []

    model_times: list[float] = []

    final_text = ""

    print(
        "===== B2 Independent Worker =====",
        flush=True,
    )

    print(
        "Run:",
        run_dir,
        flush=True,
    )

    print(
        "Model:",
        client.model,
        flush=True,
    )

    print(
        "Skill:",
        skill["name"],
        flush=True,
    )

    print(
        "Skill SHA:",
        skill["sha256"],
        flush=True,
    )

    print(
        "Assignment:",
        assignment,
        flush=True,
    )

    for turn in range(
        1,
        max_turns + 1,
    ):
        print(
            f"\n[{turn}/{max_turns}] "
            "Worker 모델 응답 대기",
            flush=True,
        )

        model_started = (
            time.monotonic()
        )

        response = client.chat(
            messages,
            tools=tools.schemas,
        )

        model_elapsed = (
            time.monotonic()
            - model_started
        )

        model_times.append(
            model_elapsed
        )

        print(
            "Worker 모델 응답 시간:",
            f"{model_elapsed:.3f}초",
            flush=True,
        )

        response[
            "_runtime"
        ] = {
            "turn": turn,
            "model_elapsed_seconds":
                round(
                    model_elapsed,
                    3,
                ),
        }

        save_json(
            run_dir
            / f"response-{turn}.json",
            response,
        )

        message = response["message"]

        messages.append(
            message
        )

        calls = (
            message.get("tool_calls")
            or []
        )

        if not calls:
            final_text = (
                message.get("content")
                or ""
            )

            print(
                "Worker 최종 응답 수신",
                flush=True,
            )

            break

        for call in calls:
            function = (
                call.get("function")
                or {}
            )

            name = function.get(
                "name"
            )

            arguments = (
                function.get(
                    "arguments"
                )
                or {}
            )

            if isinstance(
                arguments,
                str,
            ):
                arguments = (
                    json.loads(
                        arguments
                    )
                )

            print(
                "Tool 실행:",
                name,
                "/",
                arguments,
                flush=True,
            )

            tool_started = (
                time.monotonic()
            )

            ok = True
            error = None

            try:
                data = tools.execute(
                    name,
                    arguments,
                )

                tool_result = {
                    "ok": True,
                    "data": data,
                }

            except Exception as exc:
                ok = False

                error = (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

                tool_result = {
                    "ok": False,
                    "error": error,
                }

            tool_elapsed = (
                time.monotonic()
                - tool_started
            )

            tool_logs.append(
                {
                    "turn": turn,
                    "name": name,
                    "arguments":
                        arguments,
                    "ok": ok,
                    "error": error,
                    "elapsed_seconds":
                        round(
                            tool_elapsed,
                            3,
                        ),
                    "result":
                        tool_result,
                }
            )

            messages.append(
                {
                    "role": "tool",
                    "content":
                        json.dumps(
                            tool_result,
                            ensure_ascii=False,
                            default=str,
                        ),
                }
            )

        save_json(
            run_dir
            / "tool-calls.json",
            tool_logs,
        )

        save_json(
            run_dir
            / "messages.json",
            messages,
        )

    if not final_text:
        raise RuntimeError(
            "Worker가 max_turns 내에 "
            "최종 응답을 만들지 못했습니다."
        )

    (
        run_dir
        / "worker-final-raw.txt"
    ).write_text(
        final_text,
        encoding="utf-8",
    )

    worker_result = (
        extract_json_object(
            final_text
        )
    )

    verification = (
        verify_worker_sources(
            worker_result,
            tool_logs,
        )
    )

    elapsed = (
        time.monotonic()
        - started
    )

    search_count = sum(
        1
        for log in tool_logs
        if (
            log["name"]
            == "web_search"
        )
    )

    fetch_count = sum(
        1
        for log in tool_logs
        if (
            log["name"]
            == "fetch_page"
        )
    )

    fetch_success_count = sum(
        1
        for log in tool_logs
        if (
            log["name"]
            == "fetch_page"
            and log["ok"]
        )
    )

    result = {
        "status": "completed",
        "stage": "B2-2B",
        "created_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "run_dir":
            str(run_dir),
        "model":
            client.model,
        "skill":
            skill["name"],
        "skill_sha256":
            skill["sha256"],
        "assignment":
            assignment,
        "discovery_errors":
            discovery_errors,
        "worker_result":
            worker_result,
        "verification":
            verification,
        "metrics": {
            "turn_count":
                len(model_times),
            "tool_call_count":
                len(tool_logs),
            "search_count":
                search_count,
            "fetch_count":
                fetch_count,
            "fetch_success_count":
                fetch_success_count,
            "model_response_times_seconds":
                [
                    round(
                        value,
                        3,
                    )
                    for value
                    in model_times
                ],
            "model_total_seconds":
                round(
                    sum(
                        model_times
                    ),
                    3,
                ),
            "elapsed_seconds":
                round(
                    elapsed,
                    3,
                ),
        },
    }

    save_json(
        run_dir
        / "result.json",
        result,
    )

    save_json(
        run_dir
        / "worker-result.json",
        worker_result,
    )

    (
        run_dir
        / "assignment.md"
    ).write_text(
        assignment.strip()
        + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "===== Worker Result =====",
        flush=True,
    )

    print(
        "Turns:",
        result["metrics"][
            "turn_count"
        ],
        flush=True,
    )

    print(
        "Tool calls:",
        result["metrics"][
            "tool_call_count"
        ],
        flush=True,
    )

    print(
        "Search:",
        search_count,
        flush=True,
    )

    print(
        "Fetch:",
        fetch_count,
        flush=True,
    )

    print(
        "Fetch success:",
        fetch_success_count,
        flush=True,
    )

    print(
        "Worker web sources:",
        verification[
            "worker_web_source_count"
        ],
        flush=True,
    )

    print(
        "Verified web sources:",
        verification[
            "verified_web_source_count"
        ],
        flush=True,
    )

    print(
        "Unverified web sources:",
        verification[
            "unverified_web_source_count"
        ],
        flush=True,
    )

    print(
        "Result:",
        run_dir
        / "result.json",
        flush=True,
    )

    return result


def main() -> int:
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--assignment",
        required=True,
        help=(
            "Worker 하나가 독립적으로 "
            "조사할 Sub-goal"
        ),
    )

    parser.add_argument(
        "--skill",
        default="deep-research",
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=6,
    )

    args = parser.parse_args()

    run_worker(
        assignment=args.assignment,
        skill_name=args.skill,
        max_turns=args.max_turns,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
