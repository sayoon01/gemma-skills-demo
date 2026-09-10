"""B2 Deep Research end-to-end runtime.

Public Agent Skill과 B2 Markdown contracts가 연구 방법을 정의하고,
이 모듈은 이미 검증된 Python runtime component를 순서대로 연결한다.

현재 검증된 cumulative architecture 범위:
- Wave 1
- Replan
- Wave 2
- Cumulative semantic matching
- Independence audit/challenge
- Finalization
- Synthesis

max_waves=2는 semantic convergence 선언이 아니라
resource safety cap으로 취급한다.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any

from .coordinator import (
    run_coordinator,
)
from .parallel_workers import (
    run_parallel_workers,
)
from .recovery import (
    run_recovery,
)
from .evidence_pool import (
    run_evidence_pool,
)
from .replanner import (
    run_replanner,
)
from .cumulative_matcher import (
    run_match,
)
from .cumulative_state import (
    build_state,
)
from .source_independence import (
    run_independence_audit,
)
from .independence_challenge import (
    run_independence_challenge,
)
from .finalizer import (
    run_finalizer,
)
from .synthesis import (
    run_synthesis,
)


ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


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
    value: Any,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )


def find_single_file(
    root: Path,
    name: str,
) -> Path:
    matches = sorted(
        root.rglob(
            name
        )
    )

    if len(matches) != 1:
        raise RuntimeError(
            f"{root} 아래에서 {name!r}을 "
            "정확히 1개 찾을 것으로 예상했지만 "
            f"{len(matches)}개를 찾았습니다."
        )

    return matches[0]


def resolve_batch_dir(
    stage_root: Path,
) -> Path:
    parallel_result = (
        find_single_file(
            stage_root,
            "parallel-result.json",
        )
    )

    return (
        parallel_result
        .parent
        .resolve()
    )


def require_completed(
    result: dict[str, Any],
    *,
    stage: str,
) -> None:
    status = (
        result.get(
            "status"
        )
    )

    if status != "completed":
        raise RuntimeError(
            f"{stage}가 completed가 아닙니다: "
            f"{status!r}"
        )


def run_wave(
    *,
    wave: int,
    plan_path: Path,
    run_dir: Path,
    skill_name: str,
    max_workers: int,
    max_turns: int,
    input_dir: Path | None,
) -> dict[str, Any]:
    wave_root = (
        run_dir
        / "waves"
        / f"wave-{wave}"
    )

    wave_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(
        "=" * 72
    )
    print(
        f"B2 WAVE {wave}"
    )
    print(
        "=" * 72
    )
    print()

    parallel = (
        run_parallel_workers(
            plan_path=
                plan_path,
            skill_name=
                skill_name,
            max_workers=
                max_workers,
            max_turns=
                max_turns,
            output_root=
                wave_root,
            wave_override=
                wave,
            input_dir=
                input_dir,
        )
    )

    batch_dir = (
        resolve_batch_dir(
            wave_root
        )
    )

    recovery = (
        run_recovery(
            batch_dir=
                batch_dir,
            skill_name=
                skill_name,
            max_turns=
                max_turns,
            input_dir=
                input_dir,
        )
    )

    pool_runtime = (
        run_evidence_pool(
            batch_dir=
                batch_dir,
            skill_name=
                skill_name,
        )
    )

    pool_path = (
        batch_dir
        / "evidence-pool"
        / "evidence-pool.json"
    )

    if not pool_path.is_file():
        raise RuntimeError(
            "Evidence Pool이 생성되지 않았습니다: "
            f"{pool_path}"
        )

    return {
        "wave":
            wave,
        "plan_path":
            str(
                plan_path.resolve()
            ),
        "batch_dir":
            str(
                batch_dir
            ),
        "pool_path":
            str(
                pool_path.resolve()
            ),
        "parallel":
            parallel,
        "recovery":
            recovery,
        "evidence_pool":
            pool_runtime,
    }


def build_stop_record(
    *,
    final_replan: dict[str, Any],
    max_waves: int,
) -> dict[str, Any]:
    measurements = (
        final_replan.get(
            "measurements"
        )
        or {}
    )

    replan = (
        final_replan.get(
            "replan"
        )
        or {}
    )

    resource_cap_reached = bool(
        measurements.get(
            "resource_cap_reached"
        )
    )

    needs_another_wave = bool(
        replan.get(
            "needs_another_wave"
        )
    )

    #
    # Runtime이 Skill의 semantic convergence 기준을
    # Python으로 재구현하지 않는다.
    #
    # 현재 Replanner schema에는 explicit converged 필드가 없으므로
    # semantic convergence를 임의로 true로 만들지 않는다.
    #
    converged = bool(
        replan.get(
            "converged",
            False,
        )
    )

    if converged:
        stop_reason = (
            "semantic_convergence"
        )

    elif resource_cap_reached:
        stop_reason = (
            "max_waves_reached"
        )

    elif needs_another_wave:
        stop_reason = (
            "runtime_stopped_before_requested_next_wave"
        )

    else:
        stop_reason = (
            "replanner_stop_without_explicit_convergence"
        )

    return {
        "created_at":
            utc_now(),
        "converged":
            converged,
        "stop_reason":
            stop_reason,
        "max_waves":
            max_waves,
        "resource_cap_reached":
            resource_cap_reached,
        "needs_another_wave":
            needs_another_wave,
        "replanner_reason":
            replan.get(
                "reason"
            ),
        "measurements":
            measurements,
    }


def run_research_b2(
    *,
    task_path: Path,
    skill_name: str,
    max_workers: int,
    max_turns: int,
    max_waves: int,
    input_dir: Path | None,
    output_root: Path,
    report_out: Path | None,
) -> dict[str, Any]:
    task_path = (
        task_path
        .expanduser()
        .resolve()
    )

    if not task_path.is_file():
        raise FileNotFoundError(
            f"Task 파일을 찾지 못했습니다: {task_path}"
        )

    if not 1 <= max_workers <= 5:
        raise ValueError(
            "max_workers는 1~5여야 합니다."
        )

    if not 1 <= max_turns <= 20:
        raise ValueError(
            "max_turns는 1~20이어야 합니다."
        )

    #
    # 현재 cumulative matcher/state가 실제 검증된 범위는
    # Wave1 + Wave2이다.
    #
    # 3-wave 이상을 지원한다고 가장하지 않는다.
    #
    if max_waves != 2:
        raise ValueError(
            "현재 검증된 B2 E2E cumulative runtime은 "
            "--max-waves 2만 지원합니다. "
            "이 값은 convergence 선언이 아니라 "
            "resource safety cap입니다."
        )

    if input_dir is not None:
        input_dir = (
            input_dir
            .expanduser()
            .resolve()
        )

        if not input_dir.is_dir():
            raise ValueError(
                "input_dir가 존재하는 "
                "디렉터리가 아닙니다: "
                f"{input_dir}"
            )

    output_root = (
        output_root
        .expanduser()
        .resolve()
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

    task_text = (
        task_path.read_text(
            encoding="utf-8"
        )
    )

    print(
        "=" * 72
    )
    print(
        "B2 DEEP RESEARCH E2E"
    )
    print(
        "=" * 72
    )
    print(
        "Run:",
        run_dir,
    )
    print(
        "Task:",
        task_path,
    )
    print(
        "Skill:",
        skill_name,
    )
    print(
        "Max workers:",
        max_workers,
    )
    print(
        "Max turns:",
        max_turns,
    )
    print(
        "Max waves:",
        max_waves,
    )
    print(
        "Input dir:",
        input_dir,
    )
    print()

    #
    # ------------------------------------------------------------
    # B2-3 Coordinator
    # ------------------------------------------------------------
    #
    coordinator_root = (
        run_dir
        / "coordinator"
    )

    coordinator = (
        run_coordinator(
            request_text=
                task_text,
            request_source={
                "type":
                    "task_file",
                "path":
                    str(
                        task_path
                    ),
            },
            skill_name=
                skill_name,
            max_workers=
                max_workers,
            output_root=
                coordinator_root,
        )
    )

    require_completed(
        coordinator,
        stage="Coordinator",
    )

    #
    # Coordinator가 실제 저장한 plan을 그대로 사용한다.
    # 별도 재생성하지 않는다.
    #
    wave1_plan_path = (
        find_single_file(
            coordinator_root,
            "plan.json",
        )
    )

    #
    # ------------------------------------------------------------
    # Wave 1
    # ------------------------------------------------------------
    #
    wave1 = run_wave(
        wave=1,
        plan_path=
            wave1_plan_path,
        run_dir=
            run_dir,
        skill_name=
            skill_name,
        max_workers=
            max_workers,
        max_turns=
            max_turns,
        input_dir=
            input_dir,
    )

    wave1_batch = Path(
        wave1[
            "batch_dir"
        ]
    )

    wave1_pool = Path(
        wave1[
            "pool_path"
        ]
    )

    #
    # ------------------------------------------------------------
    # Replan after Wave 1
    # ------------------------------------------------------------
    #
    replan1 = (
        run_replanner(
            batch_dir=
                wave1_batch,
            skill_name=
                skill_name,
            max_workers=
                max_workers,
            max_waves=
                max_waves,
        )
    )

    require_completed(
        replan1,
        stage="Wave 1 Replanner",
    )

    replan1_plan = (
        replan1.get(
            "replan"
        )
        or {}
    )

    if (
        replan1_plan.get(
            "needs_another_wave"
        )
        is not True
    ):
        raise RuntimeError(
            "Wave 1 Replanner가 두 번째 wave를 "
            "요청하지 않았습니다. "
            "현재 검증된 cumulative runtime은 "
            "2-wave 입력을 필요로 하므로 "
            "semantic 결과를 임의로 만들어 진행하지 않습니다. "
            f"Reason={replan1_plan.get('reason')!r}"
        )

    wave2_plan_path = (
        Path(
            replan1[
                "run_dir"
            ]
        )
        / "replan.json"
    )

    if not wave2_plan_path.is_file():
        raise RuntimeError(
            "Wave 2 replan.json을 찾지 못했습니다: "
            f"{wave2_plan_path}"
        )

    #
    # ------------------------------------------------------------
    # Wave 2
    # ------------------------------------------------------------
    #
    wave2 = run_wave(
        wave=2,
        plan_path=
            wave2_plan_path,
        run_dir=
            run_dir,
        skill_name=
            skill_name,
        max_workers=
            max_workers,
        max_turns=
            max_turns,
        input_dir=
            input_dir,
    )

    wave2_batch = Path(
        wave2[
            "batch_dir"
        ]
    )

    wave2_pool = Path(
        wave2[
            "pool_path"
        ]
    )

    #
    # ------------------------------------------------------------
    # Final Replanner / stop assessment
    # ------------------------------------------------------------
    #
    final_replan = (
        run_replanner(
            batch_dir=
                wave2_batch,
            skill_name=
                skill_name,
            max_workers=
                max_workers,
            max_waves=
                max_waves,
        )
    )

    require_completed(
        final_replan,
        stage="Wave 2 Replanner",
    )

    #
    # ------------------------------------------------------------
    # Cumulative semantic matcher
    # ------------------------------------------------------------
    #
    cumulative_root = (
        run_dir
        / "cumulative"
    )

    cumulative_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    matcher = (
        run_match(
            prior_pool_path=
                wave1_pool,
            new_pool_path=
                wave2_pool,
            skill_name=
                skill_name,
            output_root=
                cumulative_root
                / "matcher-wave2",
        )
    )

    matcher_validation = (
        matcher.get(
            "validation"
        )
        or {}
    )

    if (
        matcher_validation.get(
            "ok"
        )
        is not True
    ):
        raise RuntimeError(
            "Cumulative Matcher validation이 "
            "ok=true가 아닙니다."
        )

    #
    # ------------------------------------------------------------
    # Cumulative state
    # ------------------------------------------------------------
    #
    prior_pool = (
        load_json(
            wave1_pool
        )
    )

    new_pool = (
        load_json(
            wave2_pool
        )
    )

    cumulative_state = (
        build_state(
            prior_pool=
                prior_pool,
            new_pool=
                new_pool,
            match_result=
                matcher,
        )
    )

    cumulative_path = (
        cumulative_root
        / "cumulative-state-wave2.json"
    )

    save_json(
        cumulative_path,
        cumulative_state,
    )

    #
    # ------------------------------------------------------------
    # Independence
    # ------------------------------------------------------------
    #
    pending_refs = (
        cumulative_state.get(
            "pending_independence_claim_refs"
        )
        or []
    )

    final_cumulative_path = (
        cumulative_root
        / "cumulative-state-final.json"
    )

    independence = None
    challenge = None

    if pending_refs:
        independence = (
            run_independence_audit(
                cumulative_path=
                    cumulative_path,
                skill_name=
                    skill_name,
                output_root=
                    cumulative_root
                    / "independence-wave2",
            )
        )

        require_completed(
            independence,
            stage="Source Independence",
        )

        independence_run = Path(
            independence[
                "run_dir"
            ]
        )

        challenge = (
            run_independence_challenge(
                independence_run=
                    independence_run,
                skill_name=
                    skill_name,
            )
        )

        require_completed(
            challenge,
            stage="Independence Challenge",
        )

        run_finalizer(
            cumulative_path=
                cumulative_path,
            independence_result_path=
                independence_run
                / "result.json",
            challenge_result_path=
                independence_run
                / "challenge-result.json",
            output_path=
                final_cumulative_path,
        )

    else:
        #
        # Independence 검증 대상 자체가 없다면
        # semantic verdict를 새로 만들지 않는다.
        #
        shutil.copy2(
            cumulative_path,
            final_cumulative_path,
        )

    #
    # ------------------------------------------------------------
    # Stop record
    # ------------------------------------------------------------
    #
    stop_record = (
        build_stop_record(
            final_replan=
                final_replan,
            max_waves=
                max_waves,
        )
    )

    stop_record_path = (
        cumulative_root
        / "stop-record.json"
    )

    save_json(
        stop_record_path,
        stop_record,
    )

    #
    # ------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------
    #
    synthesis = (
        run_synthesis(
            task_path=
                task_path,
            cumulative_path=
                final_cumulative_path,
            stop_record_path=
                stop_record_path,
            skill_name=
                skill_name,
            output_root=
                run_dir
                / "synthesis",
        )
    )

    require_completed(
        synthesis,
        stage="Synthesis",
    )

    generated_report = Path(
        synthesis[
            "report_path"
        ]
    )

    external_report = None

    if report_out is not None:
        report_out = (
            report_out
            .expanduser()
            .resolve()
        )

        report_out.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            generated_report,
            report_out,
        )

        external_report = (
            str(
                report_out
            )
        )

    result = {
        "status":
            "completed",
        "stage":
            "B2-E2E",
        "created_at":
            utc_now(),
        "run_dir":
            str(
                run_dir
            ),
        "task_path":
            str(
                task_path
            ),
        "skill":
            skill_name,
        "max_workers":
            max_workers,
        "max_turns":
            max_turns,
        "max_waves":
            max_waves,
        "input_dir":
            (
                str(
                    input_dir
                )
                if input_dir
                is not None
                else None
            ),
        "wave1_batch":
            str(
                wave1_batch
            ),
        "wave1_pool":
            str(
                wave1_pool
            ),
        "wave2_batch":
            str(
                wave2_batch
            ),
        "wave2_pool":
            str(
                wave2_pool
            ),
        "cumulative_path":
            str(
                cumulative_path
            ),
        "final_cumulative_path":
            str(
                final_cumulative_path
            ),
        "stop_record_path":
            str(
                stop_record_path
            ),
        "stop":
            stop_record,
        "synthesis_result":
            synthesis,
        "report_path":
            str(
                generated_report
            ),
        "report_out":
            external_report,
    }

    result_path = (
        run_dir
        / "result.json"
    )

    save_json(
        result_path,
        result,
    )

    print()
    print(
        "=" * 72
    )
    print(
        "B2 E2E COMPLETED"
    )
    print(
        "=" * 72
    )

    print(
        "Run:",
        run_dir,
    )

    print(
        "Stop reason:",
        stop_record[
            "stop_reason"
        ],
    )

    print(
        "Converged:",
        stop_record[
            "converged"
        ],
    )

    print(
        "Report:",
        generated_report,
    )

    if external_report:
        print(
            "Report out:",
            external_report,
        )

    print(
        "Result:",
        result_path,
    )

    return result


def main() -> int:
    parser = (
        argparse.ArgumentParser(
            description=(
                "Public Agent Skill 기반 "
                "B2 Deep Research E2E runtime"
            )
        )
    )

    parser.add_argument(
        "--task",
        type=Path,
        required=True,
        help=(
            "연구 요청 Markdown/Text 파일"
        ),
    )

    parser.add_argument(
        "--skill",
        default="deep-research",
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help=(
            "Worker에게 제공할 로컬 자료 디렉터리"
        ),
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
        "--max-waves",
        type=int,
        default=2,
        help=(
            "Resource safety cap. "
            "현재 검증된 cumulative E2E는 2만 지원."
        ),
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        default=(
            ROOT
            / "outputs"
            / "research-b2"
            / "e2e"
        ),
    )

    parser.add_argument(
        "--report-out",
        type=Path,
        default=None,
        help=(
            "최종 report.md를 추가로 복사할 "
            "사용자 지정 경로"
        ),
    )

    args = (
        parser.parse_args()
    )

    try:
        result = (
            run_research_b2(
                task_path=
                    args.task,
                skill_name=
                    args.skill,
                max_workers=
                    args.max_workers,
                max_turns=
                    args.max_turns,
                max_waves=
                    args.max_waves,
                input_dir=
                    args.input_dir,
                output_root=
                    args.output_root,
                report_out=
                    args.report_out,
            )
        )

    except Exception as exc:
        print()
        print(
            "===== B2 E2E FAILED ====="
        )
        print(
            f"{type(exc).__name__}: {exc}"
        )

        return 1

    return (
        0
        if result.get(
            "status"
        )
        == "completed"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
