from __future__ import annotations

import argparse
import itertools
import json
import time
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

PAIR_VERDICTS = {
    "CONFIRMED_INDEPENDENT",
    "DEPENDENT",
    "INSUFFICIENT_PROVENANCE",
}

FAMILY_VERDICTS = {
    "TRIANGULATED",
    "NOT_TRIANGULATED",
    "UNKNOWN",
}


def load_json(path: Path) -> Any:
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
        )
        + "\n",
        encoding="utf-8",
    )


def expected_pairs(
    family: dict[str, Any],
) -> set[tuple[str, str]]:
    refs = sorted(
        source["source_ref"]
        for source in family["sources"]
    )

    return {
        tuple(sorted(pair))
        for pair in itertools.combinations(
            refs,
            2,
        )
    }


def validate(
    *,
    result: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    errors = []

    families = result.get("families")

    if not isinstance(families, list):
        return {
            "ok": False,
            "errors": [
                "families가 list가 아닙니다."
            ],
        }

    expected = {
        family["family_ref"]: family
        for family in packet["families"]
    }

    seen = set()

    for family in families:
        family_ref = family.get(
            "family_ref"
        )

        if family_ref not in expected:
            errors.append(
                f"잘못된 family_ref: {family_ref!r}"
            )
            continue

        if family_ref in seen:
            errors.append(
                f"중복 family_ref: {family_ref}"
            )

        seen.add(family_ref)

        final_verdict = family.get(
            "final_verdict"
        )

        if final_verdict not in FAMILY_VERDICTS:
            errors.append(
                f"{family_ref}: 잘못된 final_verdict "
                f"{final_verdict!r}"
            )

        pairwise = family.get(
            "pairwise"
        )

        if not isinstance(pairwise, list):
            errors.append(
                f"{family_ref}: pairwise가 list가 아닙니다."
            )
            continue

        expected_set = expected_pairs(
            expected[family_ref]
        )

        seen_pairs = set()
        confirmed = 0
        insufficient = 0

        for pair in pairwise:
            a = pair.get("source_a_ref")
            b = pair.get("source_b_ref")

            normalized = tuple(
                sorted((a, b))
            )

            seen_pairs.add(
                normalized
            )

            verdict = pair.get(
                "verdict"
            )

            if verdict not in PAIR_VERDICTS:
                errors.append(
                    f"{family_ref}: 잘못된 pair verdict "
                    f"{verdict!r}"
                )

            if verdict == "CONFIRMED_INDEPENDENT":
                confirmed += 1

            if verdict == "INSUFFICIENT_PROVENANCE":
                insufficient += 1

            reason = pair.get(
                "reason"
            )

            if (
                not isinstance(reason, str)
                or not reason.strip()
            ):
                errors.append(
                    f"{family_ref}: pair reason이 비어 있습니다."
                )

        if seen_pairs != expected_set:
            errors.append(
                f"{family_ref}: source pair 집합이 "
                "입력과 일치하지 않습니다."
            )

        if (
            final_verdict == "TRIANGULATED"
            and confirmed == 0
        ):
            errors.append(
                f"{family_ref}: TRIANGULATED인데 "
                "confirmed independent pair가 없습니다."
            )

        if (
            final_verdict == "UNKNOWN"
            and insufficient == 0
        ):
            errors.append(
                f"{family_ref}: UNKNOWN인데 "
                "INSUFFICIENT_PROVENANCE pair가 없습니다."
            )

        reason = family.get(
            "reason"
        )

        if (
            not isinstance(reason, str)
            or not reason.strip()
        ):
            errors.append(
                f"{family_ref}: family reason이 비어 있습니다."
            )

    missing = (
        set(expected)
        - seen
    )

    if missing:
        errors.append(
            "누락 family: "
            + ", ".join(
                sorted(missing)
            )
        )

    return {
        "ok": not errors,
        "errors": errors,
    }


def run_independence_challenge(
    *,
    independence_run: Path,
    skill_name: str,
) -> dict[str, Any]:
    """기존 Source Independence 결과를 adversarial하게 재검토한다."""

    run_dir = (
        independence_run
        .expanduser()
        .resolve()
    )

    previous = load_json(
        run_dir
        / "result.json"
    )

    packet = load_json(
        run_dir
        / "independence-packet.json"
    )

    evidence_policy = (
        ROOT
        / "runtime"
        / "b2"
        / "evidence-policy.md"
    ).read_text(
        encoding="utf-8"
    )

    independence_contract = (
        ROOT
        / "runtime"
        / "b2"
        / "source-independence.md"
    ).read_text(
        encoding="utf-8"
    )

    challenge_contract = (
        ROOT
        / "runtime"
        / "b2"
        / "independence-challenge.md"
    ).read_text(
        encoding="utf-8"
    )

    catalog, _ = discover_skills(
        DEFAULT_SEARCH_ROOTS
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
        "# Independence Contract\n\n"
        + independence_contract
        + "\n\n"
        "# Adversarial Challenge Contract\n\n"
        + challenge_contract
    )

    user_prompt = (
        "# VERIFIED Evidence Packet\n\n"
        + json.dumps(
            packet,
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "# Previous Independence Audit\n\n"
        + json.dumps(
            previous["audit"],
            ensure_ascii=False,
            indent=2,
        )
        + "\n\n"
        "Challenge every previous INDEPENDENT judgment. "
        "Do not assume independence from different publisher "
        "names or domains. Return JSON only."
    )

    client = OllamaClient()

    print(
        "===== B2 Independence Challenge =====",
        flush=True,
    )

    print(
        "Prior run:",
        run_dir,
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
        / "challenge-response.json",
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
        / "challenge-raw.txt"
    ).write_text(
        raw,
        encoding="utf-8",
    )

    if not raw.strip():
        raise RuntimeError(
            "Challenge reviewer가 빈 응답을 반환했습니다."
        )

    result = extract_json_object(
        raw
    )

    validation = validate(
        result=result,
        packet=packet,
    )

    final = {
        "status":
            (
                "completed"
                if validation["ok"]
                else "invalid_challenge_output"
            ),
        "validation":
            validation,
        "challenge":
            result,
        "elapsed_seconds":
            round(
                elapsed,
                3,
            ),
        "run_dir":
            str(
                run_dir
            ),
        "challenge_result_path":
            str(
                (
                    run_dir
                    / "challenge-result.json"
                ).resolve()
            ),
    }

    save_json(
        run_dir
        / "challenge-result.json",
        final,
    )

    print(
        "Time:",
        f"{elapsed:.3f}초",
        flush=True,
    )

    print(
        "Validation:",
        validation["ok"],
        flush=True,
    )

    if validation["ok"]:
        for family in (
            result[
                "families"
            ]
        ):
            print(
                family[
                    "family_ref"
                ],
                "=>",
                family[
                    "final_verdict"
                ],
                flush=True,
            )

    print(
        "Result:",
        run_dir
        / "challenge-result.json",
        flush=True,
    )

    return final


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--independence-run",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--skill",
        default="deep-research",
    )

    args = (
        parser.parse_args()
    )

    result = (
        run_independence_challenge(
            independence_run=
                args.independence_run,
            skill_name=
                args.skill,
        )
    )

    return (
        0
        if (
            result.get(
                "validation",
                {},
            ).get(
                "ok"
            )
            is True
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
