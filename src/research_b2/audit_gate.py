"""B2 Semantic Audit 결과의 deterministic post-audit gate.

Semantic Auditor가 반환한 evidence state는 사용하지만,
Auditor가 반환한 claim verdict는 그대로 신뢰하지 않는다.

Runtime이 VERIFIED evidence 개수를 기준으로
claim 상태를 다시 계산한다.

Source independence와 최종 triangulation은
후속 aggregation 단계에서 확정한다.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ACCEPTED_EVIDENCE_STATE = "VERIFIED"

REJECTED_EVIDENCE_STATES = {
    "CONTENT_MISMATCH",
    "INSUFFICIENT_SUPPORT",
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


def index_packet_claims(
    packet: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    index = {}

    for claim in (
        packet.get("accepted_claims")
        or []
    ):
        if not isinstance(
            claim,
            dict,
        ):
            continue

        claim_id = (
            claim.get("claim_id")
            or ""
        )

        if claim_id:
            index[claim_id] = claim

    return index


def index_packet_evidence(
    packet: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    index = {}

    for claim in (
        packet.get("accepted_claims")
        or []
    ):
        for source in (
            claim.get("sources")
            or []
        ):
            if not isinstance(
                source,
                dict,
            ):
                continue

            evidence_id = (
                source.get(
                    "evidence_id"
                )
                or ""
            )

            if evidence_id:
                index[
                    evidence_id
                ] = source

    return index


def normalize_audit_document(
    document: dict[str, Any],
) -> dict[str, Any]:
    """semantic-audit.json 전체 또는 audit_result만 모두 지원한다."""

    if (
        "audit_result"
        in document
        and isinstance(
            document["audit_result"],
            dict,
        )
    ):
        return document[
            "audit_result"
        ]

    return document


def apply_audit_gate(
    *,
    packet: dict[str, Any],
    audit_document: dict[str, Any],
) -> dict[str, Any]:
    audit = normalize_audit_document(
        audit_document
    )

    claim_index = (
        index_packet_claims(
            packet
        )
    )

    evidence_index = (
        index_packet_evidence(
            packet
        )
    )

    accepted_claims = []
    unsupported_claims = []
    rejected_evidence = []
    consistency_warnings = []

    audited_claim_ids = set()

    for audited_claim in (
        audit.get("claims")
        or []
    ):
        if not isinstance(
            audited_claim,
            dict,
        ):
            continue

        claim_id = (
            audited_claim.get(
                "claim_id"
            )
            or ""
        )

        audited_claim_ids.add(
            claim_id
        )

        packet_claim = (
            claim_index.get(
                claim_id
            )
        )

        if packet_claim is None:
            consistency_warnings.append(
                {
                    "type":
                        "UNKNOWN_CLAIM_ID",
                    "claim_id":
                        claim_id,
                }
            )
            continue

        verified_evidence = []
        nonverified_evidence = []

        seen_evidence_ids = set()

        for audited_evidence in (
            audited_claim.get(
                "evidence"
            )
            or []
        ):
            if not isinstance(
                audited_evidence,
                dict,
            ):
                continue

            evidence_id = (
                audited_evidence.get(
                    "evidence_id"
                )
                or ""
            )

            seen_evidence_ids.add(
                evidence_id
            )

            source = (
                evidence_index.get(
                    evidence_id
                )
            )

            if source is None:
                consistency_warnings.append(
                    {
                        "type":
                            "UNKNOWN_EVIDENCE_ID",
                        "claim_id":
                            claim_id,
                        "evidence_id":
                            evidence_id,
                    }
                )
                continue

            state = (
                audited_evidence.get(
                    "state"
                )
                or ""
            )

            record = {
                "evidence_id":
                    evidence_id,
                "state":
                    state,
                "reason":
                    audited_evidence.get(
                        "reason"
                    )
                    or "",
                "audited_source_type":
                    audited_evidence.get(
                        "audited_source_type"
                    ),
                "audited_tier":
                    audited_evidence.get(
                        "audited_tier"
                    ),
                "source":
                    source,
            }

            if (
                state
                == ACCEPTED_EVIDENCE_STATE
            ):
                verified_evidence.append(
                    record
                )
            else:
                nonverified_evidence.append(
                    record
                )

                rejected_evidence.append(
                    {
                        "claim_id":
                            claim_id,
                        **record,
                    }
                )

        expected_evidence_ids = {
            source.get(
                "evidence_id"
            )
            for source
            in packet_claim.get(
                "sources"
            )
            or []
            if source.get(
                "evidence_id"
            )
        }

        missing_evidence_ids = (
            expected_evidence_ids
            - seen_evidence_ids
        )

        for evidence_id in sorted(
            missing_evidence_ids
        ):
            consistency_warnings.append(
                {
                    "type":
                        "MISSING_AUDIT_EVIDENCE",
                    "claim_id":
                        claim_id,
                    "evidence_id":
                        evidence_id,
                }
            )

        verified_count = len(
            verified_evidence
        )

        if verified_count == 0:
            runtime_status = (
                "UNSUPPORTED"
            )
        elif verified_count == 1:
            runtime_status = (
                "SINGLE_SOURCE"
            )
        else:
            # 아직 publisher / organization 독립성을
            # Runtime에서 확정하지 않았으므로
            # 여기서 TRIANGULATED라고 부르지 않는다.
            runtime_status = (
                "MULTI_SOURCE_PENDING_INDEPENDENCE"
            )

        auditor_verdict = (
            audited_claim.get(
                "verdict"
            )
            or ""
        )

        if (
            auditor_verdict
            != runtime_status
            and not (
                auditor_verdict
                == "TRIANGULATED"
                and runtime_status
                == "MULTI_SOURCE_PENDING_INDEPENDENCE"
            )
        ):
            consistency_warnings.append(
                {
                    "type":
                        "VERDICT_OVERRIDDEN",
                    "claim_id":
                        claim_id,
                    "auditor_verdict":
                        auditor_verdict,
                    "runtime_status":
                        runtime_status,
                }
            )

        result_claim = {
            "claim_id":
                claim_id,
            "claim":
                packet_claim.get(
                    "claim"
                )
                or "",
            "worker_support":
                packet_claim.get(
                    "worker_support"
                )
                or "",
            "runtime_status":
                runtime_status,
            "verified_evidence_count":
                verified_count,
            "verified_evidence":
                verified_evidence,
            "nonverified_evidence":
                nonverified_evidence,
            "auditor_verdict":
                auditor_verdict,
            "auditor_reason":
                audited_claim.get(
                    "reason"
                )
                or "",
        }

        if (
            runtime_status
            == "UNSUPPORTED"
        ):
            unsupported_claims.append(
                result_claim
            )
        else:
            accepted_claims.append(
                result_claim
            )

    missing_claim_ids = (
        set(
            claim_index
        )
        - audited_claim_ids
    )

    for claim_id in sorted(
        missing_claim_ids
    ):
        consistency_warnings.append(
            {
                "type":
                    "MISSING_AUDIT_CLAIM",
                "claim_id":
                    claim_id,
            }
        )

    return {
        "accepted_claims":
            accepted_claims,
        "unsupported_claims":
            unsupported_claims,
        "rejected_evidence":
            rejected_evidence,
        "quality_flags":
            audit.get(
                "quality_flags"
            )
            or [],
        "consistency_warnings":
            consistency_warnings,
        "summary": {
            "input_claim_count":
                len(
                    claim_index
                ),
            "accepted_claim_count":
                len(
                    accepted_claims
                ),
            "unsupported_claim_count":
                len(
                    unsupported_claims
                ),
            "verified_evidence_count":
                sum(
                    claim[
                        "verified_evidence_count"
                    ]
                    for claim
                    in accepted_claims
                ),
            "rejected_evidence_count":
                len(
                    rejected_evidence
                ),
            "warning_count":
                len(
                    consistency_warnings
                ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--packet",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--semantic-audit",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    packet = load_json(
        args.packet
    )

    audit_document = load_json(
        args.semantic_audit
    )

    result = apply_audit_gate(
        packet=packet,
        audit_document=
            audit_document,
    )

    save_json(
        args.output,
        result,
    )

    print(
        json.dumps(
            result["summary"],
            ensure_ascii=False,
            indent=2,
        )
    )

    if result[
        "consistency_warnings"
    ]:
        print()
        print(
            "===== WARNINGS ====="
        )

        for warning in result[
            "consistency_warnings"
        ]:
            print(
                json.dumps(
                    warning,
                    ensure_ascii=False,
                )
            )

    print()
    print(
        "saved:",
        args.output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
