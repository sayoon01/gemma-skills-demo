"""B2 Deep Research Coordinator.

Coordinator의 연구 행동은 Python에 정의하지 않는다.

활성 Agent Skill의 SKILL.md와
runtime/b2/controller.md를 읽어 Gemma4에 전달하고,
사용자 요청을 병렬 조사 가능한 Assignment로 분해한다.

이 단계에서는 실제 웹 조사나 Worker 실행을 수행하지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.ollama_client import OllamaClient
from src.skill_loader import (
    DEFAULT_SEARCH_ROOTS,
    activate_skill,
    discover_skills,
)

from .contracts import load_b2_contracts
from .worker import extract_json_object


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


def sha256_text(
    text: str,
) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def load_request(
    *,
    request_path: Path | None,
    topic: str | None,
) -> tuple[str, dict[str, Any]]:
    if topic is not None:
        value = topic.strip()

        if not value:
            raise ValueError(
                "--topic이 비어 있습니다."
            )

        return (
            value,
            {
                "type": "topic",
                "value": value,
            },
        )

    if request_path is None:
        raise ValueError(
            "request 또는 topic이 필요합니다."
        )

    path = request_path.resolve()

    if not path.is_file():
        raise FileNotFoundError(
            f"요청 파일이 없습니다: {path}"
        )

    value = path.read_text(
        encoding="utf-8-sig"
    ).strip()

    if not value:
        raise ValueError(
            "요청 파일이 비어 있습니다."
        )

    return (
        value,
        {
            "type": "file",
            "path": str(path),
        },
    )


def build_system_prompt(
    *,
    skill: dict[str, Any],
    controller_contract: str,
) -> str:
    return (
        "# Active Agent Skill\n\n"
        "The following is the active public Agent Skill. "
        "It is the primary research behavior specification.\n\n"
        "<skill>\n"
        + skill["body"]
        + "\n</skill>\n\n"
        "# Runtime Controller Contract\n\n"
        + controller_contract
    )


def build_user_prompt(
    *,
    request_text: str,
    max_workers: int,
    current_date: str,
) -> str:
    return (
        "# User Research Request\n\n"
        + request_text
        + "\n\n"
        "# Runtime Context\n\n"
        + f"- Current date: {current_date}\n"
        + "\n"
        + "# Runtime Limits\n\n"
        + f"- Maximum assignments in this wave: {max_workers}\n"
        + "- This is planning only.\n"
        + "- Do not perform research in this response.\n"
        + "- Do not provide research findings yet.\n"
        + "- Do not invent sources or URLs.\n"
        + "- Return the planning JSON required by the controller contract.\n"
    )


def validate_plan(
    plan: dict[str, Any],
    *,
    max_workers: int,
) -> dict[str, Any]:
    errors: list[str] = []

    wave = plan.get("wave")

    if wave != 1:
        errors.append(
            f"wave는 1이어야 합니다: {wave!r}"
        )

    assignments = (
        plan.get("assignments")
    )

    if not isinstance(
        assignments,
        list,
    ):
        errors.append(
            "assignments가 list가 아닙니다."
        )

        return {
            "ok": False,
            "errors": errors,
            "assignment_count": 0,
        }

    if not assignments:
        errors.append(
            "assignment가 하나도 없습니다."
        )

    if len(assignments) > max_workers:
        errors.append(
            "assignment 수가 max_workers를 초과했습니다: "
            f"{len(assignments)} > {max_workers}"
        )

    seen_ids: set[str] = set()

    for index, assignment in enumerate(
        assignments,
        1,
    ):
        prefix = f"assignments[{index}]"

        if not isinstance(
            assignment,
            dict,
        ):
            errors.append(
                f"{prefix}가 객체가 아닙니다."
            )
            continue

        assignment_id = (
            assignment.get(
                "assignment_id"
            )
        )

        if not isinstance(
            assignment_id,
            str,
        ) or not assignment_id.strip():
            errors.append(
                f"{prefix}.assignment_id가 비어 있습니다."
            )
        elif assignment_id in seen_ids:
            errors.append(
                f"중복 assignment_id: {assignment_id}"
            )
        else:
            seen_ids.add(
                assignment_id
            )

        for field in (
            "title",
            "objective",
        ):
            value = assignment.get(
                field
            )

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                errors.append(
                    f"{prefix}.{field}가 비어 있습니다."
                )

        queries = assignment.get(
            "queries"
        )

        if (
            not isinstance(
                queries,
                list,
            )
            or not queries
        ):
            errors.append(
                f"{prefix}.queries가 비어 있습니다."
            )
        else:
            for query_index, query in enumerate(
                queries,
                1,
            ):
                if (
                    not isinstance(
                        query,
                        str,
                    )
                    or not query.strip()
                ):
                    errors.append(
                        f"{prefix}.queries[{query_index}]가 "
                        "유효한 문자열이 아닙니다."
                    )

        source_priority = assignment.get(
            "source_priority"
        )

        if not isinstance(
            source_priority,
            list,
        ):
            errors.append(
                f"{prefix}.source_priority가 list가 아닙니다."
            )
        else:
            for source_index, source_type in enumerate(
                source_priority,
                1,
            ):
                if (
                    not isinstance(
                        source_type,
                        str,
                    )
                    or not source_type.strip()
                ):
                    errors.append(
                        f"{prefix}.source_priority"
                        f"[{source_index}]가 "
                        "유효한 문자열이 아닙니다."
                    )

        needs_local_files = assignment.get(
            "needs_local_files"
        )

        if not isinstance(
            needs_local_files,
            bool,
        ):
            errors.append(
                f"{prefix}.needs_local_files가 bool이 아닙니다."
            )

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "assignment_count":
            len(assignments),
        "assignment_ids":
            [
                assignment.get(
                    "assignment_id"
                )
                for assignment
                in assignments
                if isinstance(
                    assignment,
                    dict,
                )
            ],
    }


def run_coordinator(
    *,
    request_text: str,
    request_source: dict[str, Any],
    skill_name: str,
    max_workers: int,
    output_root: Path,
) -> dict[str, Any]:
    if not 1 <= max_workers <= 5:
        raise ValueError(
            "max_workers는 1~5여야 합니다."
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

    controller_contract = (
        contracts["controller"]
    )

    system_prompt = (
        build_system_prompt(
            skill=skill,
            controller_contract=
                controller_contract,
        )
    )

    current_date = (
        datetime.now(
            timezone.utc
        ).date().isoformat()
    )

    user_prompt = (
        build_user_prompt(
            request_text=request_text,
            max_workers=max_workers,
            current_date=current_date,
        )
    )

    client = OllamaClient()

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="plan-",
            dir=output_root,
        )
    )

    (
        run_dir
        / "request.md"
    ).write_text(
        request_text + "\n",
        encoding="utf-8",
    )

    (
        run_dir
        / "system-prompt.md"
    ).write_text(
        system_prompt + "\n",
        encoding="utf-8",
    )

    (
        run_dir
        / "user-prompt.md"
    ).write_text(
        user_prompt + "\n",
        encoding="utf-8",
    )

    config = {
        "stage": "B2-3",
        "created_at":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "model":
            client.model,
        "skill":
            skill["name"],
        "skill_sha256":
            skill["sha256"],
        "controller_contract_sha256":
            sha256_text(
                controller_contract
            ),
        "request_source":
            request_source,
        "max_workers":
            max_workers,
        "current_date":
            current_date,
        "discovery_errors":
            discovery_errors,
    }

    save_json(
        run_dir
        / "run-config.json",
        config,
    )

    messages = [
        {
            "role": "system",
            "content":
                system_prompt,
        },
        {
            "role": "user",
            "content":
                user_prompt,
        },
    ]

    print(
        "===== B2 Coordinator Planning =====",
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
        "Max workers:",
        max_workers,
        flush=True,
    )

    started = (
        time.monotonic()
    )

    response = client.chat(
        messages
    )

    elapsed = (
        time.monotonic()
        - started
    )

    save_json(
        run_dir
        / "response.json",
        response,
    )

    raw_text = (
        response["message"]
        .get("content")
        or ""
    )

    (
        run_dir
        / "plan-raw.txt"
    ).write_text(
        raw_text,
        encoding="utf-8",
    )

    try:
        plan = extract_json_object(
            raw_text
        )

    except Exception as exc:
        result = {
            **config,
            "status":
                "parse_failed",
            "elapsed_seconds":
                round(
                    elapsed,
                    3,
                ),
            "error":
                f"{type(exc).__name__}: {exc}",
        }

        save_json(
            run_dir
            / "result.json",
            result,
        )

        print()
        print(
            "Plan JSON parse 실패:",
            result["error"],
            flush=True,
        )

        raise

    validation = validate_plan(
        plan,
        max_workers=max_workers,
    )

    save_json(
        run_dir
        / "plan.json",
        plan,
    )

    save_json(
        run_dir
        / "plan-validation.json",
        validation,
    )

    result = {
        **config,
        "status":
            (
                "completed"
                if validation["ok"]
                else "invalid_plan"
            ),
        "elapsed_seconds":
            round(
                elapsed,
                3,
            ),
        "plan":
            plan,
        "validation":
            validation,
    }

    save_json(
        run_dir
        / "result.json",
        result,
    )

    print()
    print(
        "Coordinator time:",
        f"{elapsed:.3f}초",
        flush=True,
    )

    print(
        "Plan validation:",
        validation["ok"],
        flush=True,
    )

    print(
        "Assignments:",
        validation[
            "assignment_count"
        ],
        flush=True,
    )

    print()

    for assignment in (
        plan.get("assignments")
        or []
    ):
        print(
            assignment.get(
                "assignment_id"
            ),
            "-",
            assignment.get(
                "title"
            ),
            flush=True,
        )

        print(
            " objective:",
            assignment.get(
                "objective"
            ),
            flush=True,
        )

        print(
            " local files:",
            assignment.get(
                "needs_local_files"
            ),
            flush=True,
        )

        print()

    if validation["errors"]:
        print(
            "===== PLAN ERRORS =====",
            flush=True,
        )

        for error in validation[
            "errors"
        ]:
            print(
                "-",
                error,
                flush=True,
            )

    print(
        "Plan:",
        run_dir / "plan.json",
        flush=True,
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    request_group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    request_group.add_argument(
        "--request",
        type=Path,
    )

    request_group.add_argument(
        "--topic",
        type=str,
    )

    parser.add_argument(
        "--skill",
        default="deep-research",
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        default=(
            ROOT
            / "outputs"
            / "research-b2"
            / "coordinator-smoke"
        ),
    )

    args = parser.parse_args()

    request_text, request_source = (
        load_request(
            request_path=
                args.request,
            topic=
                args.topic,
        )
    )

    run_coordinator(
        request_text=request_text,
        request_source=
            request_source,
        skill_name=
            args.skill,
        max_workers=
            args.max_workers,
        output_root=
            args.output_root,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
