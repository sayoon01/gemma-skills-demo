"""B2 Wave Evidence Pool Builder.

Parallel Worker와 Recovery Worker의 기존 결과를 재사용하여:

1. deterministic evidence gate
2. semantic audit
3. post-audit deterministic gate
4. validated evidence aggregation
5. unique URL normalization

을 수행한다.

새로운 웹 조사는 수행하지 않는다.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit_gate import apply_audit_gate
from .auditor import run_audit
from .evidence_gate import (
    canonical_url,
    validate_worker_result,
)


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


def resolve_worker_runs(
    batch_dir: Path,
) -> dict[str, dict[str, Any]]:
    """최종 사용할 Worker run을 Assignment별로 결정한다.

    원 Parallel Worker가 완료되었으면 그대로 사용하고,
    성공한 Recovery가 있으면 해당 Assignment를 Recovery 결과로
    덮어쓴다.
    """

    parallel_path = (
        batch_dir
        / "parallel-result.json"
    )

    plan_path = (
        batch_dir
        / "plan.json"
    )

    parallel = load_json(
        parallel_path
    )

    plan = load_json(
        plan_path
    )

    resolved: dict[
        str,
        dict[str, Any],
    ] = {}

    for worker in (
        parallel.get("workers")
        or []
    ):
        if (
            worker.get("status")
            != "completed"
        ):
            continue

        assignment_id = (
            worker.get(
                "assignment_id"
            )
            or ""
        )

        run_dir = (
            worker.get(
                "worker_run_dir"
            )
        )

        if (
            assignment_id
            and run_dir
        ):
            resolved[
                assignment_id
            ] = {
                "assignment_id":
                    assignment_id,
                "source":
                    "parallel",
                "run_dir":
                    str(
                        Path(
                            run_dir
                        ).resolve()
                    ),
            }

    recovery_index = (
        batch_dir
        / "recovery"
        / "recovery-index.json"
    )

    if recovery_index.is_file():
        recovery = load_json(
            recovery_index
        )

        for worker in recovery:
            if (
                worker.get("status")
                != "completed"
            ):
                continue

            assignment_id = (
                worker.get(
                    "assignment_id"
                )
                or ""
            )

            run_dir = (
                worker.get(
                    "worker_run_dir"
                )
            )

            if (
                assignment_id
                and run_dir
            ):
                resolved[
                    assignment_id
                ] = {
                    "assignment_id":
                        assignment_id,
                    "source":
                        "recovery",
                    "run_dir":
                        str(
                            Path(
                                run_dir
                            ).resolve()
                        ),
                }

    expected_ids = [
        assignment[
            "assignment_id"
        ]
        for assignment
        in plan.get(
            "assignments",
            [],
        )
    ]

    missing = [
        assignment_id
        for assignment_id
        in expected_ids
        if assignment_id
        not in resolved
    ]

    if missing:
        raise ValueError(
            "완료된 Worker 결과가 없는 Assignment: "
            + ", ".join(
                missing
            )
        )

    return {
        assignment_id:
            resolved[
                assignment_id
            ]
        for assignment_id
        in expected_ids
    }


def build_source_registry(
    accepted_claims: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    """Accepted evidence를 canonical URL 기준으로 중복 제거한다."""

    registry: dict[
        str,
        dict[str, Any],
    ] = {}

    for claim in accepted_claims:
        assignment_id = (
            claim.get(
                "assignment_id"
            )
            or ""
        )

        claim_id = (
            claim.get(
                "claim_id"
            )
            or ""
        )

        claim_ref = (
            f"{assignment_id}:{claim_id}"
            if assignment_id and claim_id
            else claim_id
        )

        for evidence in (
            claim.get(
                "verified_evidence"
            )
            or []
        ):
            source = (
                evidence.get(
                    "source"
                )
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

            url = (
                retrieved.get(
                    "url"
                )
                or worker_source.get(
                    "url"
                )
                or ""
            )

            canonical = (
                canonical_url(
                    url
                )
            )

            if not canonical:
                continue

            if canonical not in registry:
                registry[
                    canonical
                ] = {
                    "canonical_url":
                        canonical,
                    "url":
                        url,
                    "title":
                        retrieved.get(
                            "title"
                        )
                        or worker_source.get(
                            "title"
                        )
                        or "",
                    "domain":
                        retrieved.get(
                            "domain"
                        )
                        or "",
                    "claimed_publisher":
                        worker_source.get(
                            "publisher"
                        )
                        or "",
                    "audited_source_type":
                        evidence.get(
                            "audited_source_type"
                        ),
                    "audited_tier":
                        evidence.get(
                            "audited_tier"
                        ),
                    "assignments": [],
                    "claim_ids": [],
                    "evidence_ids": [],
                }

            record = registry[
                canonical
            ]

            if (
                assignment_id
                and assignment_id
                not in record[
                    "assignments"
                ]
            ):
                record[
                    "assignments"
                ].append(
                    assignment_id
                )

            if (
                claim_ref
                and claim_ref
                not in record[
                    "claim_ids"
                ]
            ):
                record[
                    "claim_ids"
                ].append(
                    claim_ref
                )

            evidence_id = (
                evidence.get(
                    "evidence_id"
                )
                or ""
            )

            if (
                evidence_id
                and evidence_id
                not in record[
                    "evidence_ids"
                ]
            ):
                record[
                    "evidence_ids"
                ].append(
                    evidence_id
                )

    items = list(
        registry.values()
    )

    items.sort(
        key=lambda item:
            item[
                "canonical_url"
            ]
    )

    for index, item in enumerate(
        items,
        1,
    ):
        item[
            "source_id"
        ] = (
            f"SRC{index:03d}"
        )

    return items


def build_worker_gap_records(
    *,
    assignment_id: str,
    worker_result:
        dict[str, Any],
    post_audit:
        dict[str, Any],
) -> list[dict[str, Any]]:
    gaps = []

    for gap in (
        worker_result.get(
            "gaps"
        )
        or []
    ):
        gaps.append(
            {
                "assignment_id":
                    assignment_id,
                "type":
                    "WORKER_GAP",
                "detail":
                    gap,
            }
        )

    for claim in (
        post_audit.get(
            "unsupported_claims"
        )
        or []
    ):
        gaps.append(
            {
                "assignment_id":
                    assignment_id,
                "type":
                    "UNSUPPORTED_CLAIM",
                "claim_id":
                    claim.get(
                        "claim_id"
                    ),
                "detail":
                    claim.get(
                        "claim"
                    )
                    or "",
                "reason":
                    claim.get(
                        "auditor_reason"
                    )
                    or "",
            }
        )

    return gaps


def run_evidence_pool(
    *,
    batch_dir: Path,
    skill_name: str,
) -> dict[str, Any]:
    batch_dir = (
        batch_dir.resolve()
    )

    resolved = (
        resolve_worker_runs(
            batch_dir
        )
    )

    pool_dir = (
        batch_dir
        / "evidence-pool"
    )

    pool_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    save_json(
        pool_dir
        / "resolved-workers.json",
        resolved,
    )

    assignment_records = []

    accepted_claims = []
    unsupported_claims = []
    rejected_evidence = []
    gaps = []
    quality_flags = []

    print(
        "===== B2 Evidence Pool =====",
        flush=True,
    )

    print(
        "Batch:",
        batch_dir,
        flush=True,
    )

    print(
        "Assignments:",
        len(resolved),
        flush=True,
    )

    print()

    for assignment_id, worker in (
        resolved.items()
    ):
        print(
            "================================"
        )

        print(
            "VALIDATE:",
            assignment_id,
            "/",
            worker["source"],
            flush=True,
        )

        print(
            "================================",
            flush=True,
        )

        worker_run = Path(
            worker["run_dir"]
        )

        worker_result_path = (
            worker_run
            / "worker-result.json"
        )

        tool_calls_path = (
            worker_run
            / "tool-calls.json"
        )

        result_path = (
            worker_run
            / "result.json"
        )

        for required in (
            worker_result_path,
            tool_calls_path,
            result_path,
        ):
            if not required.is_file():
                raise FileNotFoundError(
                    f"필수 Worker artifact가 없습니다: "
                    f"{required}"
                )

        raw_worker_result = load_json(
            worker_result_path
        )

        worker_runtime_result = (
            load_json(
                result_path
            )
        )

        tool_logs = load_json(
            tool_calls_path
        )

        assignment_dir = (
            pool_dir
            / assignment_id
        )

        assignment_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        deterministic = (
            validate_worker_result(
                raw_worker_result,
                tool_logs,
            )
        )

        deterministic_path = (
            assignment_dir
            / "deterministic-gate.json"
        )

        save_json(
            deterministic_path,
            deterministic,
        )

        print(
            "deterministic accepted:",
            deterministic[
                "summary"
            ][
                "accepted_claim_count"
            ],
            flush=True,
        )

        print(
            "deterministic unsupported:",
            deterministic[
                "summary"
            ][
                "unsupported_claim_count"
            ],
            flush=True,
        )

        semantic_root = (
            assignment_dir
            / "semantic-audits"
        )

        post_path = (
            assignment_dir
            / "post-audit-result.json"
        )

        audit_run_dir = None

        if post_path.is_file():
            print(
                "resume: existing post-audit result",
                flush=True,
            )

            post_audit = load_json(
                post_path
            )

            completed_audits = sorted(
                [
                    audit_dir
                    for audit_dir
                    in semantic_root.glob(
                        "audit-*"
                    )
                    if (
                        audit_dir
                        / "semantic-audit.json"
                    ).is_file()
                    and (
                        audit_dir
                        / "post-audit-result.json"
                    ).is_file()
                ],
                key=lambda value:
                    value.stat().st_mtime,
                reverse=True,
            )

            if completed_audits:
                audit_run_dir = (
                    completed_audits[0]
                )

        else:
            audit_runtime = run_audit(
                validated_result_path=
                    deterministic_path,
                tool_calls_path=
                    tool_calls_path,
                skill_name=
                    skill_name,
                output_root=
                    semantic_root,
            )

            if (
                audit_runtime.get(
                    "status"
                )
                != "completed"
            ):
                raise RuntimeError(
                    f"{assignment_id}: "
                    "Semantic Auditor 결과가 "
                    f"정상이 아닙니다: "
                    f"{audit_runtime.get('status')}"
                )

            audit_run_dir = Path(
                audit_runtime[
                    "run_dir"
                ]
            )

            packet = load_json(
                audit_run_dir
                / "audit-packet.json"
            )

            semantic_audit = load_json(
                audit_run_dir
                / "semantic-audit.json"
            )

            post_audit = (
                apply_audit_gate(
                    packet=packet,
                    audit_document=
                        semantic_audit,
                )
            )

            save_json(
                post_path,
                post_audit,
            )

            save_json(
                audit_run_dir
                / "post-audit-result.json",
                post_audit,
            )

        assignment_accepted = []

        for claim in (
            post_audit.get(
                "accepted_claims"
            )
            or []
        ):
            value = dict(
                claim
            )

            value[
                "assignment_id"
            ] = assignment_id

            value[
                "claim_ref"
            ] = (
                f"{assignment_id}:"
                f"{value.get('claim_id', '')}"
            )

            assignment_accepted.append(
                value
            )

            accepted_claims.append(
                value
            )

        for claim in (
            post_audit.get(
                "unsupported_claims"
            )
            or []
        ):
            value = dict(
                claim
            )

            value[
                "assignment_id"
            ] = assignment_id

            value[
                "claim_ref"
            ] = (
                f"{assignment_id}:"
                f"{value.get('claim_id', '')}"
            )

            unsupported_claims.append(
                value
            )

        for evidence in (
            post_audit.get(
                "rejected_evidence"
            )
            or []
        ):
            value = dict(
                evidence
            )

            value[
                "assignment_id"
            ] = assignment_id

            rejected_evidence.append(
                value
            )

        for flag in (
            post_audit.get(
                "quality_flags"
            )
            or []
        ):
            value = dict(
                flag
            )

            value[
                "assignment_id"
            ] = assignment_id

            quality_flags.append(
                value
            )

        assignment_gaps = (
            build_worker_gap_records(
                assignment_id=
                    assignment_id,
                worker_result=
                    raw_worker_result,
                post_audit=
                    post_audit,
            )
        )

        gaps.extend(
            assignment_gaps
        )

        assignment_record = {
            "assignment_id":
                assignment_id,
            "worker_source":
                worker[
                    "source"
                ],
            "worker_run_dir":
                str(
                    worker_run
                ),
            "worker_metrics":
                worker_runtime_result.get(
                    "metrics"
                ),
            "deterministic_summary":
                deterministic.get(
                    "summary"
                ),
            "semantic_audit_run_dir":
                (
                    str(
                        audit_run_dir
                    )
                    if audit_run_dir
                    else None
                ),
            "post_audit_summary":
                post_audit.get(
                    "summary"
                ),
            "accepted_claim_count":
                len(
                    assignment_accepted
                ),
            "gap_count":
                len(
                    assignment_gaps
                ),
        }

        assignment_records.append(
            assignment_record
        )

        save_json(
            assignment_dir
            / "assignment-summary.json",
            assignment_record,
        )

        print(
            "post-audit accepted:",
            len(
                assignment_accepted
            ),
            flush=True,
        )

        print(
            "gaps:",
            len(
                assignment_gaps
            ),
            flush=True,
        )

        print()

    source_registry = (
        build_source_registry(
            accepted_claims
        )
    )

    pool = {
        "stage":
            "B2-5",
        "created_at":
            utc_now(),
        "batch_dir":
            str(
                batch_dir
            ),
        "skill":
            skill_name,
        "assignments":
            assignment_records,
        "accepted_claims":
            accepted_claims,
        "unsupported_claims":
            unsupported_claims,
        "rejected_evidence":
            rejected_evidence,
        "quality_flags":
            quality_flags,
        "gaps":
            gaps,
        "sources":
            source_registry,
        "summary": {
            "assignment_count":
                len(
                    assignment_records
                ),
            "accepted_claim_count":
                len(
                    accepted_claims
                ),
            "unsupported_claim_count":
                len(
                    unsupported_claims
                ),
            "rejected_evidence_count":
                len(
                    rejected_evidence
                ),
            "quality_flag_count":
                len(
                    quality_flags
                ),
            "gap_count":
                len(
                    gaps
                ),
            "unique_verified_source_count":
                len(
                    source_registry
                ),
        },
    }

    save_json(
        pool_dir
        / "evidence-pool.json",
        pool,
    )

    print(
        "===== Evidence Pool Summary ====="
    )

    print(
        json.dumps(
            pool["summary"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print(
        "Result:",
        pool_dir
        / "evidence-pool.json",
    )

    return pool


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

    args = parser.parse_args()

    run_evidence_pool(
        batch_dir=
            args.batch,
        skill_name=
            args.skill,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
