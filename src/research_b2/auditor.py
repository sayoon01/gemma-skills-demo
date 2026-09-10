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
    build_pdf_read_index,
    canonical_file_path,
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

    pdf_read_index = build_pdf_read_index(
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

            source_kind = (
                source.get(
                    "source_kind"
                )
                or "web"
            )

            if source_kind == "web":
                source_url = (
                    source.get(
                        "retrieved_url"
                    )
                    or source.get(
                        "url"
                    )
                    or ""
                )

                fetch = fetch_index.get(
                    canonical_url(
                        source_url
                    )
                )

                if fetch is None:
                    #
                    # Deterministic Gate를 통과했는데
                    # fetch record가 사라진 경우
                    # Runtime consistency 오류.
                    #
                    raise ValueError(
                        "검증된 Web Source의 fetch record를 "
                        f"찾지 못했습니다: {source_url}"
                    )

                worker_source = {
                    "source_kind":
                        "web",
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
                }

                retrieved_source = {
                    "source_kind":
                        "web",
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
                }

            elif source_kind == "file":
                source_path = (
                    source.get(
                        "retrieved_path"
                    )
                    or source.get(
                        "path"
                    )
                    or ""
                )

                page_number = (
                    source.get(
                        "retrieved_page"
                    )
                    or source.get(
                        "page"
                    )
                )

                if (
                    not source_path
                    or not isinstance(
                        page_number,
                        int,
                    )
                    or isinstance(
                        page_number,
                        bool,
                    )
                    or page_number < 1
                ):
                    raise ValueError(
                        "검증된 File Source의 "
                        "path/page가 유효하지 않습니다: "
                        f"{source!r}"
                    )

                read = pdf_read_index.get(
                    (
                        canonical_file_path(
                            source_path
                        ),
                        page_number,
                    )
                )

                if read is None:
                    #
                    # Deterministic Gate를 통과했는데
                    # 실제 read_pdf_pages record가
                    # 사라졌다면 Runtime consistency 오류.
                    #
                    raise ValueError(
                        "검증된 File Source의 PDF read record를 "
                        "찾지 못했습니다: "
                        f"{source_path} / page {page_number}"
                    )

                worker_source = {
                    "source_kind":
                        "file",
                    "path":
                        source.get(
                            "path"
                        )
                        or source_path,
                    "page":
                        source.get(
                            "page"
                        )
                        or page_number,
                    "file_sha256":
                        (
                            source.get(
                                "file_sha256"
                            )
                            or source.get(
                                "retrieved_file_sha256"
                            )
                            or ""
                        ),
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
                }

                retrieved_source = {
                    "source_kind":
                        "file",
                    "title":
                        read.get(
                            "title"
                        )
                        or "",
                    "path":
                        read.get(
                            "final_path"
                        )
                        or "",
                    "page":
                        read.get(
                            "page"
                        ),
                    "file_sha256":
                        read.get(
                            "file_sha256"
                        )
                        or "",
                    "content":
                        read.get(
                            "content"
                        )
                        or "",
                    "content_chars":
                        read.get(
                            "content_chars"
                        )
                        or 0,
                }

            else:
                raise ValueError(
                    "Deterministic Gate 이후 "
                    "지원되지 않는 source_kind: "
                    f"{source_kind!r}"
                )

            packet_sources.append(
                {
                    "evidence_id":
                        evidence_id,
                    "worker_source":
                        worker_source,
                    "retrieved_source":
                        retrieved_source,
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



def build_audit_repair_prompt(
    *,
    packet: dict[str, Any],
    invalid_audit: dict[str, Any],
    integrity: dict[str, Any],
) -> str:
    """Semantic judgment를 Python에서 고치지 않고 Gemma에 repair 요청한다."""

    return (
        "# Semantic Audit Output Repair\n\n"
        "The previous semantic audit completed, but its "
        "structured output failed runtime integrity validation.\n\n"
        "This is a schema and consistency repair pass. "
        "Do not perform new research. Do not add new claims, "
        "new evidence, new URLs, or unsupported facts.\n\n"

        "# Integrity Errors\n\n"
        + json.dumps(
            integrity.get(
                "errors",
                [],
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"

        "# Original Audit Packet\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"

        "# Invalid Audit Output\n\n"
        + json.dumps(
            invalid_audit,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"

        "# Repair Requirements\n\n"
        "- Preserve every expected claim_id.\n"
        "- Preserve every expected evidence_id.\n"
        "- Do not create or remove claims or evidence.\n"
        "- Use only claim verdict values permitted by the "
        "semantic verification contract in the system prompt.\n"
        "- Use only evidence state values permitted by that contract.\n"
        "- Do not use an evidence-state label as a claim verdict "
        "unless the contract explicitly permits it.\n"
        "- Keep the semantic judgment of the previous audit whenever "
        "possible, changing only what is required for contract "
        "consistency and integrity.\n"
        "- Claim-level verdicts must remain consistent with their "
        "evidence-level states according to the active verification "
        "contract.\n"
        "- Return the semantic audit JSON object only.\n"
    )


def repair_audit_output(
    *,
    client: OllamaClient,
    base_messages: list[dict[str, Any]],
    packet: dict[str, Any],
    initial_audit: dict[str, Any],
    initial_integrity: dict[str, Any],
    run_dir: Path,
    max_attempts: int = 2,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
]:
    """Integrity-invalid audit를 Gemma semantic repair로 복구한다."""

    audit_result = initial_audit
    integrity = initial_integrity

    attempts: list[
        dict[str, Any]
    ] = []

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        if integrity["ok"]:
            break

        repair_prompt = (
            build_audit_repair_prompt(
                packet=packet,
                invalid_audit=
                    audit_result,
                integrity=
                    integrity,
            )
        )

        (
            run_dir
            / f"repair-{attempt:02d}-prompt.md"
        ).write_text(
            repair_prompt + "\n",
            encoding="utf-8",
        )

        #
        # 기존 system message는 그대로 유지한다.
        # 원 research 실행은 하지 않고 semantic output만 repair.
        #
        system_messages = [
            message
            for message in base_messages
            if message.get("role")
            == "system"
        ]

        repair_messages = (
            system_messages
            + [
                {
                    "role": "user",
                    "content":
                        repair_prompt,
                }
            ]
        )

        started = time.monotonic()

        response = client.chat(
            repair_messages,
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
            attempts.append(
                {
                    "attempt":
                        attempt,
                    "status":
                        "empty_response",
                    "elapsed_seconds":
                        round(
                            elapsed,
                            3,
                        ),
                    "done_reason":
                        response.get(
                            "done_reason"
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
                    "status":
                        "parse_error",
                    "elapsed_seconds":
                        round(
                            elapsed,
                            3,
                        ),
                    "error":
                        (
                            f"{type(exc).__name__}: "
                            f"{exc}"
                        ),
                }
            )
            continue

        candidate_integrity = (
            validate_audit_ids(
                packet=packet,
                audit_result=candidate,
            )
        )

        save_json(
            run_dir
            / (
                f"repair-{attempt:02d}"
                "-audit.json"
            ),
            candidate,
        )

        save_json(
            run_dir
            / (
                f"repair-{attempt:02d}"
                "-integrity.json"
            ),
            candidate_integrity,
        )

        attempts.append(
            {
                "attempt":
                    attempt,
                "status":
                    (
                        "valid"
                        if candidate_integrity[
                            "ok"
                        ]
                        else "invalid"
                    ),
                "elapsed_seconds":
                    round(
                        elapsed,
                        3,
                    ),
                "errors":
                    candidate_integrity[
                        "errors"
                    ],
            }
        )

        audit_result = (
            candidate
        )

        integrity = (
            candidate_integrity
        )

    return (
        audit_result,
        integrity,
        attempts,
    )


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
        messages,
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

    raw_text = (
        response["message"]
        .get("content")
        or ""
    )

    if not raw_text.strip():
        thinking = (
            response["message"]
            .get("thinking")
            or ""
        )

        raise RuntimeError(
            "Semantic Auditor가 빈 content를 반환했습니다. "
            f"done_reason={response.get('done_reason')!r}, "
            f"eval_count={response.get('eval_count')!r}, "
            f"thinking_chars={len(thinking)}"
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

    initial_integrity = dict(
        integrity
    )

    initial_audit_result = (
        audit_result
    )

    repair_attempts = []

    if not integrity["ok"]:
        save_json(
            run_dir
            / "audit-initial-invalid.json",
            {
                "audit_result":
                    initial_audit_result,
                "integrity":
                    initial_integrity,
            },
        )

        print()
        print(
            "Initial semantic audit invalid; "
            "starting generic repair.",
            flush=True,
        )

        (
            audit_result,
            integrity,
            repair_attempts,
        ) = repair_audit_output(
            client=client,
            base_messages=
                messages,
            packet=packet,
            initial_audit=
                audit_result,
            initial_integrity=
                integrity,
            run_dir=run_dir,
            max_attempts=2,
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
        "initial_integrity":
            initial_integrity,
        "repair_applied":
            bool(
                repair_attempts
            ),
        "repair_attempts":
            repair_attempts,
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
