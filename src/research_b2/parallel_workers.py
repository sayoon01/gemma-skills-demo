"""B2 Parallel Research Worker Runtime.

Coordinator가 생성한 plan.json의 assignment를 그대로 읽어
여러 개의 독립 Gemma4 Worker context에서 동시에 실행한다.

조사 주제나 sub-goal은 이 파일에 하드코딩하지 않는다.

주의:
Thread/worker session의 시간 중첩은 측정하지만,
이 값만으로 GPU 내부 inference가 실제 병렬 수행됐다고
단정하지 않는다.
"""

from __future__ import annotations

import argparse
import itertools
import json
import tempfile
import time
import traceback
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .worker import run_worker


ROOT = Path(__file__).resolve().parents[2]


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


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def current_date() -> str:
    return datetime.now(
        timezone.utc
    ).date().isoformat()


def validate_parallel_plan(
    plan: dict[str, Any],
    *,
    max_workers: int,
) -> list[dict[str, Any]]:
    if not isinstance(
        plan,
        dict,
    ):
        raise ValueError(
            "plan 최상위는 객체여야 합니다."
        )

    assignments = (
        plan.get("assignments")
    )

    if (
        not isinstance(
            assignments,
            list,
        )
        or not assignments
    ):
        raise ValueError(
            "plan.assignments가 비어 있습니다."
        )

    if len(assignments) > max_workers:
        raise ValueError(
            "plan assignment 수가 "
            "max_workers를 초과합니다: "
            f"{len(assignments)} > {max_workers}"
        )

    seen_ids = set()

    for index, assignment in enumerate(
        assignments,
        1,
    ):
        if not isinstance(
            assignment,
            dict,
        ):
            raise ValueError(
                f"assignments[{index}]가 "
                "객체가 아닙니다."
            )

        assignment_id = (
            assignment.get(
                "assignment_id"
            )
            or ""
        ).strip()

        if not assignment_id:
            raise ValueError(
                f"assignments[{index}]의 "
                "assignment_id가 없습니다."
            )

        if assignment_id in seen_ids:
            raise ValueError(
                "중복 assignment_id: "
                f"{assignment_id}"
            )

        seen_ids.add(
            assignment_id
        )

        objective = (
            assignment.get(
                "objective"
            )
            or ""
        ).strip()

        if not objective:
            raise ValueError(
                f"{assignment_id}: "
                "objective가 비어 있습니다."
            )

        queries = (
            assignment.get(
                "queries"
            )
        )

        if (
            not isinstance(
                queries,
                list,
            )
            or not queries
        ):
            raise ValueError(
                f"{assignment_id}: "
                "queries가 비어 있습니다."
            )

    return assignments


def build_worker_assignment(
    assignment: dict[str, Any],
    *,
    runtime_current_date: str,
) -> str:
    """Coordinator assignment를 손실 없이 Worker에게 전달한다."""

    return (
        "# Runtime Context\n\n"
        f"- Current date: {runtime_current_date}\n\n"
        "# Controller Assignment\n\n"
        + json.dumps(
            assignment,
            ensure_ascii=False,
            indent=2,
        )
    )


