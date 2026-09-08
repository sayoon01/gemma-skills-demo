"""Gemma4 + Agent Skills Deep Research B2 실행기.

B2 목표:
- 범용 CLI 입력
- 공개 SKILL.md 활성화
- Parallel Gemma4 sub-agent
- Multi-wave research
- Evidence aggregation
- Citation verification
- 2-source triangulation
- Source quality gate
- Convergence
- Context/runtime optimization

현재 Phase B2-1에서는 CLI / Skill Activation /
Run Configuration까지만 검증한다.
실제 Model/Worker 실행은 다음 Phase에서 추가한다.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from src.ollama_client import OllamaClient
from src.skill_loader import (
    DEFAULT_SEARCH_ROOTS,
    activate_skill,
    discover_skills,
)


ROOT = Path(__file__).resolve().parent


def save_json(
    path: Path,
    data,
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


def normalize_case_name(
    value: str | None,
) -> str:
    if not value:
        return "adhoc"

    value = value.strip().lower()

    value = re.sub(
        r"[^a-z0-9_-]+",
        "-",
        value,
    )

    value = value.strip("-_")

    return value or "adhoc"


def load_request(
    args: argparse.Namespace,
) -> tuple[str, dict]:
    if args.topic is not None:
        text = args.topic.strip()

        if not text:
            raise ValueError(
                "--topic이 비어 있습니다."
            )

        return (
            text,
            {
                "type": "topic",
                "value": text,
            },
        )

    request_path = args.request.resolve()

    if not request_path.is_file():
        raise FileNotFoundError(
            f"요청 파일을 찾을 수 없습니다: "
            f"{request_path}"
        )

    text = request_path.read_text(
        encoding="utf-8-sig"
    ).strip()

    if not text:
        raise ValueError(
            "요청 문서가 비어 있습니다."
        )

    return (
        text,
        {
            "type": "file",
            "path": str(request_path),
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gemma4 Agent Skills "
            "Deep Research B2 Runner"
        )
    )

    parser.add_argument(
        "--skill",
        default="deep-research",
        help=(
            "활성화할 Agent Skill 이름. "
            "기본값: deep-research"
        ),
    )

    request_group = (
        parser.add_mutually_exclusive_group(
            required=True
        )
    )

    request_group.add_argument(
        "--request",
        type=Path,
        help=(
            "조사 요청이 들어 있는 "
            "Markdown/Text 파일"
        ),
    )

    request_group.add_argument(
        "--topic",
        type=str,
        help=(
            "터미널에서 직접 입력할 "
            "조사 주제/요청"
        ),
    )

    parser.add_argument(
        "--case-name",
        default=None,
        help=(
            "실험 케이스 이름. "
            "예: physical-ai, robot-spec"
        ),
    )

    parser.add_argument(
        "--inputs",
        type=Path,
        default=ROOT / "inputs",
        help=(
            "로컬 입력자료 디렉터리. "
            "기본값: ./inputs"
        ),
    )

    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help=(
            "Wave당 최대 병렬 Worker 수. "
            "기본값: 3"
        ),
    )

    parser.add_argument(
        "--max-waves",
        type=int,
        default=3,
        help=(
            "B2 PoC 안전장치용 최대 Wave 수. "
            "기본값: 3"
        ),
    )

    parser.add_argument(
        "--max-worker-turns",
        type=int,
        default=6,
        help=(
            "Worker당 최대 Agent Turn. "
            "기본값: 6"
        ),
    )

    parser.add_argument(
        "--min-sources",
        type=int,
        default=10,
        help=(
            "Convergence 판단 시 필요한 "
            "최소 고유 Source 수. "
            "기본값: 10"
        ),
    )

    parser.add_argument(
        "--novelty-threshold",
        type=float,
        default=0.15,
        help=(
            "Convergence 신규 Claim 비율 "
            "Threshold. 기본값: 0.15"
        ),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "모델을 실행하지 않고 "
            "입력/Skill/설정만 검증"
        ),
    )

    return parser.parse_args()


def validate_args(
    parser_args: argparse.Namespace,
) -> None:
    if not 1 <= parser_args.max_workers <= 5:
        raise ValueError(
            "--max-workers는 1~5여야 합니다."
        )

    if not 1 <= parser_args.max_waves <= 10:
        raise ValueError(
            "--max-waves는 1~10이어야 합니다."
        )

    if not 1 <= parser_args.max_worker_turns <= 20:
        raise ValueError(
            "--max-worker-turns는 "
            "1~20이어야 합니다."
        )

    if parser_args.min_sources < 1:
        raise ValueError(
            "--min-sources는 1 이상이어야 합니다."
        )

    if not (
        0.0
        < parser_args.novelty_threshold
        < 1.0
    ):
        raise ValueError(
            "--novelty-threshold는 "
            "0과 1 사이여야 합니다."
        )


def main() -> int:
    args = parse_args()
    validate_args(args)

    request_text, request_source = (
        load_request(args)
    )

    case_name = normalize_case_name(
        args.case_name
    )

    input_dir = args.inputs.resolve()

    catalog, discovery_errors = (
        discover_skills(
            DEFAULT_SEARCH_ROOTS
        )
    )

    if discovery_errors:
        print(
            "Skill discovery 확인 필요:",
            json.dumps(
                discovery_errors,
                ensure_ascii=False,
            ),
        )

    skill = activate_skill(
        catalog,
        args.skill,
    )

    client = OllamaClient()

    output_root = (
        ROOT
        / "outputs"
        / "research-b2"
        / case_name
    )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    run_dir = Path(
        tempfile.mkdtemp(
            prefix="run-",
            dir=output_root,
        )
    )

    config = {
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "stage": "B2-1",
        "status": "configured",
        "dry_run": args.dry_run,
        "case_name": case_name,
        "model": client.model,
        "request_source": request_source,
        "input_dir": str(input_dir),
        "input_dir_exists":
            input_dir.is_dir(),
        "skill": {
            "name": skill["name"],
            "base_dir":
                skill["base_dir"],
            "sha256":
                skill["sha256"],
            "description":
                skill["description"],
            "body_chars":
                len(skill["body"]),
        },
        "runtime": {
            "max_workers":
                args.max_workers,
            "max_waves":
                args.max_waves,
            "max_worker_turns":
                args.max_worker_turns,
            "min_sources":
                args.min_sources,
            "novelty_threshold":
                args.novelty_threshold,
        },
        "b2_targets": [
            "parallel_sub_agents",
            "subgoal_isolation",
            "multi_wave_research",
            "evidence_aggregation",
            "verified_citations",
            "two_source_triangulation",
            "source_quality_gate",
            "convergence",
            "context_runtime_optimization",
        ],
    }

    save_json(
        run_dir / "run-config.json",
        config,
    )

    (
        run_dir
        / "request.md"
    ).write_text(
        request_text + "\n",
        encoding="utf-8",
    )

    print()
    print(
        "===== Gemma4 Deep Research B2 ====="
    )
    print("Stage:", config["stage"])
    print("Run:", run_dir)
    print("Case:", case_name)
    print("Model:", client.model)
    print("Skill:", skill["name"])
    print(
        "Skill SHA:",
        skill["sha256"],
    )
    print(
        "Skill body chars:",
        len(skill["body"]),
    )
    print(
        "Request source:",
        request_source["type"],
    )
    print(
        "Input dir:",
        input_dir,
    )
    print(
        "Max workers:",
        args.max_workers,
    )
    print(
        "Max waves:",
        args.max_waves,
    )
    print(
        "Min sources:",
        args.min_sources,
    )
    print(
        "Novelty threshold:",
        args.novelty_threshold,
    )

    if not args.dry_run:
        print()
        print(
            "B2-1에서는 아직 실제 "
            "Gemma Worker를 실행하지 않습니다."
        )
        print(
            "현재 단계는 CLI / Skill Activation / "
            "Run Config 검증 단계입니다."
        )

    print()
    print(
        "설정 저장:",
        run_dir / "run-config.json",
    )
    print(
        "요청 저장:",
        run_dir / "request.md",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
