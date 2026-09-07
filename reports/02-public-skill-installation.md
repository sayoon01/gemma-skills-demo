# 02. 공개 Agent Skill 설치 및 사용 방법

> 조사 기준일: 2026-09-07  
> 목적: 공개 Skill을 확보하는 방법과 Skills CLI, Claude, Codex 사용 방식을 정리하고,
> 본 Gemma4 프로젝트에서의 관리 방식을 정의한다.

상위 문서: [README.md](../README.md)  
버전 기록: [docs/skill-versions.txt](../docs/skill-versions.txt)

---

## 1. 공개 Skill을 가져오는 방법

Agent Skill은 기본적으로 하나의 디렉터리 패키지이므로, 공개 Repository에서 직접 Clone하거나
Skill 배포 CLI / 제품별 설치 기능을 사용할 수 있다.

1. Git Repository 직접 Clone
2. `npx skills` CLI
3. Claude의 Skill / Plugin 설치
4. Codex의 Local Skill / Skill Installer
5. 자체 Runtime의 Vendor Directory에 직접 등록

---

## 2. Git Clone

가장 단순하고 구현체에 종속되지 않는 방식이다.

```bash
git clone https://github.com/anthropics/skills.git
```

Clone 후 `skills/docx`, `skills/pdf`, `skills/pptx`, `skills/xlsx` 등 구조를 확인할 수 있다.

Community Skill도 동일하다.

```bash
mkdir -p vendor/community-skills

git clone \
  https://github.com/ramit-mitra/deep-research-skill.git \
  vendor/community-skills/deep-research
```

장점: 제품 비종속, 원본 `SKILL.md` 확인, 버전 관리, 자체 Loader에서 직접 사용,
`scripts/`·`references/`·`assets/`까지 전체 구조 확보.

Claude Code가 아닌 Gemma4 Runtime을 검증하는 경우 가장 명확한 방식이다.

---

## 3. npx skills

Skills 생태계에서는 skills CLI로 공개 Skill을 설치할 수 있다.

```bash
npx skills add <skill-name>
npx skills add vercel-labs/agent-skills
```

