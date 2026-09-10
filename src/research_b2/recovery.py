"""B2 failed-worker sequential recovery runtime.

Parallel Worker batch에서 실패한 assignment만 골라
같은 assignment를 독립 Worker context로 한 번씩 순차 재실행한다.

연구 주제나 deep-research workflow는 이 파일에 하드코딩하지 않는다.

Output:
    <batch>/recovery/<assignment_id>/run-*/
    <batch>/recovery/recovery-index.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .parallel_workers import (
    build_worker_assignment,
)
from .worker import run_worker


def load_json(
    path: Path,
) -> Any:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def save_json(
    path: Path,
    data: Any,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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


def run_recovery(
    *,
    batch_dir: Path,
    skill_name: str | None = None,
    max_turns: int | None = None,
    input_dir: Path | None = None,
) -> dict[str, Any]:
    """실패한 Parallel Worker만 순차적으로 한 번 재실행한다."""

    batch_dir = (
        Path(
            batch_dir
        )
        .expanduser()
        .resolve()
    )

    parallel_path = (
        batch_dir
        / "parallel-result.json"
    )

    if not parallel_path.is_file():
        raise FileNotFoundError(
            "parallel-result.json을 찾지 못했습니다: "
            f"{parallel_path}"
        )

    parallel = load_json(
        parallel_path
    )

    raw_plan_path = (
        parallel.get(
            "plan_path"
        )
        or ""
    )

    if not raw_plan_path:
        raise ValueError(
            "parallel-result.json에 plan_path가 없습니다."
        )

    plan_path = (
        Path(
            raw_plan_path
        )
        .expanduser()
        .resolve()
    )

    if not plan_path.is_file():
        raise FileNotFoundError(
            "원본 plan을 찾지 못했습니다: "
            f"{plan_path}"
        )

    plan = load_json(
        plan_path
    )

    assignments = (
        plan.get(
            "assignments"
        )
        or []
    )

    assignment_index = {
        assignment.get(
            "assignment_id"
        ):
            assignment
        for assignment
        in assignments
        if (
            isinstance(
                assignment,
                dict,
            )
            and assignment.get(
                "assignment_id"
            )
        )
    }

    failed_workers = [
        worker
        for worker in (
            parallel.get(
                "workers"
            )
            or []
        )
        if (
            worker.get(
                "status"
            )
            != "completed"
        )
    ]

    effective_skill = (
        skill_name
        or parallel.get(
            "skill"
        )
        or "deep-research"
    )

    effective_max_turns = (
        max_turns
        if max_turns is not None
        else int(
            parallel.get(
                "max_turns"
            )
            or 6
        )
    )

    if not 1 <= effective_max_turns <= 20:
        raise ValueError(
            "max_turns는 1~20이어야 합니다."
        )

    if input_dir is not None:
        input_dir = (
            Path(
                input_dir
            )
            .expanduser()
            .resolve()
        )

        if not input_dir.is_dir():
            raise ValueError(
                "input_dir가 존재하는 디렉터리가 아닙니다: "
                f"{input_dir}"
            )

    #
    # 실패한 assignment 중 local file이 필요한 것이 있다면
    # Recovery에도 동일한 capability가 반드시 제공되어야 한다.
    #
    missing_local = []

    for worker in failed_workers:
        assignment_id = (
            worker.get(
                "assignment_id"
            )
            or ""
        )

        assignment = (
            assignment_index.get(
                assignment_id
            )
        )

        if assignment is None:
            raise ValueError(
                "실패 Worker의 원본 assignment를 "
                "plan에서 찾지 못했습니다: "
                f"{assignment_id}"
            )

        if (
            assignment.get(
                "needs_local_files"
            )
            is True
            and input_dir is None
        ):
            missing_local.append(
                assignment_id
            )

    if missing_local:
        raise ValueError(
            "Recovery 대상 assignment에 local files가 "
            "필요하지만 input_dir가 없습니다: "
            + ", ".join(
                missing_local
            )
        )

    recovery_root = (
        batch_dir
        / "recovery"
    )

    recovery_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    #
    # 실패 Worker가 없더라도 빈 index를 만든다.
    # Evidence Pool은 이 파일을 안전하게 읽을 수 있다.
    #
    records = []

    runtime_current_date = (
        parallel.get(
            "current_date"
        )
        or ""
    )

    wave = int(
        parallel.get(
            "wave"
        )
        or 1
    )

    for original in failed_workers:
        assignment_id = (
            original.get(
                "assignment_id"
            )
            or ""
        )

        assignment = (
            assignment_index[
                assignment_id
            ]
        )

        assignment_text = (
            build_worker_assignment(
                assignment,
                runtime_current_date=
                    runtime_current_date,
            )
        )

        assignment_root = (
            recovery_root
            / assignment_id
        )

        assignment_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        print(
            "===== Recovery Worker ====="
        )

        print(
            "Wave:",
            wave,
        )

        print(
            "Assignment:",
            assignment_id,
        )

        print(
            "Original error:",
            original.get(
                "error"
            ),
        )

        try:
            result = run_worker(
                assignment=
                    assignment_text,
                skill_name=
                    effective_skill,
                max_turns=
                    effective_max_turns,
                output_root=
                    assignment_root,
                input_dir=
                    input_dir,
            )

            status = (
                "completed"
            )

            error = None

            worker_run_dir = (
                result.get(
                    "run_dir"
                )
            )

            metrics = (
                result.get(
                    "metrics"
                )
            )

            verification = (
                result.get(
                    "verification"
                )
            )

        except Exception as exc:
            status = (
                "failed"
            )

            error = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

            worker_run_dir = None
            metrics = None
            verification = None

        record = {
            "wave":
                wave,
            "assignment_id":
                assignment_id,
            "status":
                status,
            "recovery_mode":
                "sequential_retry",
            "original_status":
                original.get(
                    "status"
                ),
            "original_error":
                original.get(
                    "error"
                ),
            "worker_run_dir":
                worker_run_dir,
            "metrics":
                metrics,
            "verification":
                verification,
        }

        if error is not None:
            record[
                "error"
            ] = error

        records.append(
            record
        )

        print(
            "Recovery status:",
            status,
        )

        print()

    index_path = (
        recovery_root
        / "recovery-index.json"
    )

    save_json(
        index_path,
        records,
    )

    completed_count = sum(
        1
        for record in records
        if record[
            "status"
        ]
        == "completed"
    )

    failed_count = (
        len(records)
        - completed_count
    )

    result = {
        "status":
            (
                "completed"
                if failed_count == 0
                else "completed_with_errors"
            ),
        "batch_dir":
            str(
                batch_dir
            ),
        "recovery_index":
            str(
                index_path
            ),
        "recovery_count":
            len(records),
        "completed_recovery_count":
            completed_count,
        "failed_recovery_count":
            failed_count,
        "records":
            records,
    }

    print(
        "===== Recovery Summary ====="
    )

    print(
        "Recovery targets:",
        len(records),
    )

    print(
        "Completed:",
        completed_count,
    )

    print(
        "Failed:",
        failed_count,
    )

    print(
        "Result:",
        index_path,
    )

    return result


def main() -> int:
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--batch",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--skill",
        default=None,
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
    )

    args = (
        parser.parse_args()
    )

    result = run_recovery(
        batch_dir=
            args.batch,
        skill_name=
            args.skill,
        max_turns=
            args.max_turns,
        input_dir=
            args.input_dir,
    )

    return (
        0
        if result[
            "failed_recovery_count"
        ]
        == 0
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
