# Agent Skills — Gemma4 적용 검증

공개 [Agent Skills](https://agentskills.io/home) 규격과 실제 Skill 구현을 조사하고,
Claude Code에 종속되지 않은 환경에서 **Gemma4 (`gemma4:31b`)** 가 공개 `SKILL.md`
기반 Skill을 사용할 수 있는지 검증한 실험 프로젝트이다.

---

## 프로젝트 개요

목표로 하는 것은 특정 Skill의 로직을 Python으로 다시 구현하는 것이 아니다.
공개 `SKILL.md`가 정의한 업무 절차를 Gemma4가 해석하고, **실제 Tool 사용 방식과
결과 생성 방식에 반영할 수 있는지** 확인하는 것이다.

### 주요 검증 내용

1. Agent Skills 규격 및 사용 방식 조사
2. 공개 Skill 다운로드 및 구조 분석
3. 자체 Skill Loader 구현
4. Gemma4에 Skill instruction 주입
5. Skill에 필요한 Tool 연결
6. Gemma4 Tool Calling 기반 Agent Loop 실행
7. `xlsx` Skill 실제 적용
8. Community `deep-research` Skill 적용
9. Skill OFF / ON 비교
10. Context, Runtime, Tool-result 크기 등 호환성 문제 분석

### 현재 판정

**B1 Partial Compatibility 검증 완료**

- Skill 로드·활성화·Tool Calling·행동 변화: 확인
- Parallel sub-agent / Multi-wave / Resource Loader: 후속(B2)

---

## 목차

| # | 주제 | 상세 |
|---|---|---|
| 1 | [Agent Skills 개요](#1-agent-skills-개요) | [reports/01-agent-skills-overview.md](reports/01-agent-skills-overview.md) |
| 2 | [공개 Skill 설치 및 사용](#2-공개-skill-설치-및-사용-방법) | [reports/02-public-skill-installation.md](reports/02-public-skill-installation.md) |
| 3 | [Gemma4 적용 구조](#3-gemma4-적용-구조) | [reports/03-gemma4-runtime.md](reports/03-gemma4-runtime.md) |
| 4 | [xlsx Skill 실험](#4-xlsx-skill-실험) | [reports/04-xlsx-experiment.md](reports/04-xlsx-experiment.md) |
| 5 | [deep-research Skill 실험](#5-deep-research-skill-실험) | [reports/deep-research-off-vs-on-final.md](reports/deep-research-off-vs-on-final.md) |
| 6 | [검증 결과](#6-검증-결과) | [reports/06-validation-results.md](reports/06-validation-results.md) |
| 7 | [향후 적용](#7-향후-적용) | [reports/07-future-work.md](reports/07-future-work.md) |

---

## 1. Agent Skills 개요

상세: [reports/01-agent-skills-overview.md](reports/01-agent-skills-overview.md)

### 1.1 Agent Skills란

Agent Skills는 AI Agent에 **업무 수행 방법·전문 지식·반복 가능한 Workflow**를
제공하기 위한 경량 공개 포맷이다.

기본 단위는 Skill directory이며, 최소한 `SKILL.md`를 포함한다.

```text
skill-name/
├── SKILL.md      # 필수
├── scripts/      # 선택
├── references/   # 선택
└── assets/       # 선택
```

Agent Skills는 특정 LLM의 내장 기능이 아니라, **Agent Runtime이 읽고 사용하는
업무 지침 패키지**로 보는 것이 적절하다. Skill Loader와 Tool Runtime만 있으면
Claude 외 모델에서도 적용 가능성을 검증할 수 있다.

### 1.2 SKILL.md 규격

YAML Frontmatter + Markdown Body로 구성된다.

| Field | 필수 | 설명 |
|---|---|---|
| `name` | 필수 | Skill 이름. 디렉토리명과 일치, 최대 64자, 소문자·숫자·하이픈 |
| `description` | 필수 | 기능 및 **언제 활성화할지** (최대 1,024자) |
| `license` | 선택 | 라이선스 |
| `compatibility` | 선택 | 실행환경·패키지·네트워크 요구 |
| `metadata` | 선택 | 구현체용 추가 메타데이터 |
| `allowed-tools` | 선택/실험적 | 허용 Tool 선언 |

본문에는 단계별 작업, 입출력, 검증, 오류 처리, Tool 사용 시점 등을 적는다.

### 1.3 Progressive Disclosure

처음부터 모든 Skill 파일을 Context에 넣지 않는다.

```text
Discovery (name + description)
    → Activation (SKILL.md 전체)
    → Execution (필요한 scripts / references / assets만)
```

본 프로젝트 Runtime도 Discovery → Activation → Tool Execution 흐름을 따른다.

관련: [spec_skill.md](spec_skill.md), [docs/skill-validation.md](docs/skill-validation.md)

---

## 2. 공개 Skill 설치 및 사용 방법

상세: [reports/02-public-skill-installation.md](reports/02-public-skill-installation.md)

### 이 저장소에서 쓰는 방식

외부 Skill 원본은 변경하지 않고 `vendor/`에 분리한다.

```text
vendor/
├── anthropic-skills/skills/   # xlsx, pdf, pptx, ...
└── community-skills/
    └── deep-research/
        └── SKILL.md
```

```bash
git submodule update --init --recursive
```

버전 기록: [docs/skill-versions.txt](docs/skill-versions.txt)

### 다른 설치 경로 (참고)

| 방식 | 요약 |
|---|---|
| `git clone` | Repository를 직접 받아 Skill directory 사용 |
| `npx skills add` | CLI로 검색·설치 (`--skill`, `--agent` 등) |
| Claude Code | `.claude/skills/<name>/SKILL.md` |
| Codex | `.agents/skills/`, `~/.agents/skills/` 등 |

제품마다 **저장 위치·발견 방식은 다르지만**, 패키지 핵심은 `SKILL.md` 기반 구조를 공유한다.
이 프로젝트는 **git으로 vendor에 두고 Gemma Runtime이 직접 읽는 방식만** 검증한다.

---

## 3. Gemma4 적용 구조

상세: [reports/03-gemma4-runtime.md](reports/03-gemma4-runtime.md)

```text
Public Skill Repository
        ↓
   Skill Loader (Discovery / Validation / Activation)
        ↓
     SKILL.md → Gemma4 System Context
        ↓
   Tool Selection (Ollama Tool Calling)
        ↓
   Runtime Tool 실행 → Tool Result → Gemma4 재호출
        ↓
   (Agent Loop 반복) → Final Answer
```

| 구성 | 코드 |
|---|---|
| Skill Loader | [src/skill_loader.py](src/skill_loader.py) |
| Ollama 클라이언트 | [src/ollama_client.py](src/ollama_client.py) |
| 엑셀 실행기 | [run.py](run.py) |
| 웹 연구 실행기 | [research_run.py](research_run.py) |
| 웹 도구 | [src/web_tools.py](src/web_tools.py) |

### 역할 구분

| 요소 | 역할 |
|---|---|
| `SKILL.md` | **무엇을 어떻게** 해야 하는가 |
| Tool | **실제로 무엇을 실행**할 수 있는가 |
| Runtime | 로드 · 바인딩 · Agent Loop · 기록 |

### 현재 구현 범위

| 기능 | 상태 |
|---|---|
| SKILL.md Discovery / Validation / Activation | O |
| System Prompt Injection | O |
| Ollama Tool Calling / Result Feedback | O |
| Multi-turn Agent Loop / Run Logging | O |
| scripts·references·assets On-demand Loader | X |
| allowed-tools 자동 Binding | X |
| Parallel Sub-agent / Multi-wave Research | X |
| Context Compaction | X |

준비:

```bash
cp .env.example .env
# OLLAMA_BASE_URL, OLLAMA_MODEL=gemma4:31b
git submodule update --init --recursive
```

---

## 4. xlsx Skill 실험

상세: [reports/04-xlsx-experiment.md](reports/04-xlsx-experiment.md)

Anthropic 공개 `xlsx` Skill로 Excel 구조 확인·범위 읽기·도구 자율 선택을 검증했다.

| 구분 | 링크 |
|---|---|
| Runtime 이슈 정리 | [reports/xlsx-runtime-issues.md](reports/xlsx-runtime-issues.md) |
| Runtime 병목 증빙 | [docs/evidence/xlsx-runtime/](docs/evidence/xlsx-runtime/README.md) |
| 매출 데모 증빙 | [docs/evidence/xlsx-demo/](docs/evidence/xlsx-demo/README.md) |
| known-issues | [docs/known-issues.md](docs/known-issues.md) |

### 확인

- `SKILL.md` 로드 후 `inspect_workbook` / `read_excel_range` 자율 선택·실행 성공

### 발견 문제

| 설정 | 결과 |
|---|---|
| ~32K context | 파일 읽기 성공, 요청 분석 미완료 (대화 유실 의) |
| 64K context | Context 유지, 최종 분석 300초 ReadTimeout |

**병목은 Skill 지원이 아니라 Runtime 효율**(대량 cell JSON → context·처리시간).

```bash
python3 run.py \
  --skill xlsx \
  --input "inputs/....xlsx" \
  --request "tasks/budget-comparison.md"
```

---

## 5. deep-research Skill 실험

상세 최종 비교: [reports/deep-research-off-vs-on-final.md](reports/deep-research-off-vs-on-final.md)

동일 모델·동일 질문·동일 웹 도구에서 Skill OFF / ON을 비교했다.
(병렬 sub-agent 없는 **B1 Partial Compatibility Test**)

| 항목 | Skill OFF | Skill ON |
|---|---:|---:|
| Turn | 3 | 3 |
| Tool Call | 8 | 10 |
| Web Search | 8 | 8 |
| Fetch Page | **0** | **2** |
| 실제 읽은 URL | 0 | 2 |
| 답변 길이 | 3,822자 | 5,508자 |
| 실행시간 | 473.015초 | 642.762초 (+35.9%) |

### Skill ON에서 나타난 변화

- 실제 페이지 원문 확인 (`fetch_page`)
- 명시적 연구 Sub-goal
- TL;DR / Evidence / Counter-evidence / Gaps / Sources / Footnote citation

### 관련 문서

| 문서 | 내용 |
|---|---|
| [Skill OFF baseline](reports/deep-research-skill-off-baseline.md) | OFF 단독 고정 |
| [중간 비교 (timeout 실패)](reports/deep-research-off-vs-on-partial.md) | ON 1차 실패 기록 |
| [Timeout·prompt 증가](reports/ollama-timeout-and-prompt-growth.md) | 300→600초 조치 |
| [검색 순위 vs source tier](reports/source-tier-vs-search-rank.md) | Wikipedia vs Primary |
| [셋업 증빙](docs/evidence/deep-research-setup/README.md) | Skill 로드·웹 도구 |

```bash
# Skill OFF
python3 research_run.py --request tasks/physical-ai-research.md

# Skill ON
python3 research_run.py \
  --request tasks/physical-ai-research.md \
  --skill deep-research
```

기록: `outputs/research-runs/run-*/` (Git 제외)

---

## 6. 검증 결과

상세: [reports/06-validation-results.md](reports/06-validation-results.md)

### 가능한 것

- 공개 Skill 다운로드 · `SKILL.md` 발견 · Metadata 검사 · Activation
- Gemma4 Context에 Skill 적용 · Tool Calling · Tool Result 기반 반복 추론
- Skill에 따른 **행동 변화**와 **결과 Format 변화**

→ Claude Code 없이도 Agent Skills의 **핵심 실행 개념**을 Gemma4에서 구현·확인할 수 있다.

### 현재 제한

`SKILL.md`만 받는다고 기능이 자동으로 생기지 않는다. Skill이 요구하는
**Runtime Capability**가 필요하다.

| Skill 요구 | Runtime 필요 |
|---|---|
| Web Search | `web_search` Tool |
| Excel 읽기 | Excel Tool |
| Script 실행 | Sandbox / Shell |
| Sub-agent | Agent Spawn |

Skill은 업무 절차를 주고, **실행환경 자체는 주지 않는다.**
범용 사용을 위해서는 Agent Skills를 해석하는 **별도 Runtime 계층**이 필요하다.

---

## 7. 향후 적용

상세: [reports/07-future-work.md](reports/07-future-work.md)

B1에서 Discovery · Activation · Tool Calling · Agent Loop는 확인했다.
다만 `deep-research` 원본 요구 대비 미충족·부분충족과 Runtime 비용·Tool 안정성 문제가
남았다. 향후에는 아래를 우선 보완한다.

### 7.1 현재 미충족·부분충족 (요약)

| 항목 | 상태 |
|---|---|
| 병렬 Sub-agent / Multi-wave Research | 미충족 |
| 모든 Citation 원문 검증 / 2-source Triangulation | 부분충족 |
| Web Search 안정성 / Source Quality | 부분충족 |
| Runtime 성능 (ON +35.9%) | 개선 필요 |

### 우선 보완 항목

1. **Parallel Sub-agent** — Controller + Research Agent A~D → Evidence Merge
2. **Multi-wave / Convergence** — Gap 탐지 후 Wave 2 → 종료 판단
3. **Citation 원문 검증** — `VERIFIED` / `SEARCH_ONLY` / `FETCH_FAILED`
4. **2-source Triangulation** — `TRIANGULATED` / `SINGLE-SOURCE` / `UNVERIFIED`
5. **Source Quality Gate** — Tier 1~5, Material Claim에 고Tier 우선
6. **Web Tool 안정성** — Retry · Query Reformulation · Backend Fallback
7. **Runtime / Context 최적화** — Result 요약, Compaction, Synthesis 병목 완화
8. **Resource Loader** — `scripts/` · `references/` · `assets/` on-demand
9. **Tool Registry** — Capability ↔ Tool 자동 Binding
10. **자동 Compatibility Eval** — `FULL` / `PARTIAL` / `UNSUPPORTED` / `FAILED`

B2 우선 목표: Parallel Sub-agent · Multi-wave · Evidence Aggregation · Citation/Triangulation
Gate · Source Quality · Convergence · Runtime 최적화.
상세 다이어그램·수치는 [07-future-work.md](reports/07-future-work.md) 참고.

---

## 현재 결론

공개 Agent Skills의 `SKILL.md` 구조를 Claude Code가 아닌 **Gemma4 Runtime**에서도
활용할 수 있음을 확인했다.

Gemma4는 활성화된 Skill 지침에 따라 Tool을 선택하고, Agent Loop를 수행하며,
Skill OFF와 비교해 조사 방식·최종 결과 구조를 바꿨다.

다만 Agent Skills는 단순 Prompt 파일이 아니라 Tool·Script·Reference·Sub-agent 등과
결합되는 구조이므로, 다양한 공개 Skill을 범용 실행하려면 **규격을 해석하는 Runtime**이
필요하다.

**현재 단계: B1 Partial Compatibility 검증 완료**  
후속(B2): Parallel Sub-agent · Multi-wave · Evidence Gate로 원본 Workflow 호환 확대.

---

## 폴더 안내

| 경로 | 역할 |
|---|---|
| `run.py` / `research_run.py` | 공통 실행기 |
| `tasks/` | 요청 문서 |
| `docs/` | 보고서·known-issues |
| `docs/evidence/` | 공개 증빙 |
| `reports/` | 실험·개요 상세 보고서 |
| `outputs/` | 원본 실행 로그 (Git 제외) |
| `inputs/` | 실제 입력 파일 (Git 제외) |
| `checks/` | 환경·스모크·회귀 |
| `vendor/` | 공개 Skill 저장소 |

```bash
python checks/check_environment.py
python checks/check_skill_prompt.py
PYTHONPATH=. python3 checks/check_web_tools.py
```
