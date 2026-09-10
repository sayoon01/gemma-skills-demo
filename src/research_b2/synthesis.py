"""B2 final research synthesis.

The synthesis model receives:

- exact original user task;
- active public Agent Skill;
- synthesis/evidence MD contracts;
- validated cumulative claim/evidence state;
- semantic relationships and conflicts;
- independence-family decisions;
- unsupported claims and gaps;
- operational stop record.

Raw Worker conversations and search snippets are not supplied.

Python only constructs the validated packet, assigns stable citation IDs,
calls Gemma, and mechanically verifies that the final report does not invent
citations or URLs.
"""

from __future__ import annotations

import argparse
import json
import re
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


ROOT = Path(__file__).resolve().parents[2]


CITATION_RE = re.compile(
    r"\[(SRC\d{3})\]"
)

URL_RE = re.compile(
    r"https?://[^\s<>\])}\"']+"
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


def evidence_source(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    source = (
        evidence.get(
            "source"
        )
        or {}
    )

    worker = (
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
        or worker.get(
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

    return {
        "url":
            url,
        "title":
            (
                retrieved.get(
                    "title"
                )
                or worker.get(
                    "title"
                )
                or ""
            ),
        "publisher":
            worker.get(
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
            worker.get(
                "excerpt"
            )
            or "",
        "support_reason":
            evidence.get(
                "reason"
            )
            or "",
    }


def build_packet(
    *,
    state: dict[str, Any],
    stop_record: dict[str, Any],
    task_text: str,
) -> dict[str, Any]:
    #
    # VERIFIED evidence에서만 global citation registry 생성.
    #
    source_by_url: dict[
        str,
        dict[str, Any],
    ] = {}

    for claim in (
        state.get(
            "claims"
        )
        or []
    ):
        claim_ref = (
            claim[
                "claim_ref"
            ]
        )

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
                evidence_source(
                    evidence
                )
            )

            url = (
                source[
                    "url"
                ]
            )

            if not url:
                continue

            record = (
                source_by_url.setdefault(
                    url,
                    {
                        **source,
                        "claim_refs": [],
                        "evidence_refs": [],
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

            evidence_ref = (
                f"{claim_ref}:"
                f"{evidence.get('evidence_id', '')}"
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

    citation_by_url = {}

    for index, (
        url,
        source,
    ) in enumerate(
        sorted(
            source_by_url.items()
        ),
        1,
    ):
        citation_ref = (
            f"SRC{index:03d}"
        )

        citation_by_url[
            url
        ] = citation_ref

        sources.append(
            {
                "citation_ref":
                    citation_ref,
                **source,
            }
        )

    family_by_claim = {}

    for family in (
        state.get(
            "independence_families"
        )
        or []
    ):
        for claim_ref in (
            family.get(
                "claim_refs"
            )
            or []
        ):
            family_by_claim[
                claim_ref
            ] = {
                "family_ref":
                    family.get(
                        "family_ref"
                    ),
                "final_verdict":
                    family.get(
                        "final_verdict"
                    ),
                "resolved_status":
                    family.get(
                        "resolved_status"
                    ),
                "reason":
                    family.get(
                        "reason"
                    ),
            }

    claims = []

    for claim in (
        state.get(
            "claims"
        )
        or []
    ):
        evidence_records = []

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
                evidence_source(
                    evidence
                )
            )

            url = (
                source[
                    "url"
                ]
            )

            citation_ref = (
                citation_by_url.get(
                    url
                )
            )

            if not citation_ref:
                continue

            evidence_records.append(
                {
                    "evidence_id":
                        evidence.get(
                            "evidence_id"
                        ),
                    "citation_ref":
                        citation_ref,
                    "support_reason":
                        evidence.get(
                            "reason"
                        )
                        or "",
                    "source_type":
                        evidence.get(
                            "audited_source_type"
                        ),
                    "tier":
                        evidence.get(
                            "audited_tier"
                        ),
                    "excerpt":
                        source[
                            "worker_excerpt"
                        ],
                }
            )

        claims.append(
            {
                "claim_ref":
                    claim[
                        "claim_ref"
                    ],
                "wave":
                    claim.get(
                        "wave"
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
                "family_resolution":
                    family_by_claim.get(
                        claim[
                            "claim_ref"
                        ]
                    ),
                "evidence":
                    evidence_records,
            }
        )

    return {
        "original_user_task":
            task_text,
        "research_state": {
            "summary":
                state.get(
                    "summary"
                ),
            "novelty":
                state.get(
                    "novelty"
                ),
            "stop":
                stop_record,
        },
        "validated_claims":
            claims,
        "semantic_relations":
            state.get(
                "relations"
            )
            or [],
        "independence_families":
            state.get(
                "independence_families"
            )
            or [],
        "unsupported_claims":
            state.get(
                "unsupported_claims"
            )
            or [],
        "research_gaps":
            state.get(
                "gaps"
            )
            or [],
        "verified_sources":
            sources,
    }


def validate_report(
    *,
    report: str,
    packet: dict[str, Any],
) -> dict[str, Any]:
    errors = []

    allowed_refs = {
        source[
            "citation_ref"
        ]
        for source in (
            packet[
                "verified_sources"
            ]
        )
    }

    used_refs = set(
        CITATION_RE.findall(
            report
        )
    )

    invalid_refs = (
        used_refs
        - allowed_refs
    )

    if invalid_refs:
        errors.append(
            "존재하지 않는 citation ref: "
            + ", ".join(
                sorted(
                    invalid_refs
                )
            )
        )

    if (
        allowed_refs
        and not used_refs
    ):
        errors.append(
            "보고서에 VERIFIED source citation이 없습니다."
        )

    allowed_urls = {
        source[
            "url"
        ]
        for source in (
            packet[
                "verified_sources"
            ]
        )
        if source.get(
            "url"
        )
    }

    found_urls = {
        canonical_url(
            url
        )
        for url in (
            URL_RE.findall(
                report
            )
        )
    }

    unknown_urls = (
        found_urls
        - allowed_urls
    )

    if unknown_urls:
        errors.append(
            "검증되지 않은 URL이 보고서에 포함됨: "
            + ", ".join(
                sorted(
                    unknown_urls
                )
            )
        )

    hangul_count = sum(
        1
        for char in report
        if (
            "\uac00"
            <= char
            <= "\ud7a3"
        )
    )

    if hangul_count == 0:
        errors.append(
            "최종 보고서에 한국어 본문이 없습니다."
        )

    return {
        "ok":
            not errors,
        "errors":
            errors,
        "used_citation_refs":
            sorted(
                used_refs
            ),
        "used_citation_count":
            len(
                used_refs
            ),
        "allowed_citation_count":
            len(
                allowed_refs
            ),
        "hangul_char_count":
            hangul_count,
    }


def build_repair_prompt(
    *,
    report: str,
    validation: dict[str, Any],
    packet: dict[str, Any],
) -> str:
    return (
        "# Final Report Repair\n\n"
        "The previous final report failed mechanical output "
        "validation.\n\n"
        "Do not conduct new research. "
        "Use only the supplied validated research packet.\n\n"

        "# Validation Errors\n\n"
        + json.dumps(
            validation[
                "errors"
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"

        "# Allowed Citation Refs\n\n"
        + json.dumps(
            [
                {
                    "citation_ref":
                        source[
                            "citation_ref"
                        ],
                    "url":
                        source[
                            "url"
                        ],
                }
                for source in (
                    packet[
                        "verified_sources"
                    ]
                )
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"

        "# Previous Report\n\n"
        + report
        + "\n\n"

        "# Repair Requirements\n\n"
        "- Preserve supported factual meaning.\n"
        "- Write the report in Korean.\n"
        "- Do not add research, facts, URLs, or sources.\n"
        "- Use only allowed [SRCxxx] citations.\n"
        "- Preserve single-source, unknown-independence, "
        "conflicting, unsupported, and gap qualifications.\n"
        "- Return the complete corrected Markdown report only.\n"
    )


def run_synthesis(
    *,
    task_path: Path,
    cumulative_path: Path,
    stop_record_path: Path,
    skill_name: str,
    output_root: Path,
) -> dict[str, Any]:
    task_text = (
        task_path.read_text(
            encoding="utf-8"
        )
    )

    state = load_json(
        cumulative_path
    )

    stop_record = load_json(
        stop_record_path
    )

    packet = build_packet(
        state=state,
        stop_record=
            stop_record,
        task_text=
            task_text,
    )

    synthesis_contract = (
        ROOT
        / "runtime"
        / "b2"
        / "synthesis.md"
    ).read_text(
        encoding="utf-8"
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
        "# Active Public Agent Skill\n\n"
        "<skill>\n"
        + skill[
            "body"
        ]
        + "\n</skill>\n\n"

        "# Evidence Policy\n\n"
        + evidence_policy
        + "\n\n"

        "# Final Synthesis Contract\n\n"
        + synthesis_contract
        + "\n\n"

        "# Critical Output Rules\n\n"
        "The final report itself must be written in Korean.\n"
        "Do not perform new research.\n"
        "Do not introduce facts that are absent from the validated packet.\n"
        "Do not introduce new sources or URLs.\n"
        "Use citations exactly as [SRC001], [SRC002], etc.\n"
        "Only citation refs supplied in verified_sources are allowed.\n"
        "Consolidate SAME claims rather than repeating them.\n"
        "Preserve CONTRADICTS relations explicitly.\n"
        "A family with UNKNOWN independence must not be described as "
        "triangulated.\n"
        "SINGLE_SOURCE material must be marked or phrased with appropriate "
        "qualification.\n"
        "Unsupported claims are not factual findings.\n"
        "Research gaps and unknowns must remain visible.\n"
        "The stop reason is user_stop, not semantic convergence.\n"
    )

    user_prompt = (
        "# Original Research Request\n\n"
        + task_text
        + "\n\n"

        "# Validated Research Packet\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"

        "# Task\n\n"
        "Produce the final evidence-backed deep research report in Korean.\n"
        "Use the structure and research behavior specified by the active "
        "Skill and synthesis contract.\n"
        "Cite factual findings using only the provided [SRCxxx] references.\n"
        "Include a source/reference section mapping every citation used to "
        "its provided source title, publisher, and URL.\n"
        "Return Markdown report text only."
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="synthesis-",
            dir=output_root,
        )
    )

    save_json(
        run_dir
        / "synthesis-packet.json",
        packet,
    )

    (
        run_dir
        / "system-prompt.md"
    ).write_text(
        system_prompt,
        encoding="utf-8",
    )

    (
        run_dir
        / "user-prompt.md"
    ).write_text(
        user_prompt,
        encoding="utf-8",
    )

    client = OllamaClient()

    print(
        "===== B2 Final Synthesis =====",
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
        skill[
            "name"
        ],
        flush=True,
    )

    print(
        "Validated claims:",
        len(
            packet[
                "validated_claims"
            ]
        ),
        flush=True,
    )

    print(
        "Verified sources:",
        len(
            packet[
                "verified_sources"
            ]
        ),
        flush=True,
    )

    print(
        "Stop:",
        stop_record[
            "stop_reason"
        ],
        flush=True,
    )

    started = (
        time.monotonic()
    )

    response = client.chat(
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
                    user_prompt,
            },
        ],
        think=False,
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

    report = (
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
        / "report-initial.md"
    ).write_text(
        report,
        encoding="utf-8",
    )

    if not report.strip():
        raise RuntimeError(
            "Synthesis model이 빈 보고서를 반환했습니다. "
            f"done_reason={response.get('done_reason')!r}, "
            f"eval_count={response.get('eval_count')!r}"
        )

    validation = (
        validate_report(
            report=report,
            packet=packet,
        )
    )

    initial_validation = dict(
        validation
    )

    repair_attempts = []

    #
    # Citation/URL/language 같은 기계적 output failure만
    # generic repair한다.
    #
    for attempt in range(
        1,
        3,
    ):
        if validation[
            "ok"
        ]:
            break

        print(
            "Initial/previous synthesis output invalid; "
            f"repair attempt {attempt}.",
            flush=True,
        )

        repair_prompt = (
            build_repair_prompt(
                report=report,
                validation=
                    validation,
                packet=packet,
            )
        )

        (
            run_dir
            / f"repair-{attempt:02d}-prompt.md"
        ).write_text(
            repair_prompt,
            encoding="utf-8",
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

        candidate = (
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
            / f"repair-{attempt:02d}-report.md"
        ).write_text(
            candidate,
            encoding="utf-8",
        )

        if not candidate.strip():
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

        candidate_validation = (
            validate_report(
                report=
                    candidate,
                packet=
                    packet,
            )
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

        report = candidate
        validation = (
            candidate_validation
        )

    (
        run_dir
        / "report.md"
    ).write_text(
        report,
        encoding="utf-8",
    )

    save_json(
        run_dir
        / "validation.json",
        validation,
    )

    result = {
        "status":
            (
                "completed"
                if validation[
                    "ok"
                ]
                else "invalid_synthesis_output"
            ),
        "stage":
            "B2-10",
        "created_at":
            utc_now(),
        "run_dir":
            str(
                run_dir
            ),
        "model":
            client.model,
        "skill":
            skill[
                "name"
            ],
        "skill_sha256":
            skill[
                "sha256"
            ],
        "task_path":
            str(
                task_path.resolve()
            ),
        "cumulative_path":
            str(
                cumulative_path.resolve()
            ),
        "stop_record_path":
            str(
                stop_record_path.resolve()
            ),
        "initial_validation":
            initial_validation,
        "repair_attempts":
            repair_attempts,
        "validation":
            validation,
        "metrics": {
            "validated_claim_count":
                len(
                    packet[
                        "validated_claims"
                    ]
                ),
            "verified_source_count":
                len(
                    packet[
                        "verified_sources"
                    ]
                ),
            "report_chars":
                len(
                    report
                ),
            "elapsed_seconds":
                round(
                    elapsed,
                    3,
                ),
        },
        "discovery_errors":
            discovery_errors,
        "report_path":
            str(
                (
                    run_dir
                    / "report.md"
                ).resolve()
            ),
    }

    save_json(
        run_dir
        / "result.json",
        result,
    )

    print()
    print(
        "Synthesis time:",
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

    print(
        "Hangul chars:",
        validation[
            "hangul_char_count"
        ],
        flush=True,
    )

    print(
        "Citations used:",
        validation[
            "used_citation_count"
        ],
        "/",
        validation[
            "allowed_citation_count"
        ],
        flush=True,
    )

    print(
        "Report chars:",
        len(
            report
        ),
        flush=True,
    )

    print(
        "Report:",
        run_dir
        / "report.md",
        flush=True,
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--task",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--cumulative",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--stop-record",
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

    result = run_synthesis(
        task_path=
            args.task,
        cumulative_path=
            args.cumulative,
        stop_record_path=
            args.stop_record,
        skill_name=
            args.skill,
        output_root=
            args.output_root,
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