CLI 옵션과 지원 Agent 목록은 변경될 수 있으므로 설치 전 `npx skills --help` 또는
[Skills CLI 문서](https://www.skills.sh/docs/cli)를 확인하는 것이 안전하다.

공개 Skill은 실행 지침이나 Script를 포함할 수 있으므로 설치 전 내용 검토가 필요하다.

---

## 4. Anthropic 공개 Skills Repository의 성격

`anthropics/skills`는 Agent Skills 예시와 Claude에서 사용하는 Document Skill을 공개한다.

모든 Skill이 동일한 라이선스는 아니다. Repository 설명에 따르면 일반 예제 Skill 중
다수는 Open Source이지만 `docx` / `pdf` / `pptx` / `xlsx` Document Skill은
source-available 형태로 제공된다.

따라서 보고서에서는 "Anthropic의 모든 공개 Skill이 오픈소스"라고 쓰지 않고
**Anthropic 공개 Repository에서 제공되는 Skill**이라고 구분한다.

---

## 5. Claude Code에서 Anthropic Skills 사용

Anthropic 공개 Repository는 Claude Code Plugin Marketplace 등록을 안내한다.

```text
/plugin marketplace add anthropics/skills
/plugin install document-skills@anthropic-agent-skills
/plugin install example-skills@anthropic-agent-skills
```

설치 후 자연어로 특정 Skill 사용을 요청할 수 있다.

---

## 6. Claude Custom Skill

Claude 제품에서는 직접 작성한 Skill을 패키징해 사용할 수 있다.
일반적인 절차: Skill directory 생성 → `SKILL.md` 작성 → Resource/Script 추가 →
패키징 → 활성화 → Trigger Prompt로 테스트.

제품 UI/패키징 제약은 공개 Agent Skills 표준보다 더 엄격할 수 있다
(예: `description` 길이). Open Spec ≠ 각 제품의 모든 세부 제한이 동일하다.

---

## 7. Codex에서 Skill 사용

현재 OpenAI 문서에 따르면 ChatGPT/Codex Skill도 Open Agent Skills Standard를 기반으로 한다.

| 방식 | 예 |
|---|---|
| Explicit | `/skills`, `$skill-name` |
| Implicit | 요청이 `description`과 일치하면 자동 선택 |

`description`은 Trigger 정확도에 매우 중요하다.

### Local Skill 위치 (공식 문서 기준)

| Scope | 경로 |
|---|---|
| Repository | `$CWD/.agents/skills` … `$REPO_ROOT/.agents/skills` |
| User | `$HOME/.agents/skills` |
| Admin | `/etc/codex/skills` |
| System | Codex Bundled (예: `skill-creator`) |

Symlink된 Skill Directory도 탐색할 수 있다고 설명한다.

### Skill Installer

```text
$skill-installer linear
```

다른 Repository에서 Skill을 가져오도록 요청할 수도 있다. 새 Skill이 안 보이면
Codex 재시작이 필요할 수 있다.

---

## 8. 본 Gemma4 프로젝트의 설치 방식

특정 Agent 제품 설치 폴더를 쓰지 않고, 외부 Skill을 `vendor/`에 보관한다.

```text
vendor/
├── anthropic-skills/skills/   # xlsx, pdf, pptx, ...
└── community-skills/
    └── deep-research/
        └── SKILL.md
```

`src/skill_loader.py` 기본 검색:

```python
DEFAULT_SEARCH_ROOTS = [
    ROOT / "vendor" / "anthropic-skills" / "skills",
    ROOT / "vendor" / "community-skills",
]
```

(과거 `vendor/deep-research` 중복 경로는 discovery warning을 유발해 제거했다.)

장점: Claude/Codex 설치 위치와 분리, 원본 변경 방지, 공급자 혼합 관리,
SHA-256 기록, Gemma4에서 동일 Skill 사용, 실험 재현성.

```bash
git submodule update --init --recursive
```

---

## 9. Skill 설치와 Skill 실행은 다르다

```text
Skill Install ≠ Skill Execution
```

`SKILL.md`를 받았다고 Gemma4가 자동으로 쓰는 것은 아니다.

```text
Download → Discovery → Validation → Activation
  → Instruction Injection → Tool Binding → Agent Loop
```

`deep-research`를 Clone한 것만으로 Web Search가 생기지는 않는다.
Runtime에 `web_search` / `fetch_page`가 연결되어 있어야 한다.

---

## 10. 보안상 주의사항

Community Skill은 신뢰되지 않은 외부 코드와 동일하게 취급하는 것이 안전하다.

확인: `SKILL.md`의 외부 명령, `scripts/` 내용, Network, 파일 삭제/수정, Shell,
Credential, Upload, Dependency 설치.

운영 환경에서는 Skill Review → Permission Check → Sandbox → Tool Allowlist → Execution.

---

## 11. 정리

| 방식 | 목적 | 장점 |
|---|---|---|
| Git Clone | 원본 Skill 확보 | 제품 독립, 자체 Runtime에 적합 |
| `npx skills` | Skills 생태계 설치 | 편의성 |
| Claude Plugin | Claude Code 사용 | 공식 Claude 통합 |
| Claude Custom Skill | Claude에 Skill 추가 | 제품 내 Trigger |
| Codex `.agents/skills` | Local/Repo Skill | Git·Scope 관리 |
| Codex `$skill-installer` | 설치 자동화 | Codex 내부 편의 |
| 프로젝트 `vendor/` | Gemma4 실험 | 모델·제품 독립 검증 |

본 프로젝트는 **Git Clone + Vendor Directory + Skill Loader**를 기준으로 검증한다.

### 참고

- [Skills CLI](https://www.skills.sh/docs/cli)
- [Anthropic Skills](https://github.com/anthropics/skills)
- [Claude Custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills)
- [Agent Skills Specification](https://agentskills.io/specification)
