"""B2 Deep Research Replanner.

Python은 무엇을 추가 조사할지 결정하지 않는다.

기존 Wave의 측정값과 compact Evidence Pool을
active public SKILL.md + replan.md + convergence.md와 함께
Gemma4 Coordinator에 전달한다.

Gemma가 Skill에 따라:
- 추가 Wave 필요 여부
- 후속 sub-goal
- 필요한 evidence
를 결정한다.
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
from .evidence_gate import (
    canonical_file_path,
    canonical_url,
)
from .evidence_pool import resolve_worker_runs
from .worker import extract_json_object


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


def sha256_text(
    text: str,
) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


def collect_distinct_sources_read(
    batch_dir: Path,
) -> list[str]:
    """성공한 fetch_page의 실제 읽은 URL을 canonical 기준으로 센다."""

    resolved = resolve_worker_runs(
        batch_dir
    )

    urls: set[str] = set()

    for worker in resolved.values():
        run_dir = Path(
            worker["run_dir"]
        )

        logs = load_json(
            run_dir
            / "tool-calls.json"
        )

        for log in logs:
            name = (
                log.get("name")
                or ""
            )

            if name not in {
                "fetch_page",
                "read_pdf_pages",
            }:
                continue

            if log.get("ok") is not True:
                continue

            result = (
                log.get("result")
                or {}
            )

            if result.get("ok") is not True:
                continue

            data = (
                result.get("data")
                or {}
            )

            if name == "fetch_page":
                url = (
                    data.get("url")
                    or (
                        log.get(
                            "arguments"
                        )
                        or {}
                    ).get("url")
                    or ""
                )

                canonical = (
                    canonical_url(
                        url
                    )
                )

                if canonical:
                    urls.add(
                        canonical
                    )

            else:
                file_sha256 = (
                    data.get(
                        "file_sha256"
                    )
                    or ""
                ).strip()

                file_path = (
                    data.get("path")
                    or (
                        log.get(
                            "arguments"
                        )
                        or {}
                    ).get("path")
                    or ""
                )

                if file_sha256:
                    urls.add(
                        "file-sha256:"
                        + file_sha256
                    )

                elif file_path:
                    canonical_path = (
                        canonical_file_path(
                            file_path
                        )
                    )

                    if canonical_path:
                        urls.add(
                            "file-path:"
                            + canonical_path
                        )

    return sorted(
        urls
    )


def build_measurements(
    *,
    batch_dir: Path,
    pool: dict[str, Any],
    max_waves: int,
) -> dict[str, Any]:
    parallel = load_json(
        batch_dir
        / "parallel-result.json"
    )

    current_wave = int(
        parallel.get("wave")
        or 1
    )

    accepted = (
        pool.get(
            "accepted_claims"
        )
        or []
    )

    unsupported = (
        pool.get(
            "unsupported_claims"
        )
        or []
    )

    gaps = (
        pool.get("gaps")
        or []
    )

    distinct_sources = (
        collect_distinct_sources_read(
            batch_dir
        )
    )

    single_source_count = sum(
        1
        for claim in accepted
        if claim.get(
            "runtime_status"
        )
        == "SINGLE_SOURCE"
    )

    pending_independence_count = sum(
        1
        for claim in accepted
        if claim.get(
            "runtime_status"
        )
        == (
            "MULTI_SOURCE_"
            "PENDING_INDEPENDENCE"
        )
    )

    conflicting_count = sum(
        1
        for claim in accepted
        if claim.get(
            "runtime_status"
        )
        == "CONFLICTING"
    )

    # Wave 1은 이전 validated claim set이 없으므로
    # accepted claims 전체를 novel로 측정한다.
    #
    # 후속 Wave의 semantic novelty 비교는
    # 별도 단계에서 계산해야 한다.
    if current_wave == 1:
        novel_claim_counts = [
            len(accepted)
        ]

        novelty_ratios = [
            (
                1.0
                if accepted
                else 0.0
            )
        ]
    else:
        novel_claim_counts = []
        novelty_ratios = []

    return {
        "wave_count":
            current_wave,
        "max_waves":
            max_waves,
        "resource_cap_reached":
            current_wave
            >= max_waves,
        "distinct_sources_read":
            len(
                distinct_sources
            ),
        "distinct_source_urls":
            distinct_sources,
        "unique_verified_sources":
            pool.get(
                "summary",
                {},
            ).get(
                "unique_verified_source_count",
                0,
            ),
        "running_claim_count":
            len(accepted),
        "single_source_claim_count":
            single_source_count,
        "pending_independence_claim_count":
            pending_independence_count,
        "unsupported_claim_count":
            len(unsupported),
        "conflicting_claim_count":
            conflicting_count,
        "unresolved_gap_count":
            len(gaps),
        "novel_claim_counts":
            novel_claim_counts,
        "novelty_ratios":
            novelty_ratios,
        "novelty_measurement_note": (
            "Wave 1 begins with an empty prior "
            "validated claim set, so all accepted "
            "claims are measured as novel. "
            "Future-wave semantic novelty requires "
            "comparison against the running claim set."
        ),
    }


def build_compact_wave_summary(
    pool: dict[str, Any],
) -> dict[str, Any]:
    accepted = []

    for claim in (
        pool.get(
            "accepted_claims"
        )
        or []
    ):
        evidence = []

        for item in (
            claim.get(
                "verified_evidence"
            )
            or []
        ):
            source = (
                item.get("source")
                or {}
            )

            worker_source = (
                source.get(
                    "worker_source"
                )
                or {}
            )

            retrieved = (
                source.get(
                    "retrieved_source"
                )
                or {}
            )

            evidence.append(
                {
                    "evidence_id":
                        item.get(
                            "evidence_id"
                        ),
                    "state":
                        item.get(
                            "state"
                        ),
                    "publisher":
                        worker_source.get(
                            "publisher"
                        ),
                    "domain":
                        retrieved.get(
                            "domain"
                        ),
                    "url":
                        retrieved.get(
                            "url"
                        )
                        or worker_source.get(
                            "url"
                        ),
                    "audited_source_type":
                        item.get(
                            "audited_source_type"
                        ),
                    "audited_tier":
                        item.get(
                            "audited_tier"
                        ),
                }
            )

        accepted.append(
            {
                "claim_ref":
                    claim.get(
                        "claim_ref"
                    ),
                "assignment_id":
                    claim.get(
                        "assignment_id"
                    ),
                "claim":
                    claim.get(
                        "claim"
                    ),
                "runtime_status":
                    claim.get(
                        "runtime_status"
                    ),
                "verified_evidence_count":
                    claim.get(
                        "verified_evidence_count"
                    ),
                "evidence":
                    evidence,
            }
        )

    unsupported = [
        {
            "claim_ref":
                claim.get(
                    "claim_ref"
                ),
            "assignment_id":
                claim.get(
                    "assignment_id"
                ),
            "claim":
                claim.get(
                    "claim"
                ),
            "reason":
                claim.get(
                    "auditor_reason"
                ),
        }
        for claim in (
            pool.get(
                "unsupported_claims"
            )
            or []
        )
    ]

    gaps = [
        {
            "assignment_id":
                gap.get(
                    "assignment_id"
                ),
            "type":
                gap.get(
                    "type"
                ),
            "detail":
                gap.get(
                    "detail"
                ),
            "reason":
                gap.get(
                    "reason"
                ),
        }
        for gap in (
            pool.get("gaps")
            or []
        )
    ]

    sources = []

    for source in (
        pool.get("sources")
        or []
    ):
        source_kind = (
            source.get(
                "source_kind"
            )
            or (
                "web"
                if source.get(
                    "canonical_url"
                )
                else "file"
            )
        )

        sources.append(
            {
                "source_id":
                    source.get(
                        "source_id"
                    ),
                "source_kind":
                    source_kind,
                "canonical_url":
                    source.get(
                        "canonical_url"
                    ),
                "domain":
                    source.get(
                        "domain"
                    ),
                "path":
                    source.get(
                        "path"
                    ),
                "file_sha256":
                    source.get(
                        "file_sha256"
                    ),
                "verified_pages":
                    source.get(
                        "verified_pages"
                    )
                    or [],
                "publisher":
                    source.get(
                        "claimed_publisher"
                    ),
                "audited_source_type":
                    source.get(
                        "audited_source_type"
                    ),
                "audited_tier":
                    source.get(
                        "audited_tier"
                    ),
                "claim_refs":
                    source.get(
                        "claim_ids"
                    ),
            }
        )

    return {
        "completed_assignments": [
            {
                "assignment_id":
                    item.get(
                        "assignment_id"
                    ),
                "worker_source":
                    item.get(
                        "worker_source"
                    ),
                "accepted_claim_count":
                    item.get(
                        "accepted_claim_count"
                    ),
                "gap_count":
                    item.get(
                        "gap_count"
                    ),
            }
            for item in (
                pool.get(
                    "assignments"
                )
                or []
            )
        ],
        "accepted_claims":
            accepted,
        "unsupported_claims":
            unsupported,
        "gaps":
            gaps,
        "verified_source_registry":
            sources,
    }


def load_original_request(
    batch_dir: Path,
) -> str:
    parallel = load_json(
        batch_dir
        / "parallel-result.json"
    )

    plan_path = Path(
        parallel[
            "plan_path"
        ]
    )

    request_path = (
        plan_path.parent
        / "request.md"
    )

    if not request_path.is_file():
        raise FileNotFoundError(
            "Coordinator 원 요청을 찾을 수 없습니다: "
            f"{request_path}"
        )

    return request_path.read_text(
        encoding="utf-8"
    ).strip()


def build_system_prompt(
    *,
    skill: dict[str, Any],
    replan_contract: str,
    convergence_contract: str,
) -> str:
    return (
        "# Active Agent Skill\n\n"
        "The following public Agent Skill is "
        "the primary research behavior specification.\n\n"
        "<skill>\n"
        + skill["body"]
        + "\n</skill>\n\n"
        "# Runtime Re-planning Contract\n\n"
        + replan_contract
        + "\n\n"
        "# Runtime Convergence Contract\n\n"
        + convergence_contract
    )


def build_user_prompt(
    *,
    original_request: str,
    measurements: dict[str, Any],
    wave_summary: dict[str, Any],
    current_date: str,
    max_workers: int,
) -> str:
    packet = {
        "runtime_context": {
            "current_date":
                current_date,
            "maximum_followup_assignments":
                max_workers,
        },
        "measurements":
            measurements,
        "wave_summary":
            wave_summary,
    }

    return (
        "# Original Research Request\n\n"
        + original_request
        + "\n\n"
        "# Wave Review Packet\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Instructions\n\n"
        "- Review the active Skill first.\n"
        "- Decide whether another research wave is required.\n"
        "- Treat SINGLE_SOURCE, UNSUPPORTED, "
        "CONFLICTING, and "
        "MULTI_SOURCE_PENDING_INDEPENDENCE "
        "as unresolved evidence states unless the active "
        "Skill permits otherwise.\n"
        "- Do not perform research now.\n"
        "- Do not invent evidence or URLs.\n"
        "- Create only targeted follow-up assignments.\n"
        "- Return only the JSON required by replan.md.\n"
    )


def validate_replan(
    plan: dict[str, Any],
    *,
    prior_assignment_ids: set[str],
    max_workers: int,
) -> dict[str, Any]:
    errors = []

    needs_another_wave = (
        plan.get(
            "needs_another_wave"
        )
    )

    if not isinstance(
        needs_another_wave,
        bool,
    ):
        errors.append(
            "needs_another_wave가 bool이 아닙니다."
        )

    reason = (
        plan.get("reason")
    )

    if (
        not isinstance(
            reason,
            str,
        )
        or not reason.strip()
    ):
        errors.append(
            "reason이 비어 있습니다."
        )

    assignments = (
        plan.get(
            "assignments"
        )
    )

    if not isinstance(
        assignments,
        list,
    ):
        errors.append(
            "assignments가 list가 아닙니다."
        )

        assignments = []

    if (
        needs_another_wave is False
        and assignments
    ):
        errors.append(
            "needs_another_wave=false인데 "
            "assignments가 존재합니다."
        )

    if (
        needs_another_wave is True
        and not assignments
    ):
        errors.append(
            "needs_another_wave=true인데 "
            "assignments가 없습니다."
        )

    if len(assignments) > max_workers:
        errors.append(
            "assignment 수가 max_workers를 "
            "초과했습니다."
        )

    allowed_top_level = {
        "needs_another_wave",
        "reason",
        "assignments",
    }

    unexpected_top_level = sorted(
        set(plan)
        - allowed_top_level
    )

    if unexpected_top_level:
        errors.append(
            "허용되지 않은 top-level field: "
            + ", ".join(
                unexpected_top_level
            )
        )

    allowed_assignment_fields = {
        "assignment_id",
        "title",
        "objective",
        "queries",
        "source_priority",
        "needs_local_files",
    }

    seen_ids = set()

    for index, assignment in enumerate(
        assignments,
        1,
    ):
        prefix = (
            f"assignments[{index}]"
        )

        if not isinstance(
            assignment,
            dict,
        ):
            errors.append(
                f"{prefix}가 객체가 아닙니다."
            )
            continue

        unexpected_fields = sorted(
            set(assignment)
            - allowed_assignment_fields
        )

        if unexpected_fields:
            errors.append(
                f"{prefix} 허용되지 않은 field: "
                + ", ".join(
                    unexpected_fields
                )
            )

        assignment_id = (
            assignment.get(
                "assignment_id"
            )
            or ""
        ).strip()

        if not assignment_id:
            errors.append(
                f"{prefix}.assignment_id가 "
                "비어 있습니다."
            )

        elif (
            assignment_id
            in prior_assignment_ids
        ):
            errors.append(
                "기존 assignment_id 재사용: "
                f"{assignment_id}"
            )

        elif assignment_id in seen_ids:
            errors.append(
                "중복 assignment_id: "
                f"{assignment_id}"
            )

        else:
            seen_ids.add(
                assignment_id
            )

        for field in (
            "title",
            "objective",
        ):
            value = (
                assignment.get(
                    field
                )
            )

            if (
                not isinstance(
                    value,
                    str,
                )
                or not value.strip()
            ):
                errors.append(
                    f"{prefix}.{field}가 "
                    "비어 있습니다."
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
            or not all(
                isinstance(
                    query,
                    str,
                )
                and query.strip()
                for query in queries
            )
        ):
            errors.append(
                f"{prefix}.queries는 "
                "비어 있지 않은 문자열 list여야 합니다."
            )

        source_priority = (
            assignment.get(
                "source_priority"
            )
        )

        if (
            not isinstance(
                source_priority,
                list,
            )
            or not source_priority
            or not all(
                isinstance(
                    priority,
                    str,
                )
                and priority.strip()
                for priority
                in source_priority
            )
        ):
            errors.append(
                f"{prefix}.source_priority는 "
                "비어 있지 않은 문자열 list여야 합니다."
            )

        if not isinstance(
            assignment.get(
                "needs_local_files"
            ),
            bool,
        ):
            errors.append(
                f"{prefix}.needs_local_files가 "
                "bool이 아닙니다."
            )

    return {
        "ok":
            not errors,
        "errors":
            errors,
        "needs_another_wave":
            needs_another_wave,
        "assignment_count":
            len(assignments),
        "assignment_ids":
            [
                item.get(
                    "assignment_id"
                )
                for item in assignments
                if isinstance(
                    item,
                    dict,
                )
            ],
    }



def build_repair_prompt(
    *,
    invalid_plan: dict[str, Any],
    validation: dict[str, Any],
    max_workers: int,
) -> str:
    """Research intent는 유지하고 schema 오류만 Gemma가 복구하도록 요청한다."""

    required_shape = {
        "needs_another_wave": True,
        "reason": "brief reason",
        "assignments": [
            {
                "assignment_id":
                    "new unique id",
                "title":
                    "targeted follow-up",
                "objective":
                    "specific evidence gap to close",
                "queries": [
                    "targeted query 1"
                ],
                "source_priority": [
                    "official"
                ],
                "needs_local_files":
                    False,
            }
        ],
    }

    return (
        "# Re-plan Schema Repair\n\n"
        "The previous research re-plan failed runtime "
        "schema validation.\n\n"
        "This is a FORMAT/COMPLETENESS repair pass, "
        "not a new research-planning pass.\n\n"
        "Preserve the previous plan's research intent "
        "and targeted gaps wherever possible. "
        "Do not perform research and do not invent evidence.\n\n"
        "# Validation Errors\n\n"
        + json.dumps(
            validation.get(
                "errors",
                [],
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Invalid Re-plan\n\n"
        + json.dumps(
            invalid_plan,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Exact Required Shape\n\n"
        + json.dumps(
            required_shape,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Repair Rules\n\n"
        "- Return one JSON object only.\n"
        "- Use only these top-level fields: "
        "needs_another_wave, reason, assignments.\n"
        "- Each assignment must contain exactly: "
        "assignment_id, title, objective, queries, "
        "source_priority, needs_local_files.\n"
        "- Remove all other fields.\n"
        "- Every title and objective must be non-empty.\n"
        "- queries must be a non-empty list of strings.\n"
        "- source_priority must be a non-empty list of strings.\n"
        "- needs_local_files must be true or false.\n"
        f"- Return no more than {max_workers} assignments.\n"
        "- Preserve already valid assignment IDs when possible.\n"
        "- Complete malformed or truncated assignments "
        "using the same unresolved evidence context and "
        "active Skill supplied in the system message.\n"
    )


def repair_replan(
    *,
    client: OllamaClient,
    system_prompt: str,
    initial_plan: dict[str, Any],
    initial_validation: dict[str, Any],
    prior_assignment_ids: set[str],
    max_workers: int,
    run_dir: Path,
    max_attempts: int = 2,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    """Invalid replan을 generic schema-repair loop로 복구한다."""

    plan = initial_plan
    validation = initial_validation
    attempts: list[
        dict[str, Any]
    ] = []

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        if validation["ok"]:
            break

        repair_prompt = (
            build_repair_prompt(
                invalid_plan=plan,
                validation=validation,
                max_workers=max_workers,
            )
        )

        (
            run_dir
            / f"repair-{attempt:02d}-prompt.md"
        ).write_text(
            repair_prompt + "\n",
            encoding="utf-8",
        )

        started = time.monotonic()

        response = client.chat(
            [
                {
                    "role": "system",
                    "content":
                        system_prompt,
                },
                {
                    "role": "user",
                    "content":
                        repair_prompt,
                },
            ],
            think=False,
            response_format="json",
        )

        elapsed = (
            time.monotonic()
            - started
        )

        save_json(
            run_dir
            / (
                f"repair-{attempt:02d}"
                "-response.json"
            ),
            response,
        )

        raw_text = (
            response.get(
                "message",
                {},
            ).get(
                "content"
            )
            or ""
        )

        (
            run_dir
            / (
                f"repair-{attempt:02d}"
                "-raw.txt"
            )
        ).write_text(
            raw_text,
            encoding="utf-8",
        )

        if not raw_text.strip():
            thinking = (
                response.get(
                    "message",
                    {},
                ).get(
                    "thinking"
                )
                or ""
            )

            attempts.append(
                {
                    "attempt":
                        attempt,
                    "elapsed_seconds":
                        round(
                            elapsed,
                            3,
                        ),
                    "status":
                        "empty_response",
                    "done_reason":
                        response.get(
                            "done_reason"
                        ),
                    "eval_count":
                        response.get(
                            "eval_count"
                        ),
                    "thinking_chars":
                        len(
                            thinking
                        ),
                }
            )

            continue

        try:
            candidate = (
                extract_json_object(
                    raw_text
                )
            )

        except Exception as exc:
            attempts.append(
                {
                    "attempt":
                        attempt,
                    "elapsed_seconds":
                        round(
                            elapsed,
                            3,
                        ),
                    "status":
                        "parse_error",
                    "error":
                        (
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                }
            )

            continue

        candidate_validation = (
            validate_replan(
                candidate,
                prior_assignment_ids=
                    prior_assignment_ids,
                max_workers=
                    max_workers,
            )
        )

        save_json(
            run_dir
            / (
                f"repair-{attempt:02d}"
                "-replan.json"
            ),
            candidate,
        )

        save_json(
            run_dir
            / (
                f"repair-{attempt:02d}"
                "-validation.json"
            ),
            candidate_validation,
        )

        attempts.append(
            {
                "attempt":
                    attempt,
                "elapsed_seconds":
                    round(
                        elapsed,
                        3,
                    ),
                "status":
                    (
                        "valid"
                        if candidate_validation[
                            "ok"
                        ]
                        else "invalid"
                    ),
                "errors":
                    candidate_validation[
                        "errors"
                    ],
            }
        )

        plan = candidate
        validation = (
            candidate_validation
        )

    return (
        plan,
        validation,
        attempts,
    )


def run_replanner(
    *,
    batch_dir: Path,
    skill_name: str,
    max_workers: int,
    max_waves: int,
) -> dict[str, Any]:
    batch_dir = (
        batch_dir.resolve()
    )

    pool_path = (
        batch_dir
        / "evidence-pool"
        / "evidence-pool.json"
    )

    pool = load_json(
        pool_path
    )

    parallel = load_json(
        batch_dir
        / "parallel-result.json"
    )

    original_request = (
        load_original_request(
            batch_dir
        )
    )

    measurements = (
        build_measurements(
            batch_dir=
                batch_dir,
            pool=pool,
            max_waves=
                max_waves,
        )
    )

    wave_summary = (
        build_compact_wave_summary(
            pool
        )
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

    contracts = (
        load_b2_contracts()
    )

    replan_contract = (
        contracts["replan"]
    )

    convergence_contract = (
        contracts[
            "convergence"
        ]
    )

    system_prompt = (
        build_system_prompt(
            skill=skill,
            replan_contract=
                replan_contract,
            convergence_contract=
                convergence_contract,
        )
    )

    current_date = (
        parallel.get(
            "current_date"
        )
        or datetime.now(
            timezone.utc
        ).date().isoformat()
    )

    user_prompt = (
        build_user_prompt(
            original_request=
                original_request,
            measurements=
                measurements,
            wave_summary=
                wave_summary,
            current_date=
                current_date,
            max_workers=
                max_workers,
        )
    )

    output_root = (
        batch_dir
        / "replanning"
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="replan-",
            dir=output_root,
        )
    )

    save_json(
        run_dir
        / "measurements.json",
        measurements,
    )

    save_json(
        run_dir
        / "wave-summary.json",
        wave_summary,
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

    client = OllamaClient()

    print(
        "===== B2 Replanner =====",
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
        "Current wave:",
        measurements[
            "wave_count"
        ],
        flush=True,
    )

    print(
        "Distinct sources read:",
        measurements[
            "distinct_sources_read"
        ],
        flush=True,
    )

    print(
        "Verified sources:",
        measurements[
            "unique_verified_sources"
        ],
        flush=True,
    )

    print(
        "Single-source claims:",
        measurements[
            "single_source_claim_count"
        ],
        flush=True,
    )

    print(
        "Unresolved gaps:",
        measurements[
            "unresolved_gap_count"
        ],
        flush=True,
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

    started = time.monotonic()

    response = client.chat(
        messages,
        response_format="json",
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
        response.get(
            "message",
            {},
        ).get(
            "content"
        )
        or ""
    )

    (
        run_dir
        / "replan-raw.txt"
    ).write_text(
        raw_text,
        encoding="utf-8",
    )

    if not raw_text.strip():
        thinking = (
            response.get(
                "message",
                {},
            ).get(
                "thinking"
            )
            or ""
        )

        raise RuntimeError(
            "Replanner가 빈 content를 "
            "반환했습니다. "
            f"done_reason="
            f"{response.get('done_reason')!r}, "
            f"eval_count="
            f"{response.get('eval_count')!r}, "
            f"thinking_chars="
            f"{len(thinking)}"
        )

    plan = extract_json_object(
        raw_text
    )

    prior_assignment_ids = {
        assignment[
            "assignment_id"
        ]
        for assignment
        in load_json(
            batch_dir
            / "plan.json"
        ).get(
            "assignments",
            [],
        )
    }

    validation = (
        validate_replan(
            plan,
            prior_assignment_ids=
                prior_assignment_ids,
            max_workers=
                max_workers,
        )
    )

    initial_validation = dict(
        validation
    )

    save_json(
        run_dir
        / "replan-initial.json",
        plan,
    )

    save_json(
        run_dir
        / "replan-initial-validation.json",
        validation,
    )

    repair_attempts = []

    if not validation["ok"]:
        print()
        print(
            "Initial replan invalid; "
            "starting generic repair.",
            flush=True,
        )

        (
            plan,
            validation,
            repair_attempts,
        ) = repair_replan(
            client=client,
            system_prompt=
                system_prompt,
            initial_plan=plan,
            initial_validation=
                validation,
            prior_assignment_ids=
                prior_assignment_ids,
            max_workers=
                max_workers,
            run_dir=run_dir,
            max_attempts=2,
        )

    save_json(
        run_dir
        / "replan.json",
        plan,
    )

    save_json(
        run_dir
        / "replan-validation.json",
        validation,
    )

    result = {
        "status":
            (
                "completed"
                if validation["ok"]
                else "invalid_replan"
            ),
        "stage":
            "B2-6",
        "created_at":
            utc_now(),
        "run_dir":
            str(run_dir),
        "model":
            client.model,
        "skill":
            skill["name"],
        "skill_sha256":
            skill["sha256"],
        "replan_contract_sha256":
            sha256_text(
                replan_contract
            ),
        "convergence_contract_sha256":
            sha256_text(
                convergence_contract
            ),
        "elapsed_seconds":
            round(
                elapsed,
                3,
            ),
        "measurements":
            measurements,
        "replan":
            plan,
        "initial_validation":
            initial_validation,
        "repair_attempts":
            repair_attempts,
        "validation":
            validation,
        "discovery_errors":
            discovery_errors,
    }

    save_json(
        run_dir
        / "result.json",
        result,
    )

    print()
    print(
        "Replanner time:",
        f"{elapsed:.3f}초",
        flush=True,
    )

    print(
        "Validation:",
        validation["ok"],
        flush=True,
    )

    print(
        "Needs another wave:",
        plan.get(
            "needs_another_wave"
        ),
        flush=True,
    )

    print(
        "Reason:",
        plan.get(
            "reason"
        ),
        flush=True,
    )

    print()

    for assignment in (
        plan.get(
            "assignments"
        )
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

        print()

    if validation["errors"]:
        print(
            "===== VALIDATION ERRORS ====="
        )

        for error in (
            validation[
                "errors"
            ]
        ):
            print(
                "-",
                error,
            )

    print(
        "Result:",
        run_dir
        / "result.json",
        flush=True,
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch",
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
        "--max-waves",
        type=int,
        default=3,
    )

    args = parser.parse_args()

    if not 1 <= args.max_workers <= 5:
        raise ValueError(
            "max_workers는 1~5여야 합니다."
        )

    if args.max_waves < 1:
        raise ValueError(
            "max_waves는 1 이상이어야 합니다."
        )

    run_replanner(
        batch_dir=
            args.batch,
        skill_name=
            args.skill,
        max_workers=
            args.max_workers,
        max_waves=
            args.max_waves,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
