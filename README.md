# Agent Skills — Gemma4 적용 검증

공개 [Agent Skills](https://agentskills.io/home) 규격의 Skill을 Claude Code 없이
Gemma4(Ollama) Runtime에 적용할 수 있는지 검증한 기록입니다.

스킬은 작업 지침(`SKILL.md`)을 제공하고, 실제 검색·파일 읽기·검증은 Python 도구가 수행합니다.

---

## 목차

1. [Agent Skills 개요](#1-agent-skills-개요)
2. [공개 Skill 설치 방법](#2-공개-skill-설치-방법)
3. [Gemma4 적용 구조](#3-gemma4-적용-구조)
4. [xlsx 실험](#4-xlsx-실험)
5. [deep-research 실험](#5-deep-research-실험)
6. [결과](#6-결과)
7. [향후 적용](#7-향후-적용)

---

## 1. Agent Skills 개요

### 규격

- 공식 사이트: [agentskills.io](https://agentskills.io/home)
- 내부 정리: [spec_skill.md](spec_skill.md)
- 기본 구조 검사 결과: [docs/skill-validation.md](docs/skill-validation.md)

### SKILL.md

- YAML frontmatter: `name`, `description` (필수)
- 본문: 에이전트 실행 지침
- `name`은 부모 폴더 이름과 일치, 소문자·숫자·하이픈만 허용

### scripts / references / assets

```text
skill-name/
├── SKILL.md      # 필수
├── scripts/      # 선택: 실행 코드
├── references/   # 선택: 참고 문서
└── assets/       # 선택: 템플릿·정적 자원
```

예: Anthropic `xlsx` — [vendor/anthropic-skills/skills/xlsx](vendor/anthropic-skills/skills/xlsx)

---

## 2. 공개 Skill 설치 방법

### git clone / submodule

이 저장소에서 사용하는 방식입니다.

```bash
git submodule update --init --recursive
```

| 위치 | 출처 |
|---|---|
| `vendor/anthropic-skills` | [anthropics/skills](https://github.com/anthropics/skills) |
| `vendor/deep-research` | [ramit-mitra/deep-research-skill](https://github.com/ramit-mitra/deep-research-skill) |
| `vendor/community-skills/` (로컬) | 동일 deep-research 클론, Git 제외 |

버전 기록: [docs/skill-versions.txt](docs/skill-versions.txt)

### npx skills / Claude·Codex 설치 위치

Agent Skills 생태계에서는 CLI·제품별 설치 경로가 다를 수 있습니다.
이 프로젝트는 **git으로 vendor에 두고 Gemma Runtime이 직접 `SKILL.md`를 읽는 방식**만 검증합니다.
제품별 기본 설치 경로는 [spec_skill.md](spec_skill.md)와 공식 문서를 참고하세요.

---

## 3. Gemma4 적용 구조

```text
요청 문서 + 입력/주제
        ↓
Skill Loader  →  SKILL.md 발견·검사·본문 로드
        ↓
Skill Activation  →  system prompt에 <skill> 주입
        ↓
Tool Binding  →  web_search / fetch_page / Excel 도구 등
        ↓
Agent Loop  →  Gemma chat ↔ tool 실행 ↔ 기록 저장
```

| 구성 | 코드 |
|---|---|
| Skill Loader | [src/skill_loader.py](src/skill_loader.py) |
| Ollama 클라이언트 | [src/ollama_client.py](src/ollama_client.py) |
| 엑셀 공통 실행기 | [run.py](run.py) |
| 웹 연구 실행기 | [research_run.py](research_run.py) |
| 웹 도구 | [src/web_tools.py](src/web_tools.py) |

준비:

```bash
cp .env.example .env
# OLLAMA_BASE_URL, OLLAMA_MODEL=gemma4:31b
git submodule update --init --recursive
```

---

## 4. xlsx 실험

Anthropic 공개 `xlsx` Skill + Gemma4 + 실제 Excel 도구.

| 구분 | 링크 |
|---|---|
| 보고용 검증 결과 | [docs/xlsx-validation-report.md](docs/xlsx-validation-report.md) |
| 대표 성공 증빙 (매출 데모) | [docs/evidence/xlsx-demo/](docs/evidence/xlsx-demo/README.md) |
| Runtime 병목 증빙 | [docs/evidence/xlsx-runtime/](docs/evidence/xlsx-runtime/README.md) |
| Runtime 이슈 정리 | [reports/xlsx-runtime-issues.md](reports/xlsx-runtime-issues.md) |
| Timeout·prompt 증가 | [reports/ollama-timeout-and-prompt-growth.md](reports/ollama-timeout-and-prompt-growth.md) |
| 확인된 문제 | [docs/known-issues.md](docs/known-issues.md) |
| 요청 예 | [tasks/budget-comparison.md](tasks/budget-comparison.md) |
| 매출 전용 도구 | [src/tools/sales_workbook.py](src/tools/sales_workbook.py) |

### 실제 Skill / 요청 / tool call / 결과

- Skill: `vendor/anthropic-skills/skills/xlsx`
- 매출 데모: Gemma가 `create_sales_workbook`을 1회 호출 → 수식·차트·재계산 검증 passed  
  → [agent-result.json](docs/evidence/xlsx-demo/agent-result.json), [screenshot.png](docs/evidence/xlsx-demo/screenshot.png)
- 예실대비표 읽기: `inspect_workbook` / `read_excel_range` 자율 선택·실행 성공

### 발견 문제

- 셀별 JSON이 커지면 32K context에서 대화 유실
- 64K에서는 context 유지되나 최종 분석 300초 ReadTimeout
- **병목은 Skill 지원이 아니라 Runtime 효율** ([xlsx-runtime 증빙](docs/evidence/xlsx-runtime/README.md))

```bash
python3 run.py \
  --skill xlsx \
  --input "inputs/....xlsx" \
  --request "tasks/budget-comparison.md"
```

---

## 5. deep-research 실험

공개 community Skill + 동일 요청으로 Skill OFF / ON 비교.

| 구분 | 링크 |
|---|---|
| 준비 증빙 (로드·웹 도구) | [docs/evidence/deep-research-setup/](docs/evidence/deep-research-setup/README.md) |
| Skill OFF baseline | [reports/deep-research-skill-off-baseline.md](reports/deep-research-skill-off-baseline.md) |
| OFF vs ON 중간 비교 | [reports/deep-research-off-vs-on-partial.md](reports/deep-research-off-vs-on-partial.md) |
| 검색 순위 vs source tier | [reports/source-tier-vs-search-rank.md](reports/source-tier-vs-search-rank.md) |
| 요청 문서 | [tasks/physical-ai-research.md](tasks/physical-ai-research.md) |
| Skill 원본 | [vendor/deep-research/SKILL.md](vendor/deep-research/SKILL.md) |

```bash
# Skill OFF
python3 research_run.py --request tasks/physical-ai-research.md

# Skill ON
python3 research_run.py --request tasks/physical-ai-research.md --skill deep-research
```

기록: `outputs/research-runs/run-*/` (Git 제외)

웹 도구 스모크:

```bash
PYTHONPATH=. python3 checks/check_web_tools.py
```

---

## 6. 결과

### 가능한 것

- 공개 Skill의 `SKILL.md`를 Gemma Runtime에 로드·활성화
- Skill 지침에 따른 도구 자율 선택·실행 (xlsx 읽기, 웹 검색·페이지 읽기)
- Skill OFF/ON을 동일 요청·동일 도구로 비교
- 실행 기록(`answer.md`, `tool-calls.json`, `metrics.json` 등) 보존

### 안 되는 것 / 한계

- deep-research가 요구하는 **parallel sub-agent** 전체 구현 (B1에서는 미지원으로 명시)
- 대량 tool 결과를 그대로 context에 넣을 때의 안정적 장문 분석 (timeout·유실)
- Skill만으로 파일 생성·재계산이 자동 구현되지는 않음 — **도구 바인딩이 필요**
- DuckDuckGo HTML 직접 파싱 부적합 → `ddgs` 사용 ([known-issues](docs/known-issues.md))

### 별도 Runtime이 필요한 이유

Skill은 지침 파일이고, Gemma는 모델입니다. 그 사이에서
**로더 · 도구 · agent loop · 검증 · 기록**을 담당하는 Runtime이 있어야
공개 Skill을 Claude Code 없이 재현·비교할 수 있습니다.

---

## 7. 향후 적용

1. tool 결과 compact화 (xlsx 셀별 JSON 축소) — 기록만, 심화 최적화는 후순위
2. deep-research OFF/ON 비교 완료·공개 증빙 정리
3. source-tier / 인용 규율을 Runtime 검증 항목으로 연결
4. 필요 시 sub-agent·재계산 도구를 단계적으로 추가
5. 센터 보고용 요약은 `docs/`·`reports/`·`docs/evidence/`를 조합해 작성

---

## 폴더 안내

| 경로 | 역할 |
|---|---|
| `run.py` / `research_run.py` | 공통 실행기 |
| `tasks/` | 요청 문서 |
| `docs/` | 보고서·known-issues |
| `docs/evidence/` | 공개 증빙 |
| `reports/` | 실험 분석 메모 |
| `outputs/` | 원본 실행 로그 (Git 제외) |
| `inputs/` | 실제 입력 파일 (Git 제외) |
| `checks/` | 환경·스모크·회귀 |
| `vendor/` | 공개 Skill 저장소 |

기존 확인용:

```bash
python checks/check_environment.py
python checks/check_skill_prompt.py
python checks/check_sales_agent.py --input examples/sales-demo.json
python checks/inspect_run.py outputs/runs/run-XXXX
```
