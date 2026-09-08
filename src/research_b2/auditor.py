"""B2 Semantic Evidence Auditor.

Deterministic Evidence Gate를 통과한 Claim/Source를
실제 fetched content와 비교한다.

검증 행동은 runtime/b2/verification.md 및
evidence-policy.md와 활성 SKILL.md에서 정의한다.

이 Auditor에는 web tool을 제공하지 않는다.
"""

from __future__ import annotations

import argparse
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
    build_fetch_index,
    canonical_url,
)
from .worker import extract_json_object


ROOT = Path(__file__).resolve().parents[2]


ALLOWED_EVIDENCE_STATES = {
    "VERIFIED",
    "CONTENT_MISMATCH",
    "INSUFFICIENT_SUPPORT",
}


ALLOWED_CLAIM_VERDICTS = {
    "TRIANGULATED",
    "SINGLE_SOURCE",
    "UNSUPPORTED",
    "CONFLICTING",
}


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


def load_json(
    path: Path,
) -> Any:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def build_audit_packet(
    validated_result: dict[str, Any],
    tool_logs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Accepted Claim과 실제 fetched content를 Audit Packet으로 만든다."""

    fetch_index = build_fetch_index(
        tool_logs
    )

    packet_claims = []

    for claim_index, claim in enumerate(
        validated_result.get(
            "accepted_claims"
        )
        or [],
        1,
    ):
        claim_id = (
            f"C{claim_index:03d}"
        )

        packet_sources = []

        for source_index, source in enumerate(
            claim.get("sources")
            or [],
            1,
        ):
            evidence_id = (
                f"{claim_id}-"
                f"E{source_index:03d}"
            )

            source_url = (
                source.get(
                    "retrieved_url"
                )
                or source.get("url")
                or ""
            )

            fetch = fetch_index.get(
                canonical_url(
                    source_url
                )
            )

            if fetch is None:
                # Deterministic Gate를 통과했는데
                # fetch가 사라진 경우 Runtime consistency 오류.
                raise ValueError(
                    "검증된 Source의 fetch record를 "
                    f"찾지 못했습니다: {source_url}"
                )

            packet_sources.append(
                {
                    "evidence_id":
                        evidence_id,
                    "worker_source": {
                        "title":
                            source.get(
                                "title"
                            )
                            or "",
                        "publisher":
                            source.get(
                                "publisher"
                            )
                            or "",
                        "url":
                            source.get(
                                "url"
                            )
                            or "",
                        "source_type":
                            source.get(
                                "source_type"
                            )
                            or "",
                        "tier":
                            source.get(
                                "tier"
                            ),
                        "excerpt":
                            source.get(
                                "excerpt"
                            )
                            or "",
                    },
                    "retrieved_source": {
                        "title":
                            fetch.get(
                                "title"
                            )
                            or "",
                        "url":
                            fetch.get(
                                "final_url"
                            )
                            or "",
                        "domain":
                            fetch.get(
                                "domain"
                            )
                            or "",
                        "content":
                            fetch.get(
                                "content"
                            )
                            or "",
                        "content_chars":
                            fetch.get(
                                "content_chars"
                            )
                            or 0,
                    },
                }
            )

        packet_claims.append(
            {
                "claim_id":
                    claim_id,
                "claim":
                    claim.get(
                        "claim"
                    )
                    or "",
                "worker_support":
                    claim.get(
                        "support"
                    )
                    or "",
                "worker_confidence":
                    claim.get(
                        "confidence"
                    )
                    or "",
                "deterministic_status":
                    claim.get(
                        "validation_status"
                    )
                    or "",
                "sources":
                    packet_sources,
            }
        )

    unsupported = []

    for index, claim in enumerate(
        validated_result.get(
            "unsupported_claims"
        )
        or [],
        1,
    ):
        unsupported.append(
            {
                "claim_id":
                    f"U{index:03d}",
                "claim":
                    claim.get(
                        "claim"
                    )
                    or "",
                "reason":
                    "No source survived deterministic verification.",
            }
        )

    return {
        "accepted_claims":
            packet_claims,
        "already_unsupported_claims":
            unsupported,
    }


def build_system_prompt(
    *,
    skill: dict[str, Any],
    contracts: dict[str, str],
) -> str:
    return (
        "# Active Agent Skill\n\n"
        "<skill>\n"
        + skill["body"]
        + "\n</skill>\n\n"
        + contracts["verification"]
        + "\n\n"
        + contracts["evidence-policy"]
    )


def build_user_prompt(
    packet: dict[str, Any],
) -> str:
    return (
        "# Semantic Evidence Audit Packet\n\n"
        "Audit only the evidence supplied below.\n"
        "Do not search for new sources.\n"
        "Do not repair claims using model memory.\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
    )


def validate_audit_ids(
    *,
    packet: dict[str, Any],
    audit_result: dict[str, Any],
) -> dict[str, Any]:
    """Auditor가 없는 Claim/Evidence ID를 발명하지 않았는지 확인."""

    expected_claim_ids = {
        claim["claim_id"]
        for claim
        in packet[
            "accepted_claims"
        ]
    }

    expected_evidence_ids = {
        source["evidence_id"]
        for claim
        in packet[
            "accepted_claims"
        ]
        for source
        in claim["sources"]
    }

    seen_claim_ids = set()
    seen_evidence_ids = set()

    errors = []

    claims = (
        audit_result.get("claims")
        or []
    )

    if not isinstance(
        claims,
        list,
    ):
        return {
            "ok": False,
            "errors": [
                "audit_result.claims가 list가 아닙니다."
            ],
        }

    for claim in claims:
        if not isinstance(
            claim,
            dict,
        ):
            errors.append(
                "claim entry가 객체가 아닙니다."
            )
            continue

        claim_id = (
            claim.get("claim_id")
            or ""
        )

        seen_claim_ids.add(
            claim_id
        )

        if (
            claim_id
            not in expected_claim_ids
        ):
            errors.append(
                "알 수 없는 claim_id: "
                f"{claim_id}"
            )

        verdict = (
            claim.get("verdict")
            or ""
        )

        if (
            verdict
            not in ALLOWED_CLAIM_VERDICTS
        ):
            errors.append(
                "잘못된 verdict: "
                f"{claim_id} / {verdict}"
            )

        for evidence in (
            claim.get("evidence")
            or []
        ):
            if not isinstance(
                evidence,
                dict,
            ):
                errors.append(
                    f"{claim_id}: evidence가 객체가 아닙니다."
                )
                continue

            evidence_id = (
                evidence.get(
                    "evidence_id"
                )
                or ""
            )

            seen_evidence_ids.add(
                evidence_id
            )

            if (
                evidence_id
                not in expected_evidence_ids
            ):
                errors.append(
                    "알 수 없는 evidence_id: "
                    f"{evidence_id}"
                )

            state = (
                evidence.get("state")
                or ""
            )

            if (
                state
                not in ALLOWED_EVIDENCE_STATES
            ):
                errors.append(
                    "잘못된 evidence state: "
                    f"{evidence_id} / {state}"
                )

    missing_claims = (
        expected_claim_ids
        - seen_claim_ids
    )

    if missing_claims:
        errors.append(
            "Auditor가 누락한 claim_id: "
            + ", ".join(
                sorted(
                    missing_claims
                )
            )
        )

    missing_evidence = (
        expected_evidence_ids
        - seen_evidence_ids
    )

    if missing_evidence:
        errors.append(
            "Auditor가 누락한 evidence_id: "
            + ", ".join(
                sorted(
                    missing_evidence
                )
            )
        )

    return {
        "ok":
            len(errors) == 0,
        "errors":
            errors,
        "expected_claim_count":
            len(
                expected_claim_ids
            ),
        "seen_claim_count":
            len(
                seen_claim_ids
            ),
        "expected_evidence_count":
            len(
                expected_evidence_ids
            ),
        "seen_evidence_count":
            len(
                seen_evidence_ids
            ),
    }


def run_audit(
    *,
    validated_result_path: Path,
    tool_calls_path: Path,
    skill_name: str,
    output_root: Path,
) -> dict[str, Any]:
    validated_result = load_json(
        validated_result_path
    )

    tool_logs = load_json(
        tool_calls_path
    )

    packet = build_audit_packet(
        validated_result,
        tool_logs,
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

    client = OllamaClient()

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="audit-",
            dir=output_root,
        )
    )

    save_json(
        run_dir
        / "audit-packet.json",
        packet,
    )

    messages = [
        {
            "role": "system",
            "content":
                build_system_prompt(
                    skill=skill,
                    contracts=contracts,
                ),
        },
        {
            "role": "user",
            "content":
                build_user_prompt(
                    packet
                ),
        },
    ]

    print(
        "===== B2 Semantic Evidence Auditor =====",
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
        "Claims to audit:",
        len(
            packet[
                "accepted_claims"
            ]
        ),
        flush=True,
    )

    evidence_count = sum(
        len(
            claim["sources"]
        )
        for claim
        in packet[
            "accepted_claims"
        ]
    )

    print(
        "Evidence to audit:",
        evidence_count,
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
        / "audit-final-raw.txt"
    ).write_text(
        raw_text,
        encoding="utf-8",
    )

    audit_result = (
        extract_json_object(
            raw_text
        )
    )

    integrity = (
        validate_audit_ids(
            packet=packet,
            audit_result=audit_result,
        )
    )

    result = {
        "status":
            (
                "completed"
                if integrity["ok"]
                else "invalid_audit_output"
            ),
        "stage":
            "B2-2D",
        "run_dir":
            str(run_dir),
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
        "discovery_errors":
            discovery_errors,
        "audit_result":
            audit_result,
        "integrity":
            integrity,
        "metrics": {
            "claim_count":
                len(
                    packet[
                        "accepted_claims"
                    ]
                ),
            "evidence_count":
                evidence_count,
            "elapsed_seconds":
                round(
                    elapsed,
                    3,
                ),
        },
    }

    save_json(
        run_dir
        / "semantic-audit.json",
        result,
    )

    print()
    print(
        "Auditor time:",
        f"{elapsed:.3f}초",
        flush=True,
    )

    print(
        "Integrity:",
        integrity["ok"],
        flush=True,
    )

    print(
        "Result:",
        run_dir
        / "semantic-audit.json",
        flush=True,
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--validated-result",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--tool-calls",
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

    run_audit(
        validated_result_path=
            args.validated_result,
        tool_calls_path=
            args.tool_calls,
        skill_name=
            args.skill,
        output_root=
            args.output_root,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