def run_one_worker(
    *,
    assignment: dict[str, Any],
    skill_name: str,
    max_turns: int,
    workers_root: Path,
    batch_started_monotonic: float,
    runtime_current_date: str,
    input_dir: Path | None = None,
) -> dict[str, Any]:
    assignment_id = (
        assignment[
            "assignment_id"
        ]
    )

    worker_root = (
        workers_root
        / assignment_id
    )

    worker_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    assignment_text = (
        build_worker_assignment(
            assignment,
            runtime_current_date=
                runtime_current_date,
        )
    )

    started_at = utc_now()

    started_monotonic = (
        time.monotonic()
    )

    relative_start = (
        started_monotonic
        - batch_started_monotonic
    )

    print(
        f"[{assignment_id}] START "
        f"{started_at}",
        flush=True,
    )

    try:
        worker_result = run_worker(
            assignment=
                assignment_text,
            skill_name=
                skill_name,
            max_turns=
                max_turns,
            output_root=
                worker_root,
            input_dir=
                input_dir,
        )

        status = "completed"
        error = None
        error_traceback = None

    except Exception as exc:
        worker_result = None
        status = "failed"

        error = (
            f"{type(exc).__name__}: "
            f"{exc}"
        )

        error_traceback = (
            traceback.format_exc()
        )

    finished_monotonic = (
        time.monotonic()
    )

    finished_at = utc_now()

    relative_end = (
        finished_monotonic
        - batch_started_monotonic
    )

    wall_seconds = (
        finished_monotonic
        - started_monotonic
    )

    print(
        f"[{assignment_id}] END "
        f"{finished_at} / "
        f"{status} / "
        f"{wall_seconds:.3f}초",
        flush=True,
    )

    record = {
        "assignment_id":
            assignment_id,
        "title":
            assignment.get(
                "title"
            )
            or "",
        "status":
            status,
        "started_at":
            started_at,
        "finished_at":
            finished_at,
        "relative_start_seconds":
            round(
                relative_start,
                6,
            ),
        "relative_end_seconds":
            round(
                relative_end,
                6,
            ),
        "wall_seconds":
            round(
                wall_seconds,
                3,
            ),
        "error":
            error,
        "error_traceback":
            error_traceback,
        "worker_run_dir":
            (
                worker_result.get(
                    "run_dir"
                )
                if worker_result
                else None
            ),
        "worker_metrics":
            (
                worker_result.get(
                    "metrics"
                )
                if worker_result
                else None
            ),
        "worker_verification":
            (
                worker_result.get(
                    "verification"
                )
                if worker_result
                else None
            ),
    }

    return record


