"""B2 semantic source-independence auditor.

Python does not decide publisher/source independence.

Python responsibilities:

- construct SAME claim families;
- collect VERIFIED evidence;
- deduplicate identical canonical URLs;
- create stable source references;
- call Gemma with the active Skill and MD contract;
- mechanically validate IDs/schema;
- perform generic structured-output repair.

Semantic independence is decided by Gemma.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
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

from .evidence_gate import canonical_url
from .worker import extract_json_object


ROOT = Path(__file__).resolve().parents[2]


PAIR_RELATIONS = {
    "INDEPENDENT",
    "DEPENDENT",
    "UNKNOWN",
}


FAMILY_VERDICTS = {
    "TRIANGULATED",
    "NOT_TRIANGULATED",
    "UNKNOWN",
}


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


def sha256_text(
    text: str,
) -> str:
    return hashlib.sha256(
        text.encode("utf-8")
    ).hexdigest()


class UnionFind:
    def __init__(
        self,
        values: list[str],
    ) -> None:
        self.parent = {
            value: value
            for value in values
        }

    def find(
        self,
        value: str,
    ) -> str:
        parent = self.parent[
            value
        ]

        if parent != value:
            self.parent[
                value
            ] = self.find(
                parent
            )

        return self.parent[
            value
        ]

    def union(
        self,
        left: str,
        right: str,
    ) -> None:
        root_left = self.find(
            left
        )

        root_right = self.find(
            right
        )

        if root_left == root_right:
            return

        root = min(
            root_left,
            root_right,
        )

        other = (
            root_right
            if root == root_left
            else root_left
        )

        self.parent[
            other
        ] = root


def build_same_components(
    state: dict[str, Any],
) -> dict[
    str,
    list[str],
]:
    claim_refs = [
        claim[
            "claim_ref"
        ]
        for claim in (
            state.get(
                "claims"
            )
            or []
        )
    ]

    uf = UnionFind(
        claim_refs
    )

    known = set(
        claim_refs
    )

    for edge in (
        state.get(
            "relations"
        )
        or []
    ):
        if (
            edge.get(
                "relation"
            )
            != "SAME"
        ):
            continue

        left = (
            edge.get(
                "from_claim_ref"
            )
        )

        right = (
            edge.get(
                "to_claim_ref"
            )
        )

        if (
            left in known
            and right in known
        ):
            uf.union(
                left,
                right,
            )

    components: dict[
        str,
        list[str],
    ] = {}

    for claim_ref in claim_refs:
        root = uf.find(
            claim_ref
        )

        components.setdefault(
            root,
            [],
        ).append(
            claim_ref
        )

    for refs in components.values():
        refs.sort()

    return components


def build_family_packets(
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    claims = {
        claim[
            "claim_ref"
        ]:
            claim
        for claim in (
            state.get(
                "claims"
            )
            or []
        )
    }

    pending_refs = set(
        state.get(
            "pending_independence_claim_refs"
        )
        or []
    )

    components = (
        build_same_components(
            state
        )
    )

    root_by_claim = {}

    for root, refs in (
        components.items()
    ):
        for ref in refs:
            root_by_claim[
                ref
            ] = root

    target_roots = {
        root_by_claim[
            ref
        ]
        for ref in pending_refs
        if ref in root_by_claim
    }

    families = []

    for root in sorted(
        target_roots
    ):
        family_claim_refs = (
            components[root]
        )

        pending_members = sorted(
            pending_refs
            & set(
                family_claim_refs
            )
        )

        source_by_url: dict[
            str,
            dict[str, Any],
        ] = {}

        for claim_ref in (
            family_claim_refs
        ):
            claim = claims[
                claim_ref
            ]

            for evidence in (
                claim.get(
                    "verified_evidence"
                )
                or []
            ):
                if (
                    evidence.get(
                        "state"
                    )
                    != "VERIFIED"
                ):
                    continue

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

                raw_url = (
                    retrieved.get(
                        "url"
                    )
                    or worker_source.get(
                        "url"
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

                evidence_ref = (
                    f"{claim_ref}:"
                    f"{evidence.get('evidence_id', '')}"
                )

                record = (
                    source_by_url.setdefault(
                        url,
                        {
                            "canonical_url":
                                url,
                            "claim_refs": [],
                            "evidence_refs": [],
                            "title":
                                (
                                    retrieved.get(
                                        "title"
                                    )
                                    or worker_source.get(
                                        "title"
                                    )
                                    or ""
                                ),
                            "publisher":
                                worker_source.get(
                                    "publisher"
                                )
                                or "",
                            "domain":
                                retrieved.get(
                                    "domain"
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
                            "worker_excerpt":
                                worker_source.get(
                                    "excerpt"
                                )
                                or "",
                            "retrieved_content":
                                retrieved.get(
                                    "content"
                                )
                                or "",
                        },
                    )
                )

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

                if (
                    evidence_ref
                    not in record[
                        "evidence_refs"
                    ]
                ):
                    record[
                        "evidence_refs"
                    ].append(
                        evidence_ref
                    )

        sources = []

        for index, (
            _,
            source,
        ) in enumerate(
            sorted(
                source_by_url.items()
            ),
            1,
        ):
            value = dict(
                source
            )

            value[
                "source_ref"
            ] = (
                f"S{index:03d}"
            )

            sources.append(
                value
            )

        family_ref = min(
            pending_members
            or family_claim_refs
        )

        families.append(
            {
                "family_ref":
                    family_ref,
                "claim_refs":
                    family_claim_refs,
                "pending_claim_refs":
                    pending_members,
                "claims": [
                    {
                        "claim_ref":
                            ref,
                        "claim":
                            claims[
                                ref
                            ].get(
                                "claim"
                            ),
                        "runtime_status":
                            claims[
                                ref
                            ].get(
                                "runtime_status"
                            ),
                    }
                    for ref in
                    family_claim_refs
                ],
                "sources":
                    sources,
            }
        )

    return families


def expected_pairs(
    family: dict[str, Any],
) -> set[
    tuple[str, str]
]:
    refs = sorted(
        source[
            "source_ref"
        ]
        for source in (
            family.get(
                "sources"
            )
            or []
        )
    )

    return {
        tuple(
            sorted(
                pair
            )
        )
        for pair in itertools.combinations(
            refs,
            2,
        )
    }


def validate_result(
    *,
    result: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    errors = []

    if not isinstance(
        result,
        dict,
    ):
        return {
            "ok":
                False,
            "errors": [
                "최상위 결과가 객체가 아닙니다."
            ],
        }

    if (
        set(result)
        != {"families"}
    ):
        errors.append(
            "최상위 field는 families만 "
            "허용됩니다."
        )

    output_families = (
        result.get(
            "families"
        )
    )

    if not isinstance(
        output_families,
        list,
    ):
        return {
            "ok":
                False,
            "errors":
                errors
                + [
                    "families가 list가 아닙니다."
                ],
        }

    expected = {
        family[
            "family_ref"
        ]:
            family
        for family in (
            packet.get(
                "families"
            )
            or []
        )
    }

    seen = set()

    allowed_fields = {
        "family_ref",
        "claim_refs",
        "pairwise",
        "verdict",
        "independent_verified_source_count",
        "reason",
    }

    for index, family in enumerate(
        output_families,
        1,
    ):
        prefix = (
            f"families[{index}]"
        )

        if not isinstance(
            family,
            dict,
        ):
            errors.append(
                f"{prefix}가 객체가 아닙니다."
            )
            continue

        unexpected = (
            set(family)
            - allowed_fields
        )

        if unexpected:
            errors.append(
                f"{prefix} 허용되지 않은 field: "
                + ", ".join(
                    sorted(
                        unexpected
                    )
                )
            )

        family_ref = (
            family.get(
                "family_ref"
            )
        )

        if family_ref not in expected:
            errors.append(
                f"{prefix} 잘못된 family_ref: "
                f"{family_ref!r}"
            )
            continue

        if family_ref in seen:
            errors.append(
                "중복 family_ref: "
                f"{family_ref}"
            )

        seen.add(
            family_ref
        )

        expected_family = (
            expected[
                family_ref
            ]
        )

        if set(
            family.get(
                "claim_refs"
            )
            or []
        ) != set(
            expected_family[
                "claim_refs"
            ]
        ):
            errors.append(
                f"{family_ref}: claim_refs가 "
                "입력 family와 일치하지 않습니다."
            )

        verdict = (
            family.get(
                "verdict"
            )
        )

        if verdict not in FAMILY_VERDICTS:
            errors.append(
                f"{family_ref}: 잘못된 verdict "
                f"{verdict!r}"
            )

        count = (
            family.get(
                "independent_verified_source_count"
            )
        )

        source_count = len(
            expected_family[
                "sources"
            ]
        )

        if (
            not isinstance(
                count,
                int,
            )
            or isinstance(
                count,
                bool,
            )
            or not (
                0
                <= count
                <= source_count
            )
        ):
            errors.append(
                f"{family_ref}: "
                "independent_verified_source_count가 "
                "유효하지 않습니다."
            )

        reason = (
            family.get(
                "reason"
            )
        )

        if (
            not isinstance(
                reason,
                str,
            )
            or not reason.strip()
        ):
            errors.append(
                f"{family_ref}: reason이 "
                "비어 있습니다."
            )

        pairwise = (
            family.get(
                "pairwise"
            )
        )

        if not isinstance(
            pairwise,
            list,
        ):
            errors.append(
                f"{family_ref}: pairwise가 "
                "list가 아닙니다."
            )
            pairwise = []

        expected_pair_set = (
            expected_pairs(
                expected_family
            )
        )

        seen_pairs = set()

        valid_source_refs = {
            source[
                "source_ref"
            ]
            for source in (
                expected_family[
                    "sources"
                ]
            )
        }

        for pair_index, pair in enumerate(
            pairwise,
            1,
        ):
            pair_prefix = (
                f"{family_ref}.pairwise"
                f"[{pair_index}]"
            )

            if not isinstance(
                pair,
                dict,
            ):
                errors.append(
                    f"{pair_prefix}가 객체가 아닙니다."
                )
                continue

            if set(pair) != {
                "source_a_ref",
                "source_b_ref",
                "relation",
                "reason",
            }:
                errors.append(
                    f"{pair_prefix}: field schema가 "
                    "일치하지 않습니다."
                )

            source_a = (
                pair.get(
                    "source_a_ref"
                )
            )

            source_b = (
                pair.get(
                    "source_b_ref"
                )
            )

            if (
                source_a
                not in valid_source_refs
                or source_b
                not in valid_source_refs
                or source_a == source_b
            ):
                errors.append(
                    f"{pair_prefix}: 잘못된 "
                    "source pair"
                )
                continue

            normalized = tuple(
                sorted(
                    (
                        source_a,
                        source_b,
                    )
                )
            )

            if normalized in seen_pairs:
                errors.append(
                    f"{pair_prefix}: 중복 pair"
                )

            seen_pairs.add(
                normalized
            )

            relation = (
                pair.get(
                    "relation"
                )
            )

            if relation not in PAIR_RELATIONS:
                errors.append(
                    f"{pair_prefix}: 잘못된 "
                    f"relation {relation!r}"
                )

            pair_reason = (
                pair.get(
                    "reason"
                )
            )

            if (
                not isinstance(
                    pair_reason,
                    str,
                )
                or not pair_reason.strip()
            ):
                errors.append(
                    f"{pair_prefix}: reason이 "
                    "비어 있습니다."
                )

        if (
            seen_pairs
            != expected_pair_set
        ):
            errors.append(
                f"{family_ref}: 모든 source pair가 "
                "정확히 한 번씩 평가되지 않았습니다."
            )

        independent_pairs = [
            pair
            for pair in pairwise
            if (
                isinstance(
                    pair,
                    dict,
                )
                and pair.get(
                    "relation"
                )
                == "INDEPENDENT"
            )
        ]

        unknown_pairs = [
            pair
            for pair in pairwise
            if (
                isinstance(
                    pair,
                    dict,
                )
                and pair.get(
                    "relation"
                )
                == "UNKNOWN"
            )
        ]

        #
        # Semantic relation 자체는 Gemma가 정했다.
        # Runtime은 출력 consistency만 검사한다.
        #
        if (
            verdict
            == "TRIANGULATED"
            and not independent_pairs
        ):
            errors.append(
                f"{family_ref}: TRIANGULATED인데 "
                "INDEPENDENT pair가 없습니다."
            )

        if (
            verdict
            == "TRIANGULATED"
            and isinstance(
                count,
                int,
            )
            and count < 2
        ):
            errors.append(
                f"{family_ref}: TRIANGULATED인데 "
                "independent source count < 2"
            )

        if (
            verdict
            == "NOT_TRIANGULATED"
            and independent_pairs
        ):
            errors.append(
                f"{family_ref}: NOT_TRIANGULATED인데 "
                "INDEPENDENT pair가 존재합니다."
            )

        if (
            verdict
            == "UNKNOWN"
            and not unknown_pairs
        ):
            errors.append(
                f"{family_ref}: UNKNOWN인데 "
                "UNKNOWN pair가 없습니다."
            )

    missing = (
        set(expected)
        - seen
    )

    if missing:
        errors.append(
            "누락된 family: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    return {
        "ok":
            not errors,
        "errors":
            errors,
        "expected_family_count":
            len(
                expected
            ),
        "seen_family_count":
            len(
                seen
            ),
    }


def build_repair_prompt(
    *,
    invalid_result: dict[str, Any],
    validation: dict[str, Any],
    packet: dict[str, Any],
) -> str:
    return (
        "# Source Independence Output Repair\n\n"
        "The previous independence audit failed runtime "
        "schema or consistency validation.\n\n"
        "This is a repair pass only. "
        "Do not perform new research and do not introduce "
        "new sources or claims.\n\n"
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
        "# Required Input Packet\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Invalid Output\n\n"
        + json.dumps(
            invalid_result,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Repair Requirements\n\n"
        "- Preserve semantic judgments whenever possible.\n"
        "- Return each family exactly once.\n"
        "- Return every required source pair exactly once.\n"
        "- Use only INDEPENDENT, DEPENDENT, UNKNOWN for pair relations.\n"
        "- Use only TRIANGULATED, NOT_TRIANGULATED, UNKNOWN "
        "for family verdicts.\n"
        "- Do not invent family refs, claim refs, or source refs.\n"
        "- Return JSON only.\n"
    )


def run_independence_audit(
    *,
    cumulative_path: Path,
    skill_name: str,
    output_root: Path,
) -> dict[str, Any]:
    state = load_json(
        cumulative_path
    )

    families = (
        build_family_packets(
            state
        )
    )

    if not families:
        raise ValueError(
            "pending independence family가 없습니다."
        )

    packet = {
        "families":
            families,
    }

    contract_path = (
        ROOT
        / "runtime"
        / "b2"
        / "source-independence.md"
    )

    contract = (
        contract_path.read_text(
            encoding="utf-8"
        )
    )

    evidence_policy = (
        ROOT
        / "runtime"
        / "b2"
        / "evidence-policy.md"
    ).read_text(
        encoding="utf-8"
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

    system_prompt = (
        "# Active Agent Skill\n\n"
        "<skill>\n"
        + skill["body"]
        + "\n</skill>\n\n"
        "# Evidence Policy\n\n"
        + evidence_policy
        + "\n\n"
        "# Source Independence Contract\n\n"
        + contract
    )

    user_prompt = (
        "# Cumulative Evidence Families\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "Evaluate only source provenance and independence. "
        "Do not perform new research. Return JSON only."
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="independence-",
            dir=output_root,
        )
    )

    save_json(
        run_dir
        / "independence-packet.json",
        packet,
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
        "===== B2 Source Independence Auditor =====",
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
        "Families:",
        len(
            families
        ),
        flush=True,
    )

    for family in families:
        print(
            family[
                "family_ref"
            ],
            "claims=",
            len(
                family[
                    "claim_refs"
                ]
            ),
            "sources=",
            len(
                family[
                    "sources"
                ]
            ),
            flush=True,
        )

    started = (
        time.monotonic()
    )

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
                    user_prompt,
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
        / "response.json",
        response,
    )

    raw = (
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
        / "independence-raw.txt"
    ).write_text(
        raw,
        encoding="utf-8",
    )

    if not raw.strip():
        raise RuntimeError(
            "Independence Auditor가 빈 "
            "content를 반환했습니다."
        )

    audit = (
        extract_json_object(
            raw
        )
    )

    validation = (
        validate_result(
            result=audit,
            packet=packet,
        )
    )

    initial_validation = dict(
        validation
    )

    save_json(
        run_dir
        / "independence-initial.json",
        audit,
    )

    save_json(
        run_dir
        / "independence-initial-validation.json",
        validation,
    )

    repair_attempts = []

    for attempt in range(
        1,
        3,
    ):
        if validation["ok"]:
            break

        print(
            "Initial/previous independence output invalid; "
            f"repair attempt {attempt}.",
            flush=True,
        )

        repair_prompt = (
            build_repair_prompt(
                invalid_result=
                    audit,
                validation=
                    validation,
                packet=
                    packet,
            )
        )

        repair_started = (
            time.monotonic()
        )

        repair_response = (
            client.chat(
                [
                    {
                        "role":
                            "system",
                        "content":
                            system_prompt,
                    },
                    {
                        "role":
                            "user",
                        "content":
                            repair_prompt,
                    },
                ],
                think=False,
                response_format="json",
            )
        )

        repair_elapsed = (
            time.monotonic()
            - repair_started
        )

        save_json(
            run_dir
            / f"repair-{attempt:02d}-response.json",
            repair_response,
        )

        repair_raw = (
            repair_response.get(
                "message",
                {},
            ).get(
                "content"
            )
            or ""
        )

        (
            run_dir
            / f"repair-{attempt:02d}-raw.txt"
        ).write_text(
            repair_raw,
            encoding="utf-8",
        )

        if not repair_raw.strip():
            repair_attempts.append(
                {
                    "attempt":
                        attempt,
                    "status":
                        "empty_response",
                    "elapsed_seconds":
                        round(
                            repair_elapsed,
                            3,
                        ),
                }
            )
            continue

        try:
            candidate = (
                extract_json_object(
                    repair_raw
                )
            )

        except Exception as exc:
            repair_attempts.append(
                {
                    "attempt":
                        attempt,
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
            validate_result(
                result=
                    candidate,
                packet=
                    packet,
            )
        )

        save_json(
            run_dir
            / f"repair-{attempt:02d}-audit.json",
            candidate,
        )

        save_json(
            run_dir
            / f"repair-{attempt:02d}-validation.json",
            candidate_validation,
        )

        repair_attempts.append(
            {
                "attempt":
                    attempt,
                "status":
                    (
                        "valid"
                        if candidate_validation[
                            "ok"
                        ]
                        else "invalid"
                    ),
                "elapsed_seconds":
                    round(
                        repair_elapsed,
                        3,
                    ),
                "errors":
                    candidate_validation[
                        "errors"
                    ],
            }
        )

        audit = candidate
        validation = (
            candidate_validation
        )

    updates = []

    if validation["ok"]:
        family_packet_index = {
            family[
                "family_ref"
            ]:
                family
            for family in families
        }

        for family in (
            audit.get(
                "families"
            )
            or []
        ):
            verdict = (
                family[
                    "verdict"
                ]
            )

            if verdict == (
                "TRIANGULATED"
            ):
                resolved_status = (
                    "TRIANGULATED"
                )

            elif verdict == (
                "NOT_TRIANGULATED"
            ):
                resolved_status = (
                    "SINGLE_SOURCE"
                )

            else:
                resolved_status = (
                    "MULTI_SOURCE_"
                    "PENDING_INDEPENDENCE"
                )

            packet_family = (
                family_packet_index[
                    family[
                        "family_ref"
                    ]
                ]
            )

            for claim_ref in (
                packet_family[
                    "pending_claim_refs"
                ]
            ):
                updates.append(
                    {
                        "claim_ref":
                            claim_ref,
                        "family_ref":
                            family[
                                "family_ref"
                            ],
                        "family_verdict":
                            verdict,
                        "resolved_status":
                            resolved_status,
                    }
                )

    final = {
        "status":
            (
                "completed"
                if validation[
                    "ok"
                ]
                else "invalid_independence_output"
            ),
        "stage":
            "B2-8D",
        "created_at":
            utc_now(),
        "run_dir":
            str(
                run_dir
            ),
        "model":
            client.model,
        "skill":
            skill["name"],
        "skill_sha256":
            skill[
                "sha256"
            ],
        "contract_sha256":
            sha256_text(
                contract
            ),
        "cumulative_path":
            str(
                cumulative_path.resolve()
            ),
        "initial_validation":
            initial_validation,
        "repair_attempts":
            repair_attempts,
        "validation":
            validation,
        "audit":
            audit,
        "claim_status_updates":
            updates,
        "metrics": {
            "family_count":
                len(
                    families
                ),
            "elapsed_seconds":
                round(
                    elapsed,
                    3,
                ),
        },
        "discovery_errors":
            discovery_errors,
    }

    save_json(
        run_dir
        / "result.json",
        final,
    )

    save_json(
        run_dir
        / "independence.json",
        audit,
    )

    print()
    print(
        "Audit time:",
        f"{elapsed:.3f}초",
        flush=True,
    )

    print(
        "Validation:",
        validation[
            "ok"
        ],
        flush=True,
    )

    if validation["ok"]:
        print()

        for family in (
            audit[
                "families"
            ]
        ):
            print(
                family[
                    "family_ref"
                ],
                "=>",
                family[
                    "verdict"
                ],
                "independent=",
                family[
                    "independent_verified_source_count"
                ],
                flush=True,
            )

    print(
        "Result:",
        run_dir
        / "result.json",
        flush=True,
    )

    return final


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--cumulative",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--skill",
        default="deep-research",
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    result = (
        run_independence_audit(
            cumulative_path=
                args.cumulative,
            skill_name=
                args.skill,
            output_root=
                args.output_root,
        )
    )

    return (
        0
        if result[
            "status"
        ]
        == "completed"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
