"""공개 스킬 발견, 기본 메타데이터 검사, 선택한 스킬 활성화."""

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# 저장소별 검색 위치입니다. 개별 스킬 이름을 고정하지 않습니다.
DEFAULT_SEARCH_ROOTS = [
    ROOT / "vendor" / "anthropic-skills" / "skills",
    ROOT / "vendor" / "deep-research",
]


class SkillError(ValueError):
    """스킬 발견 또는 기본 구조 검사 오류."""


def read_definition(path):
    """SKILL.md를 읽고 기본 메타데이터와 본문을 분리한다."""
    path = Path(path).resolve()
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()

    if not lines or lines[0].strip() != "---":
        raise SkillError("첫 줄에 YAML 시작 구분자 ---가 없습니다.")

    end = next(
        (i for i in range(1, len(lines)) if lines[i].strip() == "---"),
        None,
    )
    if end is None:
        raise SkillError("YAML 종료 구분자 ---가 없습니다.")

    metadata = yaml.safe_load("\n".join(lines[1:end]))
    body = "\n".join(lines[end + 1:]).strip()

    if not isinstance(metadata, dict):
        raise SkillError("메타데이터가 key-value 구조가 아닙니다.")

    name = metadata.get("name")
    description = metadata.get("description")

    if (
        not isinstance(name, str)
        or not 1 <= len(name) <= 64
        or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name)
    ):
        raise SkillError("name의 길이 또는 형식이 잘못됐습니다.")

    if name != path.parent.name:
        raise SkillError("name과 부모 폴더 이름이 다릅니다.")

    if (
        not isinstance(description, str)
        or not description.strip()
        or len(description) > 1024
    ):
        raise SkillError("description은 비어 있지 않은 1024자 이하 문자열이어야 합니다.")

    if not body:
        raise SkillError("스킬 지침 본문이 비어 있습니다.")

    return metadata, body


def discover_skills(search_roots):
    """검색 위치 자체와 바로 아래 폴더에서 SKILL.md를 찾는다."""
    catalog = {}
    errors = []
    visited = set()

    for root in search_roots:
        root = Path(root).resolve()

        if not root.is_dir():
            errors.append({"path": str(root), "error": "검색 폴더가 없습니다."})
            continue

        candidates = [root / "SKILL.md"]
        candidates.extend(sorted(root.glob("*/SKILL.md")))

        for path in candidates:
            if not path.is_file():
                continue

            path = path.resolve()
            if path in visited:
                continue
            visited.add(path)

            try:
                metadata, _ = read_definition(path)
                name = metadata["name"]

                if name in catalog:
                    raise SkillError(
                        f"중복 스킬 이름: {name}. 검색 위치를 구분해야 합니다."
                    )

                catalog[name] = {
                    "name": name,
                    "description": metadata["description"],
                    "path": str(path),
                }

            except (OSError, UnicodeError, yaml.YAMLError, SkillError) as exc:
                errors.append({"path": str(path), "error": str(exc)})

    return catalog, errors


def activate_skill(catalog, name):
    """사용자가 선택한 스킬의 본문과 기준 경로를 반환한다."""
    if name not in catalog:
        raise SkillError(f"사용 가능한 목록에 없는 스킬: {name}")

    path = Path(catalog[name]["path"])
    metadata, body = read_definition(path)

    if metadata["name"] != name:
        raise SkillError("발견 이후 스킬 이름이 변경됐습니다.")

    return {
        "name": name,
        "description": metadata["description"],
        "base_dir": str(path.parent),
        "body": body,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        action="append",
        help="스킬 검색 위치. 여러 번 지정할 수 있습니다.",
    )
    parser.add_argument(
        "--skill",
        help="명시적으로 활성화할 스킬 이름",
    )
    args = parser.parse_args()

    roots = [Path(p) for p in args.root] if args.root else DEFAULT_SEARCH_ROOTS
    catalog, errors = discover_skills(roots)

    print(f"발견된 유효 스킬: {len(catalog)}개")
    for name in sorted(catalog):
        print(f"- {name}")

    selected = None
    if args.skill:
        try:
            selected = activate_skill(catalog, args.skill)
            print(f"\n활성화: {selected['name']}")
            print(f"기준 경로: {selected['base_dir']}")
            print(f"본문 길이: {len(selected['body'])}자")
            print(f"파일 SHA-256: {selected['sha256']}")
        except (OSError, UnicodeError, yaml.YAMLError, SkillError) as exc:
            errors.append({"skill": args.skill, "error": str(exc)})

    if not catalog:
        errors.append({"error": "유효한 스킬을 찾지 못했습니다."})

    for error in errors:
        print("확인 필요:", json.dumps(error, ensure_ascii=False))

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not errors else "failed",
        "search_roots": [str(Path(p).resolve()) for p in roots],
        "catalog": list(catalog.values()),
        "selected_skill": (
            {key: value for key, value in selected.items() if key != "body"}
            if selected else None
        ),
        "errors": errors,
        "scope": "기본 구조 검사와 스킬 발견·본문 로딩",
        "limitations": [
            "전체 Agent Skills 규격 인증이 아닙니다.",
            "참조 파일 유효성 및 스크립트 실행은 검사하지 않습니다.",
            "Gemma에 지침을 전달하거나 작업을 실행하지 않습니다.",
        ],
    }

    output_dir = ROOT / "outputs" / "skills"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_file = output_dir / f"{timestamp}.json"
    output_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"\n검사 결과 저장: {output_file}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
