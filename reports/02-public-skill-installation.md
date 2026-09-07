# 2. 공개 Skill 설치 및 사용 방법

상위 문서: [README.md](../README.md)

버전 기록: [docs/skill-versions.txt](../docs/skill-versions.txt)

---

## 2.1 Git Repository 직접 Clone

가장 단순한 방법은 Skill을 제공하는 Git repository를 직접 Clone하는 것이다.

```bash
git clone https://github.com/anthropics/skills.git
```

Community Skill도 동일하게 받을 수 있다.

```bash
git clone <skill-repository-url>
```

Clone 후 실제 Skill directory에서 다음 구조를 확인한다.

```text
skill-name/
└── SKILL.md
```

필요한 경우 `scripts/` · `references/` · `assets/` 도 함께 사용한다.

### 본 프로젝트 vendor 구조

외부 Skill 원본을 변경하지 않고 다음과 같이 관리한다.

```text
vendor/
├── anthropic-skills/
│   └── skills/
│       ├── xlsx/
│       ├── pdf/
│       ├── pptx/
│       └── ...
│
└── community-skills/
    └── deep-research/
        └── SKILL.md
```

```bash
git submodule update --init --recursive
```

이 구조의 장점은 외부 Skill과 자체 Runtime 코드를 분리하여 관리할 수 있다는 점이다.

Skill Loader 기본 검색 경로 (`src/skill_loader.py`):

- `vendor/anthropic-skills/skills/`
- `vendor/community-skills/`

(과거 `vendor/deep-research` 중복 경로는 discovery warning을 유발해 제거했다.
활성 deep-research는 `vendor/community-skills/deep-research`만 사용한다.)

---

## 2.2 npx skills

공개 Agent Skills 생태계에서는 skills CLI를 이용해 Skill을 검색·설치할 수도 있다.

```bash
npx skills add <owner>/<repository>
```

예:

```bash
npx skills add vercel-labs/agent-skills
```

Repository에 여러 Skill이 존재할 경우 특정 Skill만 선택할 수 있다.

```bash
npx skills add vercel-labs/agent-skills \
  --skill frontend-design
```

대상 Agent를 지정하는 것도 가능하다.

```bash
npx skills add vercel-labs/agent-skills \
  --skill frontend-design \
  --agent claude-code
```

### 주요 옵션

| 옵션 | 설명 |
|---|---|
| `-g, --global` | User scope에 설치 |
| `-a, --agent` | 설치할 Agent 지정 |
| `-s, --skill` | 특정 Skill 선택 |
| `-l, --list` | Repository의 Skill 목록 확인 |
| `--copy` | Symlink 대신 파일 복사 |
| `-y, --yes` | 확인 과정 생략 |

설치하지 않고 일시적으로 Skill prompt를 생성하는 `skills use` 방식도 제공된다.

```bash
npx skills use vercel-labs/agent-skills \
  --skill web-design-guidelines \
  --agent claude-code
```

즉 Agent Skills는 반드시 하나의 특정 제품에서만 다운로드해야 하는 형식이 아니라
Git repository, CLI, Plugin 등의 방식으로 배포할 수 있다.

---

## 2.3 Claude Code

Claude Code에서는 Project 단위 Skill을 다음 위치에 둘 수 있다.

```text
<project>/.claude/skills/<skill-name>/SKILL.md
```

사용자 전역 범위에서는 일반적으로:

```text
~/.claude/skills/<skill-name>/
```

Skill은 `/skill-name`으로 명시적으로 사용할 수도 있으며, 요청 내용과 `description`이
일치하면 자동으로 선택될 수도 있다.

Anthropic의 공개 `anthropics/skills` repository는 Claude Code Plugin marketplace
형태로 설치하는 방법도 제공한다.

---

## 2.4 Codex

현재 Codex는 Agent Skills 규격을 지원하며 Repository Skill의 기본 위치는:

```text
<repository>/.agents/skills/
```

사용자 전역 Skill:

```text
$HOME/.agents/skills/
```

관리자가 머신 공통 Skill을 제공하는 경우:

```text
/etc/codex/skills/
```

Codex에서는 명시적으로 Skill을 선택하거나 작업 내용에 따라 자동 활성화할 수 있다.
예: `$skill-name` 또는 `/skills`.

---

## 핵심 정리

Agent마다 Skill 저장 위치와 발견 방식은 다르지만, 내부 Skill package의 핵심 형식은
`SKILL.md` 기반 Agent Skills 구조를 공유할 수 있다.

**본 프로젝트 검증 범위:** git으로 `vendor/`에 두고 Gemma Runtime이 직접 `SKILL.md`를
읽는 방식. 제품별 기본 설치 경로의 완전 호환을 주장하지 않는다.
