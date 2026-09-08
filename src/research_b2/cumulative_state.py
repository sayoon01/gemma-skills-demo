"""B2 cumulative validated research state.

Semantic claim relationships are NOT decided here.

Input semantic decisions come from cumulative_matcher.py.
This module only:

- preserves validated claims from every wave;
- preserves semantic relation edges;
- measures running claim totals;
- measures per-wave novelty;
- merges source registries by canonical URL;
- records unresolved evidence states.

No domain-specific research logic belongs here.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .evidence_gate import canonical_url


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


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def claim_node(
    claim: dict[str, Any],
    *,
    wave: int,
) -> dict[str, Any]:
    return {
        "claim_ref":
            claim.get(
                "claim_ref"
            ),
        "wave":
            wave,
        "assignment_id":
            claim.get(
                "assignment_id"
            ),
        "claim_id":
            claim.get(
                "claim_id"
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
        "verified_evidence":
            claim.get(
                "verified_evidence"
            )
            or [],
    }


def build_source_registry(
    *,
    prior_pool: dict[str, Any],
    new_pool: dict[str, Any],
) -> list[dict[str, Any]]:
    """Canonical URL 기준으로 두 wave source registry를 합친다."""

    registry: dict[
        str,
        dict[str, Any],
    ] = {}

    for wave, pool in (
        (1, prior_pool),
        (2, new_pool),
    ):
        for source in (
            pool.get(
                "sources"
            )
            or []
        ):
            raw_url = (
                source.get(
                    "canonical_url"
                )
                or ""
            )

            url = (
                canonical_url(
                    raw_url
                )
                if raw_url
                else ""
            )

            if not url:
                continue

            record = registry.setdefault(
                url,
                {
                    "canonical_url":
                        url,
                    "domains": [],
                    "publishers": [],
                    "audited_source_types": [],
                    "audited_tiers": [],
                    "claim_refs": [],
                    "waves": [],
                    "source_records": [],
                },
            )

            domain = (
                source.get(
                    "domain"
                )
            )

            publisher = (
                source.get(
                    "claimed_publisher"
                )
            )

            source_type = (
                source.get(
                    "audited_source_type"
                )
            )

            tier = (
                source.get(
                    "audited_tier"
                )
            )

            claim_refs = (
                source.get(
                    "claim_ids"
                )
                or []
            )

            if (
                domain
                and domain
                not in record[
                    "domains"
                ]
            ):
                record[
                    "domains"
                ].append(
                    domain
                )

            if (
                publisher
                and publisher
                not in record[
                    "publishers"
                ]
            ):
                record[
                    "publishers"
                ].append(
                    publisher
                )

            if (
                source_type
                and source_type
                not in record[
                    "audited_source_types"
                ]
            ):
                record[
                    "audited_source_types"
                ].append(
                    source_type
                )

            if (
                tier is not None
                and tier
                not in record[
                    "audited_tiers"
                ]
            ):
                record[
                    "audited_tiers"
                ].append(
                    tier
                )

            for claim_ref in claim_refs:
                if (
                    claim_ref
                    not in record[
                        "claim_refs"
                    ]
                ):
                    record[
                        "claim_refs"
                    ].append(
                        claim_ref
                    )

            if wave not in record[
                "waves"
            ]:
                record[
                    "waves"
                ].append(
                    wave
                )

            record[
                "source_records"
            ].append(
                {
                    "wave":
                        wave,
                    "source_id":
                        source.get(
                            "source_id"
                        ),
                }
            )

    result = []

    for index, (
        _,
        record,
    ) in enumerate(
        sorted(
            registry.items()
        ),
        1,
    ):
        value = dict(
            record
        )

        value[
            "cumulative_source_id"
        ] = (
            f"CSRC{index:03d}"
        )

        result.append(
            value
        )

    return result


def build_state(
    *,
    prior_pool: dict[str, Any],
    new_pool: dict[str, Any],
    match_result: dict[str, Any],
) -> dict[str, Any]:
    validation = (
        match_result.get(
            "validation"
        )
        or {}
    )

    if validation.get(
        "ok"
    ) is not True:
        raise ValueError(
            "Semantic match validation이 "
            "ok=true가 아닙니다."
        )

    prior_claims = (
        prior_pool.get(
            "accepted_claims"
        )
        or []
    )

    new_claims = (
        new_pool.get(
            "accepted_claims"
        )
        or []
    )

    comparisons = (
        (
            match_result.get(
                "comparison"
            )
            or {}
        ).get(
            "comparisons"
        )
        or []
    )

    comparison_index = {
        item[
            "new_claim_ref"
        ]:
            item
        for item in comparisons
    }

    new_refs = {
        claim.get(
            "claim_ref"
        )
        for claim in new_claims
    }

    if (
        set(
            comparison_index
        )
        != new_refs
    ):
        raise ValueError(
            "Matcher comparison claim refs와 "
            "Wave 2 accepted claim refs가 "
            "일치하지 않습니다."
        )

    claim_nodes = [
        claim_node(
            claim,
            wave=1,
        )
        for claim in prior_claims
    ]

    claim_nodes.extend(
        claim_node(
            claim,
            wave=2,
        )
        for claim in new_claims
    )

    relation_edges = []

    novel_claim_refs = []

    same_claim_refs = []

    contradiction_claim_refs = []

    extension_claim_refs = []

    for item in comparisons:
        new_ref = (
            item[
                "new_claim_ref"
            ]
        )

        relation = (
            item[
                "relation"
            ]
        )

        is_novel = (
            item[
                "is_novel"
            ]
        )

        if is_novel:
            novel_claim_refs.append(
                new_ref
            )

        if relation == "SAME":
            same_claim_refs.append(
                new_ref
            )

        elif relation == "CONTRADICTS":
            contradiction_claim_refs.append(
                new_ref
            )

        elif relation == "EXTENDS":
            extension_claim_refs.append(
                new_ref
            )

        matched = (
            item.get(
                "matched_prior_claim_refs"
            )
            or []
        )

        if matched:
            for prior_ref in matched:
                relation_edges.append(
                    {
                        "from_claim_ref":
                            new_ref,
                        "to_claim_ref":
                            prior_ref,
                        "relation":
                            relation,
                        "is_novel":
                            is_novel,
                        "reason":
                            item.get(
                                "reason"
                            )
                            or "",
                    }
                )

        else:
            relation_edges.append(
                {
                    "from_claim_ref":
                        new_ref,
                    "to_claim_ref":
                        None,
                    "relation":
                        relation,
                    "is_novel":
                        is_novel,
                    "reason":
                        item.get(
                            "reason"
                        )
                        or "",
                }
            )

    wave1_running_claim_count = (
        len(
            prior_claims
        )
    )

    wave2_novel_claim_count = (
        len(
            novel_claim_refs
        )
    )

    cumulative_running_claim_count = (
        wave1_running_claim_count
        + wave2_novel_claim_count
    )

    #
    # Skill convergence용 측정값:
    # new materially distinct findings /
    # running cumulative claim total.
    #
    wave1_novelty_ratio_running = (
        1.0
        if wave1_running_claim_count
        else 0.0
    )

    wave2_novelty_ratio_running = (
        (
            wave2_novel_claim_count
            / cumulative_running_claim_count
        )
        if cumulative_running_claim_count
        else 0.0
    )

    sources = (
        build_source_registry(
            prior_pool=
                prior_pool,
            new_pool=
                new_pool,
        )
    )

    single_source_claim_refs = []

    pending_independence_claim_refs = []

    conflicting_status_claim_refs = []

    for claim in claim_nodes:
        status = (
            claim.get(
                "runtime_status"
            )
        )

        if status == "SINGLE_SOURCE":
            single_source_claim_refs.append(
                claim[
                    "claim_ref"
                ]
            )

        elif status == (
            "MULTI_SOURCE_"
            "PENDING_INDEPENDENCE"
        ):
            pending_independence_claim_refs.append(
                claim[
                    "claim_ref"
                ]
            )

        elif status == "CONFLICTING":
            conflicting_status_claim_refs.append(
                claim[
                    "claim_ref"
                ]
            )

    unsupported = []

    for wave, pool in (
        (1, prior_pool),
        (2, new_pool),
    ):
        for claim in (
            pool.get(
                "unsupported_claims"
            )
            or []
        ):
            unsupported.append(
                {
                    "wave":
                        wave,
                    "claim_ref":
                        claim.get(
                            "claim_ref"
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
            )

    gaps = []

    for wave, pool in (
        (1, prior_pool),
        (2, new_pool),
    ):
        for gap in (
            pool.get(
                "gaps"
            )
            or []
        ):
            value = dict(
                gap
            )

            value[
                "wave"
            ] = wave

            gaps.append(
                value
            )

    return {
        "stage":
            "B2-8C",
        "created_at":
            utc_now(),
        "waves": [
            1,
            2,
        ],
        "summary": {
            "wave_count":
                2,
            "wave1_accepted_claim_count":
                len(
                    prior_claims
                ),
            "wave2_accepted_claim_count":
                len(
                    new_claims
                ),
            "wave2_novel_claim_count":
                wave2_novel_claim_count,
            "running_claim_count":
                cumulative_running_claim_count,
            "physical_claim_node_count":
                len(
                    claim_nodes
                ),
            "relation_edge_count":
                len(
                    relation_edges
                ),
            "same_count":
                len(
                    same_claim_refs
                ),
            "extension_count":
                len(
                    extension_claim_refs
                ),
            "contradiction_count":
                len(
                    contradiction_claim_refs
                ),
            "cumulative_verified_source_count":
                len(
                    sources
                ),
            "single_source_claim_count":
                len(
                    single_source_claim_refs
                ),
            "pending_independence_claim_count":
                len(
                    pending_independence_claim_refs
                ),
            "unsupported_claim_count":
                len(
                    unsupported
                ),
            "gap_count":
                len(
                    gaps
                ),
        },
        "novelty": {
            "novel_claim_counts": [
                len(
                    prior_claims
                ),
                wave2_novel_claim_count,
            ],
            "running_claim_counts": [
                wave1_running_claim_count,
                cumulative_running_claim_count,
            ],
            "novelty_ratios_running_total": [
                wave1_novelty_ratio_running,
                wave2_novelty_ratio_running,
            ],
            "wave2_matcher_ratio_new_claims":
                (
                    match_result.get(
                        "metrics"
                    )
                    or {}
                ).get(
                    "novelty_ratio"
                ),
            "measurement_note": (
                "wave2_matcher_ratio_new_claims measures "
                "novel claims / accepted claims in Wave 2. "
                "novelty_ratios_running_total measures "
                "new materially distinct findings / running "
                "cumulative claim total and is kept separately "
                "for Skill convergence evaluation."
            ),
        },
        "novel_claim_refs":
            novel_claim_refs,
        "same_claim_refs":
            same_claim_refs,
        "extension_claim_refs":
            extension_claim_refs,
        "contradiction_claim_refs":
            contradiction_claim_refs,
        "single_source_claim_refs":
            single_source_claim_refs,
        "pending_independence_claim_refs":
            pending_independence_claim_refs,
        "conflicting_status_claim_refs":
            conflicting_status_claim_refs,
        "claims":
            claim_nodes,
        "relations":
            relation_edges,
        "sources":
            sources,
        "unsupported_claims":
            unsupported,
        "gaps":
            gaps,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--prior-pool",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--new-pool",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--match-result",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    prior_pool = load_json(
        args.prior_pool
    )

    new_pool = load_json(
        args.new_pool
    )

    match_result = load_json(
        args.match_result
    )

    state = build_state(
        prior_pool=
            prior_pool,
        new_pool=
            new_pool,
        match_result=
            match_result,
    )

    save_json(
        args.output,
        state,
    )

    print(
        "===== B2 Cumulative State ====="
    )

    print(
        json.dumps(
            state["summary"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print(
        "Novelty:"
    )

    print(
        json.dumps(
            state["novelty"],
            ensure_ascii=False,
            indent=2,
        )
    )

    print()
    print(
        "Result:",
        args.output.resolve(),
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
