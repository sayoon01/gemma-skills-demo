"""B2 independence finalization runtime.

Semantic 판단은 수행하지 않는다.

입력:
- cumulative state
- source independence result
- independence challenge result

Challenge의 검증된 family verdict를
Source Independence가 지정한 pending claim에만 적용하여
최종 cumulative state를 생성한다.
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import (
    datetime,
    timezone,
)
from pathlib import Path
from typing import Any


VERDICT_TO_STATUS = {
    "TRIANGULATED":
        "TRIANGULATED",
    "NOT_TRIANGULATED":
        "SINGLE_SOURCE",
    "UNKNOWN":
        "MULTI_SOURCE_PENDING_INDEPENDENCE",
}


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


def validate_inputs(
    *,
    cumulative: dict[str, Any],
    independence: dict[str, Any],
    challenge: dict[str, Any],
) -> None:
    if (
        independence.get(
            "status"
        )
        != "completed"
    ):
        raise ValueError(
            "Source Independence 결과가 "
            "completed가 아닙니다."
        )

    independence_validation = (
        independence.get(
            "validation"
        )
        or {}
    )

    if (
        independence_validation.get(
            "ok"
        )
        is not True
    ):
        raise ValueError(
            "Source Independence validation이 "
            "ok=true가 아닙니다."
        )

    if (
        challenge.get(
            "status"
        )
        != "completed"
    ):
        raise ValueError(
            "Independence Challenge 결과가 "
            "completed가 아닙니다."
        )

    challenge_validation = (
        challenge.get(
            "validation"
        )
        or {}
    )

    if (
        challenge_validation.get(
            "ok"
        )
        is not True
    ):
        raise ValueError(
            "Independence Challenge validation이 "
            "ok=true가 아닙니다."
        )

    audit_families = (
        (
            independence.get(
                "audit"
            )
            or {}
        ).get(
            "families"
        )
        or []
    )

    challenge_families = (
        (
            challenge.get(
                "challenge"
            )
            or {}
        ).get(
            "families"
        )
        or []
    )

    audit_refs = {
        family.get(
            "family_ref"
        )
        for family in audit_families
    }

    challenge_refs = {
        family.get(
            "family_ref"
        )
        for family in challenge_families
    }

    if audit_refs != challenge_refs:
        raise ValueError(
            "Source Independence와 Challenge의 "
            "family 집합이 일치하지 않습니다."
        )

    claim_refs = {
        claim.get(
            "claim_ref"
        )
        for claim in (
            cumulative.get(
                "claims"
            )
            or []
        )
    }

    for update in (
        independence.get(
            "claim_status_updates"
        )
        or []
    ):
        claim_ref = (
            update.get(
                "claim_ref"
            )
        )

        if (
            claim_ref
            not in claim_refs
        ):
            raise ValueError(
                "claim_status_updates의 claim을 "
                "cumulative state에서 찾지 못했습니다: "
                f"{claim_ref}"
            )

        family_ref = (
            update.get(
                "family_ref"
            )
        )

        if (
            family_ref
            not in challenge_refs
        ):
            raise ValueError(
                "claim_status_updates의 family를 "
                "Challenge 결과에서 찾지 못했습니다: "
                f"{family_ref}"
            )


def build_final_state(
    *,
    cumulative: dict[str, Any],
    independence: dict[str, Any],
    challenge: dict[str, Any],
    challenge_result_path: Path,
) -> dict[str, Any]:
    validate_inputs(
        cumulative=
            cumulative,
        independence=
            independence,
        challenge=
            challenge,
    )

    state = copy.deepcopy(
        cumulative
    )

    audit_families = (
        (
            independence.get(
                "audit"
            )
            or {}
        ).get(
            "families"
        )
        or []
    )

    challenge_families = (
        (
            challenge.get(
                "challenge"
            )
            or {}
        ).get(
            "families"
        )
        or []
    )

    audit_by_ref = {
        family[
            "family_ref"
        ]:
            family
        for family in audit_families
    }

    challenge_by_ref = {
        family[
            "family_ref"
        ]:
            family
        for family in challenge_families
    }

    #
    # Challenge 결과를 사람이 읽기 좋은
    # final family record로 정규화한다.
    #
    final_families = []

    for family_ref in (
        family[
            "family_ref"
        ]
        for family in challenge_families
    ):
        challenge_family = (
            challenge_by_ref[
                family_ref
            ]
        )

        audit_family = (
            audit_by_ref[
                family_ref
            ]
        )

        verdict = (
            challenge_family.get(
                "final_verdict"
            )
        )

        if (
            verdict
            not in VERDICT_TO_STATUS
        ):
            raise ValueError(
                f"{family_ref}: "
                "지원되지 않는 final_verdict "
                f"{verdict!r}"
            )

        final_families.append(
            {
                "family_ref":
                    family_ref,
                "claim_refs":
                    audit_family.get(
                        "claim_refs"
                    )
                    or [],
                "final_verdict":
                    verdict,
                "resolved_status":
                    VERDICT_TO_STATUS[
                        verdict
                    ],
                "reason":
                    challenge_family.get(
                        "reason"
                    )
                    or "",
                "pairwise":
                    challenge_family.get(
                        "pairwise"
                    )
                    or [],
            }
        )

    #
    # 핵심:
    # family의 모든 claim을 바꾸지 않는다.
    #
    # Source Independence가 실제 pending claim으로
    # 지정한 claim_status_updates만 Challenge verdict로
    # 최종 상태 전이한다.
    #
    status_by_claim = {}

    for update in (
        independence.get(
            "claim_status_updates"
        )
        or []
    ):
        claim_ref = (
            update[
                "claim_ref"
            ]
        )

        family_ref = (
            update[
                "family_ref"
            ]
        )

        verdict = (
            challenge_by_ref[
                family_ref
            ][
                "final_verdict"
            ]
        )

        status_by_claim[
            claim_ref
        ] = (
            VERDICT_TO_STATUS[
                verdict
            ]
        )

    for claim in (
        state.get(
            "claims"
        )
        or []
    ):
        claim_ref = (
            claim.get(
                "claim_ref"
            )
        )

        if (
            claim_ref
            in status_by_claim
        ):
            claim[
                "runtime_status"
            ] = (
                status_by_claim[
                    claim_ref
                ]
            )

    #
    # 상태 기반 claim index를 다시 계산한다.
    #
    triangulated_claim_refs = [
        claim[
            "claim_ref"
        ]
        for claim in (
            state.get(
                "claims"
            )
            or []
        )
        if (
            claim.get(
                "runtime_status"
            )
            == "TRIANGULATED"
        )
    ]

    pending_claim_refs = [
        claim[
            "claim_ref"
        ]
        for claim in (
            state.get(
                "claims"
            )
            or []
        )
        if (
            claim.get(
                "runtime_status"
            )
            == (
                "MULTI_SOURCE_"
                "PENDING_INDEPENDENCE"
            )
        )
    ]

    single_source_claim_refs = [
        claim[
            "claim_ref"
        ]
        for claim in (
            state.get(
                "claims"
            )
            or []
        )
        if (
            claim.get(
                "runtime_status"
            )
            == "SINGLE_SOURCE"
        )
    ]

    state[
        "stage"
    ] = "B2-8E"

    state[
        "created_at"
    ] = utc_now()

    state[
        "independence_challenge_result"
    ] = str(
        challenge_result_path
        .expanduser()
        .resolve()
    )

    state[
        "independence_families"
    ] = final_families

    state[
        "triangulated_claim_refs"
    ] = triangulated_claim_refs

    state[
        "pending_independence_claim_refs"
    ] = pending_claim_refs

    state[
        "single_source_claim_refs"
    ] = single_source_claim_refs

    summary = dict(
        state.get(
            "summary"
        )
        or {}
    )

    summary[
        "triangulated_claim_count"
    ] = len(
        triangulated_claim_refs
    )

    summary[
        "pending_independence_claim_count"
    ] = len(
        pending_claim_refs
    )

    summary[
        "single_source_claim_count"
    ] = len(
        single_source_claim_refs
    )

    summary[
        "independence_family_count"
    ] = len(
        final_families
    )

    summary[
        "independence_unknown_family_count"
    ] = sum(
        1
        for family in final_families
        if (
            family[
                "final_verdict"
            ]
            == "UNKNOWN"
        )
    )

    state[
        "summary"
    ] = summary

    return state


def run_finalizer(
    *,
    cumulative_path: Path,
    independence_result_path: Path,
    challenge_result_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    cumulative_path = (
        cumulative_path
        .expanduser()
        .resolve()
    )

    independence_result_path = (
        independence_result_path
        .expanduser()
        .resolve()
    )

    challenge_result_path = (
        challenge_result_path
        .expanduser()
        .resolve()
    )

    output_path = (
        output_path
        .expanduser()
        .resolve()
    )

    cumulative = load_json(
        cumulative_path
    )

    independence = load_json(
        independence_result_path
    )

    challenge = load_json(
        challenge_result_path
    )

    final_state = build_final_state(
        cumulative=
            cumulative,
        independence=
            independence,
        challenge=
            challenge,
        challenge_result_path=
            challenge_result_path,
    )

    save_json(
        output_path,
        final_state,
    )

    print(
        "===== B2 Independence Finalizer ====="
    )

    print(
        "Triangulated:",
        len(
            final_state.get(
                "triangulated_claim_refs"
            )
            or []
        ),
    )

    print(
        "Pending independence:",
        len(
            final_state.get(
                "pending_independence_claim_refs"
            )
            or []
        ),
    )

    print(
        "Single source:",
        len(
            final_state.get(
                "single_source_claim_refs"
            )
            or []
        ),
    )

    print(
        "Families:",
        len(
            final_state.get(
                "independence_families"
            )
            or []
        ),
    )

    print(
        "Result:",
        output_path,
    )

    return final_state


def main() -> int:
    parser = (
        argparse.ArgumentParser()
    )

    parser.add_argument(
        "--cumulative",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--independence-result",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--challenge-result",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = (
        parser.parse_args()
    )

    run_finalizer(
        cumulative_path=
            args.cumulative,
        independence_result_path=
            args.independence_result,
        challenge_result_path=
            args.challenge_result,
        output_path=
            args.output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