def pairwise_overlaps(
    workers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    overlaps = []

    for left, right in itertools.combinations(
        workers,
        2,
    ):
        start = max(
            left[
                "relative_start_seconds"
            ],
            right[
                "relative_start_seconds"
            ],
        )

        end = min(
            left[
                "relative_end_seconds"
            ],
            right[
                "relative_end_seconds"
            ],
        )

        overlap = max(
            0.0,
            end - start,
        )

        overlaps.append(
            {
                "left":
                    left[
                        "assignment_id"
                    ],
                "right":
                    right[
                        "assignment_id"
                    ],
                "overlap_seconds":
                    round(
                        overlap,
                        3,
                    ),
                "overlapped":
                    overlap > 0,
            }
        )

    return overlaps


def calculate_max_concurrency(
    workers: list[dict[str, Any]],
) -> int:
    events = []

    for worker in workers:
        events.append(
            (
                worker[
                    "relative_start_seconds"
                ],
                1,
            )
        )

        events.append(
            (
                worker[
                    "relative_end_seconds"
                ],
                -1,
            )
        )

    # 같은 시각이면 start를 end보다 먼저 계산한다.
    events.sort(
        key=lambda item: (
            item[0],
            -item[1],
        )
    )

    current = 0
    maximum = 0

    for _, delta in events:
        current += delta

        maximum = max(
            maximum,
            current,
        )

    return maximum


def build_parallel_metrics(
    *,
    workers: list[dict[str, Any]],
    batch_wall_seconds: float,
) -> dict[str, Any]:
    overlaps = pairwise_overlaps(
        workers
    )

    max_concurrency = (
        calculate_max_concurrency(
            workers
        )
    )

    worker_wall_sum = sum(
        worker["wall_seconds"]
        for worker
        in workers
    )

    model_total_sum = 0.0

    for worker in workers:
        metrics = (
            worker.get(
                "worker_metrics"
            )
            or {}
        )

        model_total_sum += float(
            metrics.get(
                "model_total_seconds"
            )
            or 0.0
        )

    starts = [
        worker[
            "relative_start_seconds"
        ]
        for worker
        in workers
    ]

    ends = [
        worker[
            "relative_end_seconds"
        ]
        for worker
        in workers
    ]

    all_started_before_first_finished = (
        bool(
            starts
            and ends
        )
        and max(starts) < min(ends)
    )

    return {
        "worker_count":
            len(workers),
        "completed_worker_count":
            sum(
                1
                for worker
                in workers
                if worker[
                    "status"
                ]
                == "completed"
            ),
        "failed_worker_count":
            sum(
                1
                for worker
                in workers
                if worker[
                    "status"
                ]
                != "completed"
            ),
        "batch_wall_seconds":
            round(
                batch_wall_seconds,
                3,
            ),
        "worker_wall_seconds_sum":
            round(
                worker_wall_sum,
                3,
            ),
        "worker_model_seconds_sum":
            round(
                model_total_sum,
                3,
            ),
        "session_overlap_factor":
            round(
                (
                    worker_wall_sum
                    / batch_wall_seconds
                )
                if batch_wall_seconds
                else 0.0,
                3,
            ),
        "max_concurrent_worker_sessions":
            max_concurrency,
        "all_workers_started_before_first_finished":
            all_started_before_first_finished,
        "parallel_session_overlap_observed":
            max_concurrency >= 2,
        "pairwise_overlaps":
            overlaps,
        "measurement_scope": (
            "Worker session/request wall-time overlap. "
            "This does not by itself prove simultaneous "
            "GPU inference inside the model server."
        ),
    }


def run_parallel_workers(
    *,
    plan_path: Path,
    skill_name: str,
    max_workers: int,
    max_turns: int,
    output_root: Path,
    wave_override: int | None = None,
    input_dir: Path | None = None,
) -> dict[str, Any]:
    if not 1 <= max_workers <= 5:
        raise ValueError(
            "max_workers는 1~5여야 합니다."
        )

    if not 1 <= max_turns <= 20:
        raise ValueError(
            "max_turns는 1~20이어야 합니다."
        )

    plan_path = (
        plan_path.resolve()
    )

    plan = load_json(
        plan_path
    )

    assignments = (
        validate_parallel_plan(
            plan,
            max_workers=
                max_workers,
        )
    )

    local_required = any(
        assignment.get(
            "needs_local_files"
        )
        is True
        for assignment
        in assignments
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
                "--input-dir가 존재하는 "
                "디렉터리가 아닙니다: "
                f"{input_dir}"
            )

    if (
        local_required
        and input_dir is None
    ):
        raise ValueError(
            "생성된 plan에 local files가 필요한 "
            "assignment가 있지만 input_dir가 "
            "제공되지 않았습니다."
        )

    if (
        wave_override is not None
        and wave_override < 1
    ):
        raise ValueError(
            "wave_override는 1 이상이어야 합니다."
        )

    wave = (
        wave_override
        if wave_override is not None
        else (
            plan.get("wave")
            or 1
        )
    )

    if (
        not isinstance(wave, int)
        or isinstance(wave, bool)
        or wave < 1
    ):
        raise ValueError(
            f"유효하지 않은 wave 값: {wave!r}"
        )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    batch_dir = Path(
        tempfile.mkdtemp(
            prefix="run-",
            dir=output_root,
        )
    )

    workers_root = (
        batch_dir
        / "workers"
    )

    workers_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_json(
        batch_dir
        / "plan.json",
        plan,
    )

    runtime_current_date = (
        current_date()
    )

    config = {
        "stage":
            "B2-4",
        "created_at":
            utc_now(),
        "plan_path":
            str(
                plan_path
            ),
        "wave":
            wave,
        "skill":
            skill_name,
        "max_workers":
            max_workers,
        "max_turns":
            max_turns,
        "current_date":
            runtime_current_date,
        "assignment_count":
            len(
                assignments
            ),
        "assignment_ids":
            [
                assignment[
                    "assignment_id"
                ]
                for assignment
                in assignments
            ],
        "local_file_tools":
            False,
    }

    save_json(
        batch_dir
        / "run-config.json",
        config,
    )

    print(
        "===== B2 Parallel Workers =====",
        flush=True,
    )

    print(
        "Run:",
        batch_dir,
        flush=True,
    )

    print(
        "Wave:",
        wave,
        flush=True,
    )

    print(
        "Workers:",
        len(assignments),
        flush=True,
    )

    print(
        "Max parallel:",
        max_workers,
        flush=True,
    )

    print(
        "Current date:",
        runtime_current_date,
        flush=True,
    )

    print()

    batch_started_at = (
        utc_now()
    )

    batch_started_monotonic = (
        time.monotonic()
    )

    worker_records = []

    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix=
            "research-worker",
    ) as executor:
        futures = {}

        for assignment in assignments:
            future = executor.submit(
                run_one_worker,
                assignment=
                    assignment,
                skill_name=
                    skill_name,
                max_turns=
                    max_turns,
                workers_root=
                    workers_root,
                batch_started_monotonic=
                    batch_started_monotonic,
                runtime_current_date=
                    runtime_current_date,
                input_dir=
                    input_dir,
            )

            futures[
                future
            ] = assignment[
                "assignment_id"
            ]

        for future in as_completed(
            futures
        ):
            assignment_id = (
                futures[future]
            )

            try:
                record = future.result()

            except Exception as exc:
                # run_one_worker 안에서도 예외를 잡지만
                # executor 자체 예외에 대한 최후의 방어선.
                record = {
                    "assignment_id":
                        assignment_id,
                    "title":
                        "",
                    "status":
                        "executor_failed",
                    "started_at":
                        None,
                    "finished_at":
                        utc_now(),
                    "relative_start_seconds":
                        0.0,
                    "relative_end_seconds":
                        round(
                            time.monotonic()
                            - batch_started_monotonic,
                            6,
                        ),
                    "wall_seconds":
                        0.0,
                    "error":
                        (
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                    "error_traceback":
                        traceback.format_exc(),
                    "worker_run_dir":
                        None,
                    "worker_metrics":
                        None,
                    "worker_verification":
                        None,
                }

            worker_records.append(
                record
            )

            save_json(
                batch_dir
                / "workers-index.partial.json",
                sorted(
                    worker_records,
                    key=lambda item:
                        item[
                            "assignment_id"
                        ],
                ),
            )

    batch_finished_monotonic = (
        time.monotonic()
    )

    batch_finished_at = utc_now()

    batch_wall_seconds = (
        batch_finished_monotonic
        - batch_started_monotonic
    )

    worker_records.sort(
        key=lambda item:
            item[
                "assignment_id"
            ]
    )

    metrics = build_parallel_metrics(
        workers=
            worker_records,
        batch_wall_seconds=
            batch_wall_seconds,
    )

    status = (
        "completed"
        if metrics[
            "failed_worker_count"
        ]
        == 0
        else "completed_with_errors"
    )

    result = {
        **config,
        "status":
            status,
        "batch_started_at":
            batch_started_at,
        "batch_finished_at":
            batch_finished_at,
        "workers":
            worker_records,
        "metrics":
            metrics,
    }

    save_json(
        batch_dir
        / "workers-index.json",
        worker_records,
    )

    save_json(
        batch_dir
        / "parallel-result.json",
        result,
    )

    print()
    print(
        "===== Parallel Summary =====",
        flush=True,
    )

    print(
        "Status:",
        status,
        flush=True,
    )

    print(
        "Batch wall:",
        f"{batch_wall_seconds:.3f}초",
        flush=True,
    )

    print(
        "Worker wall sum:",
        metrics[
            "worker_wall_seconds_sum"
        ],
        flush=True,
    )

    print(
        "Worker model sum:",
        metrics[
            "worker_model_seconds_sum"
        ],
        flush=True,
    )

    print(
        "Max concurrent sessions:",
        metrics[
            "max_concurrent_worker_sessions"
        ],
        flush=True,
    )

    print(
        "All started before first finished:",
        metrics[
            "all_workers_started_before_first_finished"
        ],
        flush=True,
    )

    print(
        "Session overlap observed:",
        metrics[
            "parallel_session_overlap_observed"
        ],
        flush=True,
    )

    print()
    print(
        "Pairwise overlap:",
        flush=True,
    )

    for overlap in metrics[
        "pairwise_overlaps"
    ]:
        print(
            "-",
            overlap["left"],
            "/",
            overlap["right"],
            ":",
            overlap[
                "overlap_seconds"
            ],
            "sec",
            flush=True,
        )

    print()
    print(
        "Result:",
        batch_dir
        / "parallel-result.json",
        flush=True,
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
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
        "--max-turns",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        default=(
            ROOT
            / "outputs"
            / "research-b2"
            / "parallel-smoke"
        ),
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help=(
            "Worker가 접근할 수 있는 "
            "로컬 입력 디렉터리. "
            "지정하지 않으면 local-file tools는 "
            "Worker에 제공되지 않습니다."
        ),
    )

    parser.add_argument(
        "--wave",
        type=int,
        default=None,
        help=(
            "Plan 내부 wave 값 대신 사용할 "
            "runtime wave 번호"
        ),
    )

    args = parser.parse_args()

    run_parallel_workers(
        plan_path=
            args.plan,
        skill_name=
            args.skill,
        max_workers=
            args.max_workers,
        max_turns=
            args.max_turns,
        output_root=
            args.output_root,
        wave_override=
            args.wave,
        input_dir=
            args.input_dir,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
