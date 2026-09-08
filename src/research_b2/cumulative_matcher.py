"""B2 cumulative semantic claim matcher.

Python은 claim의 의미적 동일성/확장/충돌/신규성을 결정하지 않는다.

Python 역할:
- validated Evidence Pool load
- compact claim packet 생성
- active Skill + MD contract를 Gemma에 전달
- JSON/ID/schema 검증
- generic repair
- 측정값 저장

Semantic relation과 novelty 판단은 Gemma가 수행한다.
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

from .worker import extract_json_object


ROOT = Path(__file__).resolve().parents[2]

RELATIONS = {
    "SAME",
    "EXTENDS",
    "CONTRADICTS",
    "NOVEL",
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


def compact_claims(
    pool: dict[str, Any],
) -> list[dict[str, Any]]:
    result = []

    for claim in (
        pool.get(
            "accepted_claims"
        )
        or []
    ):
        result.append(
            {
                "claim_ref":
                    claim.get(
                        "claim_ref"
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
            }
        )

    return result


def validate_match_result(
    *,
    result: dict[str, Any],
    prior_claim_refs: set[str],
    new_claim_refs: set[str],
) -> dict[str, Any]:
    errors = []

    if not isinstance(
        result,
        dict,
    ):
        return {
            "ok": False,
            "errors": [
                "최상위 결과가 객체가 아닙니다."
            ],
        }

    unexpected_top = (
        set(result)
        - {"comparisons"}
    )

    if unexpected_top:
        errors.append(
            "허용되지 않은 top-level field: "
            + ", ".join(
                sorted(
                    unexpected_top
                )
            )
        )

    comparisons = (
        result.get(
            "comparisons"
        )
    )

    if not isinstance(
        comparisons,
        list,
    ):
        return {
            "ok": False,
            "errors":
                errors
                + [
                    "comparisons가 list가 아닙니다."
                ],
        }

    seen_new_refs = set()

    allowed_fields = {
        "new_claim_ref",
        "relation",
        "matched_prior_claim_refs",
        "is_novel",
        "reason",
    }

    for index, item in enumerate(
        comparisons,
        1,
    ):
        prefix = (
            f"comparisons[{index}]"
        )

        if not isinstance(
            item,
            dict,
        ):
            errors.append(
                f"{prefix}가 객체가 아닙니다."
            )
            continue

        unexpected = (
            set(item)
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

        new_ref = (
            item.get(
                "new_claim_ref"
            )
            or ""
        )

        if new_ref not in new_claim_refs:
            errors.append(
                f"{prefix} 잘못된 new_claim_ref: "
                f"{new_ref!r}"
            )

        elif new_ref in seen_new_refs:
            errors.append(
                "중복 new_claim_ref: "
                f"{new_ref}"
            )

        else:
            seen_new_refs.add(
                new_ref
            )

        relation = (
            item.get(
                "relation"
            )
        )

        if relation not in RELATIONS:
            errors.append(
                f"{prefix} 잘못된 relation: "
                f"{relation!r}"
            )

        matched = (
            item.get(
                "matched_prior_claim_refs"
            )
        )

        if not isinstance(
            matched,
            list,
        ):
            errors.append(
                f"{prefix}.matched_prior_claim_refs가 "
                "list가 아닙니다."
            )
            matched = []

        for prior_ref in matched:
            if prior_ref not in prior_claim_refs:
                errors.append(
                    f"{prefix} 존재하지 않는 prior claim: "
                    f"{prior_ref!r}"
                )

        if (
            relation == "NOVEL"
            and matched
        ):
            errors.append(
                f"{prefix}: relation=NOVEL인데 "
                "matched_prior_claim_refs가 비어 있지 않습니다."
            )

        if (
            relation
            in {
                "SAME",
                "EXTENDS",
                "CONTRADICTS",
            }
            and not matched
        ):
            errors.append(
                f"{prefix}: relation={relation}인데 "
                "matched prior claim이 없습니다."
            )

        if not isinstance(
            item.get(
                "is_novel"
            ),
            bool,
        ):
            errors.append(
                f"{prefix}.is_novel이 bool이 아닙니다."
            )

        reason = (
            item.get(
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
                f"{prefix}.reason이 비어 있습니다."
            )

    missing = (
        new_claim_refs
        - seen_new_refs
    )

    if missing:
        errors.append(
            "누락된 new claim: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    extra = (
        seen_new_refs
        - new_claim_refs
    )

    if extra:
        errors.append(
            "예상하지 않은 new claim: "
            + ", ".join(
                sorted(
                    extra
                )
            )
        )

    return {
        "ok":
            not errors,
        "errors":
            errors,
        "expected_new_claim_count":
            len(
                new_claim_refs
            ),
        "seen_new_claim_count":
            len(
                seen_new_refs
            ),
    }


def build_repair_prompt(
    *,
    invalid_result: dict[str, Any],
    validation: dict[str, Any],
    prior_claim_refs: set[str],
    new_claim_refs: set[str],
) -> str:
    return (
        "# Cumulative Claim Match Repair\n\n"
        "The previous semantic comparison failed runtime "
        "schema or ID validation.\n\n"
        "This is a repair pass only. "
        "Do not perform research and do not introduce new claims.\n\n"
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
        "# Allowed Prior Claim Refs\n\n"
        + json.dumps(
            sorted(
                prior_claim_refs
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Required New Claim Refs\n\n"
        + json.dumps(
            sorted(
                new_claim_refs
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Invalid Result\n\n"
        + json.dumps(
            invalid_result,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Repair Rules\n\n"
        "- Preserve the semantic judgments whenever possible.\n"
        "- Return every required new_claim_ref exactly once.\n"
        "- Do not invent claim refs.\n"
        "- Use only SAME, EXTENDS, CONTRADICTS, or NOVEL.\n"
        "- Return JSON only in the required contract shape.\n"
    )


def run_match(
    *,
    prior_pool_path: Path,
    new_pool_path: Path,
    skill_name: str,
    output_root: Path,
) -> dict[str, Any]:
    prior_pool = load_json(
        prior_pool_path
    )

    new_pool = load_json(
        new_pool_path
    )

    prior_claims = (
        compact_claims(
            prior_pool
        )
    )

    new_claims = (
        compact_claims(
            new_pool
        )
    )

    prior_claim_refs = {
        item["claim_ref"]
        for item in prior_claims
    }

    new_claim_refs = {
        item["claim_ref"]
        for item in new_claims
    }

    if not prior_claim_refs:
        raise ValueError(
            "prior accepted claims가 없습니다."
        )

    if not new_claim_refs:
        raise ValueError(
            "new accepted claims가 없습니다."
        )

    contract_path = (
        ROOT
        / "runtime"
        / "b2"
        / "claim-merge.md"
    )

    contract = (
        contract_path.read_text(
            encoding="utf-8"
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

    system_prompt = (
        "# Active Agent Skill\n\n"
        "Use the following public Skill as the primary "
        "research-method specification.\n\n"
        "<skill>\n"
        + skill["body"]
        + "\n</skill>\n\n"
        "# Cumulative Claim Merge Contract\n\n"
        + contract
    )

    packet = {
        "prior_cumulative_claims":
            prior_claims,
        "new_wave_claims":
            new_claims,
    }

    user_prompt = (
        "# Semantic Comparison Packet\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "Compare the new-wave validated claims against "
        "the prior cumulative validated claims. "
        "Do not perform new research. "
        "Return JSON only according to claim-merge.md."
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="match-",
            dir=output_root,
        )
    )

    save_json(
        run_dir
        / "match-packet.json",
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
        "===== B2 Cumulative Claim Matcher =====",
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
        "Prior claims:",
        len(
            prior_claims
        ),
        flush=True,
    )

    print(
        "New claims:",
        len(
            new_claims
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
        / "match-raw.txt"
    ).write_text(
        raw_text,
        encoding="utf-8",
    )

    if not raw_text.strip():
        raise RuntimeError(
            "Matcher가 빈 content를 반환했습니다. "
            f"done_reason={response.get('done_reason')!r}, "
            f"eval_count={response.get('eval_count')!r}"
        )

    result = (
        extract_json_object(
            raw_text
        )
    )

    validation = (
        validate_match_result(
            result=result,
            prior_claim_refs=
                prior_claim_refs,
            new_claim_refs=
                new_claim_refs,
        )
    )

    initial_validation = dict(
        validation
    )

    save_json(
        run_dir
        / "match-initial.json",
        result,
    )

    save_json(
        run_dir
        / "match-initial-validation.json",
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
            "Initial/previous match invalid; "
            f"repair attempt {attempt}.",
            flush=True,
        )

        repair_prompt = (
            build_repair_prompt(
                invalid_result=result,
                validation=validation,
                prior_claim_refs=
                    prior_claim_refs,
                new_claim_refs=
                    new_claim_refs,
            )
        )

        (
            run_dir
            / f"repair-{attempt:02d}-prompt.md"
        ).write_text(
            repair_prompt + "\n",
            encoding="utf-8",
        )

        repair_started = (
            time.monotonic()
        )

        repair_response = (
            client.chat(
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
                    "elapsed_seconds":
                        round(
                            repair_elapsed,
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

        candidate_validation = (
            validate_match_result(
                result=
                    candidate,
                prior_claim_refs=
                    prior_claim_refs,
                new_claim_refs=
                    new_claim_refs,
            )
        )

        save_json(
            run_dir
            / f"repair-{attempt:02d}-match.json",
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

        result = candidate
        validation = (
            candidate_validation
        )

    save_json(
        run_dir
        / "match.json",
        result,
    )

    save_json(
        run_dir
        / "match-validation.json",
        validation,
    )

    comparisons = (
        result.get(
            "comparisons"
        )
        or []
    )

    relation_counts = {
        relation: 0
        for relation in sorted(
            RELATIONS
        )
    }

    for item in comparisons:
        relation = (
            item.get(
                "relation"
            )
        )

        if relation in relation_counts:
            relation_counts[
                relation
            ] += 1

    novel_count = sum(
        1
        for item in comparisons
        if item.get(
            "is_novel"
        )
        is True
    )

    new_claim_count = len(
        new_claims
    )

    novelty_ratio = (
        novel_count
        / new_claim_count
        if new_claim_count
        else 0.0
    )

    final = {
        "status":
            (
                "completed"
                if validation["ok"]
                else "invalid_match_output"
            ),
        "stage":
            "B2-8B",
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
            skill["sha256"],
        "contract_sha256":
            sha256_text(
                contract
            ),
        "prior_pool_path":
            str(
                prior_pool_path.resolve()
            ),
        "new_pool_path":
            str(
                new_pool_path.resolve()
            ),
        "initial_validation":
            initial_validation,
        "repair_attempts":
            repair_attempts,
        "validation":
            validation,
        "comparison":
            result,
        "metrics": {
            "prior_claim_count":
                len(
                    prior_claims
                ),
            "new_claim_count":
                new_claim_count,
            "novel_claim_count":
                novel_count,
            "novelty_ratio":
                novelty_ratio,
            "relation_counts":
                relation_counts,
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

    print()
    print(
        "Matcher time:",
        f"{elapsed:.3f}초",
        flush=True,
    )

    print(
        "Validation:",
        validation["ok"],
        flush=True,
    )

    print(
        "Relations:",
        relation_counts,
        flush=True,
    )

    print(
        "Novel claims:",
        novel_count,
        "/",
        new_claim_count,
        flush=True,
    )

    print(
        "Novelty ratio:",
        round(
            novelty_ratio,
            6,
        ),
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
        "--skill",
        default="deep-research",
    )

    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    result = run_match(
        prior_pool_path=
            args.prior_pool,
        new_pool_path=
            args.new_pool,
        skill_name=
            args.skill,
        output_root=
            args.output_root,
    )

    return (
        0
        if result["status"]
        == "completed"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
