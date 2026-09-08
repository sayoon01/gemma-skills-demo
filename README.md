# Agent Skills — Gemma4 적용 검증

공개 [Agent Skills](https://agentskills.io/home) 규격과 실제 Skill 구현을 조사하고,
Claude Code에 종속되지 않은 환경에서 **Gemma4 (`gemma4:31b`)** 가 공개 `SKILL.md`를
읽고 조사 절차를 바꿀 수 있는지 검증한 실험 프로젝트이다.

목표는 Skill 로직을 Python으로 다시 짜는 것이 아니다.
공개 `SKILL.md`가 연구 방법을 정하고, Runtime은 도구를 붙이고, 측정하고, 기록을 남긴다.

---

## 현재 판정

**B1 Partial Compatibility: 완료**  
단일 Gemma4 세션에서 Skill 로드, Tool Calling, Skill OFF/ON 행동 변화를 확인했다.

**B2 Deep Research Runtime: 단계별 구현·스모크 실행까지**  
같은 `gemma4:31b`의 독립 Chat Session으로 Coordinator, 병렬 Worker, Evidence Gate,
Semantic Auditor, Evidence Pool, Replanner, Claim Merge, Source Independence를 돌렸다.
한 명령으로 Wave 전체를 잇는 실행기는 아직 없다. `research_b2.py`는 설정 검증만 한다.

하지 않은 것:

- 최종 사용자 보고서 합성 모듈. 출력 언어와 Evidence Pack 경계는 [synthesis.md](runtime/b2/synthesis.md)에만 있다
- `scripts/` · `references/` · `assets/` on-demand 로더
- 범용 Compatibility Eval

---

## 목차

| # | 주제 | 상세 |
|---|---|---|
| 1 | [Agent Skills 개요](#1-agent-skills-개요) | [reports/01-agent-skills-overview.md](reports/01-agent-skills-overview.md) |
| 2 | [공개 Skill 설치](#2-공개-skill-설치-및-사용-방법) | [reports/02-public-skill-installation.md](reports/02-public-skill-installation.md) |
| 3 | [Runtime 구분](#3-runtime-구분) | [reports/03-gemma4-runtime.md](reports/03-gemma4-runtime.md) |
| 4 | [B2 Deep Research](#4-b2-deep-research) | [docs/b2-sub-agents.md](docs/b2-sub-agents.md) |
| 5 | [B1 기록](#5-b1-기록) | [reports/06-validation-results.md](reports/06-validation-results.md) |
| 6 | [아직 남은 것](#6-아직-남은-것) | [reports/07-future-work.md](reports/07-future-work.md) |

---

## 1. Agent Skills 개요

상세: [reports/01-agent-skills-overview.md](reports/01-agent-skills-overview.md)

Agent Skills는 특정 LLM 기능이 아니라, Runtime이 읽는 업무 지침 패키지다.
최소 단위는 `SKILL.md`다.

```text
Discovery (name + description)
    → Activation (SKILL.md 전체)
    → Execution (필요한 tool / reference만)
```

관련: [spec_skill.md](spec_skill.md), [docs/skill-validation.md](docs/skill-validation.md)

---

## 2. 공개 Skill 설치 및 사용 방법

상세: [reports/02-public-skill-installation.md](reports/02-public-skill-installation.md)

```text
vendor/
├── anthropic-skills/skills/
└── community-skills/
    └── deep-research/
        └── SKILL.md
```

```bash
cp .env.example .env
git submodule update --init --recursive
```

버전 기록: [docs/skill-versions.txt](docs/skill-versions.txt)

이 저장소는 Claude Code 설치 경로를 쓰지 않는다.
`vendor/`의 `SKILL.md`를 Gemma Runtime이 직접 읽는다.

---

## 3. Runtime 구분

상세: [reports/03-gemma4-runtime.md](reports/03-gemma4-runtime.md)

| Runtime | 역할 | 진입점 |
|---|---|---|
| B1 | 단일 세션 Skill OFF/ON, xlsx 초기 실험 | [research_run.py](research_run.py), [run.py](run.py) |
| B2 | 독립 세션 조사·검증·재계획 | `src/research_b2/` |

공통:

| 구성 | 코드 |
|---|---|
| Skill Loader | [src/skill_loader.py](src/skill_loader.py) |
| Ollama 클라이언트 | [src/ollama_client.py](src/ollama_client.py) |
| 웹 도구 | [src/web_tools.py](src/web_tools.py) |

`SKILL.md`는 무엇을 어떻게 할지를 정한다.
Python은 그 규칙을 주제에 맞게 다시 쓰지 않는다.

---

## 4. B2 Deep Research

같은 모델, 같은 Ollama endpoint, 서로 다른 `messages[]`다.

```text
Coordinator
    ↓
plan.json
    ↓
Worker SG01 / SG02 / SG03   (동시, thinking 사용)
    ↓
Deterministic Gate
    ↓
Semantic Auditor             (순차, thinking OFF, 도구 없음)
    ↓
Post-Audit Gate
    ↓
unique URL Evidence Pool
    ↓
Public SKILL.md + measurements
    ↓
Gemma Replanner
    ↓
Generic Validator → schema repair
    ↓
다음 Wave plan
    ↓
Wave 2 Evidence Pool
    ↓
Claim Merge                 (thinking OFF, 관계만 판정)
    ↓
Cumulative State            (측정과 누적만)
    ↓
Source Independence         (thinking OFF, SAME family만)
```

| 문서 | 내용 |
|---|---|
| [역할별 thinking](docs/b2-thinking-roles.md) | Coordinator/Worker ON, Auditor OFF |
| [Coordinator](docs/b2-coordinator.md) | 첫 계획만 만든다 |
| [병렬 Worker](docs/b2-parallel-workers.md) | 자기 assignment만 조사하고 JSON을 돌려준다 |
| [Sub-agent](docs/b2-sub-agents.md) | 모델 3개가 아니라 독립 세션 3개 |
| [Semantic Auditor](docs/b2-semantic-auditor.md) | 이미 읽은 본문만 판정한다 |
| [Evidence Pool](docs/b2-evidence-pool.md) | 새 조사 없이 고유 URL만 모은다 |
| [Replanner](docs/b2-replanner.md) | Skill이 다음 Wave를 정하고, Validator는 schema만 본다 |
| [Claim Merge](docs/b2-claim-merge.md) | Wave claim의 SAME / EXTENDS / CONTRADICTS / NOVEL만 비교한다 |
| [Source Independence](docs/b2-source-independence.md) | URL 개수가 아니라 출처 provenance로 독립성을 본다 |
| [Runtime 계약](docs/b2-runtime-contracts.md) | `runtime/b2/` 역할 구분 |

계약 원문: [runtime/b2/](runtime/b2/)

수렴 숫자(출처 10개, novelty 15% 등)는 public `SKILL.md`에만 있다.
[convergence.md](runtime/b2/convergence.md)는 측정값과 종료 이유만 기록한다.

요청이 한국어이면 Worker claim과 gap은 [worker.md](runtime/b2/worker.md)에 따라 한국어로 쓴다.
최종 보고서도 다른 언어를 요청하지 않으면 [synthesis.md](runtime/b2/synthesis.md)에 따라 한국어다.
고유명사, 모델명, URL, 출처 원문 용어는 그대로 둔다.
이 규칙을 넣기 전에 돌린 스모크 로그는 영어 claim일 수 있다.

### 이 저장소에서 실제로 돌린 방식

모듈을 단계마다 호출한다. 예시 배치는 `outputs/research-b2/parallel-smoke/run-asiwjsyn`이다.

```bash
# 1. 계획
python3 -m src.research_b2.coordinator \
  --request tasks/physical-ai-research.md \
  --skill deep-research

# 2. Wave 1 병렬 Worker
python3 -m src.research_b2.parallel_workers \
  --plan outputs/research-b2/coordinator-smoke/plan-*/plan.json \
  --skill deep-research \
  --max-workers 3 \
  --max-turns 6

# 3. 이미 읽은 결과만 Evidence Pool
python3 -m src.research_b2.evidence_pool \
  --batch outputs/research-b2/parallel-smoke/run-asiwjsyn \
  --skill deep-research

# 4. 다음 Wave 판단. 조사는 하지 않는다
python3 -m src.research_b2.replanner \
  --batch outputs/research-b2/parallel-smoke/run-asiwjsyn \
  --skill deep-research \
  --max-workers 3 \
  --max-waves 3

# 5. 후속 plan을 Wave 2로 실행
python3 -m src.research_b2.parallel_workers \
  --plan path/to/replan.json \
  --skill deep-research \
  --max-workers 3 \
  --max-turns 6 \
  --wave 2

# 6. Wave 2 Pool을 만든 뒤, 이전 Pool과 의미 비교
python3 -m src.research_b2.cumulative_matcher \
  --prior-pool path/to/wave-1/evidence-pool.json \
  --new-pool path/to/wave-2/evidence-pool.json \
  --skill deep-research \
  --output-root path/to/cumulative/wave-2-match

# 7. Matcher 판정을 누적 상태로만 접는다
python3 -m src.research_b2.cumulative_state \
  --prior-pool path/to/wave-1/evidence-pool.json \
  --new-pool path/to/wave-2/evidence-pool.json \
  --match-result path/to/match-*/result.json \
  --output path/to/cumulative-state.json

# 8. SAME family의 VERIFIED 출처 독립성
python3 -m src.research_b2.source_independence \
  --cumulative path/to/cumulative-state.json \
  --skill deep-research \
  --output-root path/to/cumulative/independence-wave2
```

실패한 Assignment만 다시 돌리는 recovery는 배치의 `plan.json`과 `parallel-result.json`을 읽어 `run_worker()`를 한 번 더 호출한다.
Worker 성공 조건은 6턴을 채우는 것이 아니라, `max-turns` 안에 도구 호출 없는 최종 JSON을 내는 것이다.

---

## 5. B1 기록

B1은 단일 세션 비교다. 병렬 Worker는 없었다.

### deep-research OFF / ON

상세: [reports/deep-research-off-vs-on-final.md](reports/deep-research-off-vs-on-final.md)

| 항목 | Skill OFF | Skill ON |
|---|---:|---:|
| Fetch Page | 0 | 2 |
| 실행시간 | 473.015초 | 642.762초 |

```bash
python3 research_run.py --request tasks/physical-ai-research.md
python3 research_run.py --request tasks/physical-ai-research.md --skill deep-research
```

기록: `outputs/research-runs/run-zqa3vu3e` (OFF), `run-il0bppa7` (ON)

관련: [OFF baseline](reports/deep-research-skill-off-baseline.md) ·
[timeout 기록](reports/ollama-timeout-and-prompt-growth.md) ·
[source tier](reports/source-tier-vs-search-rank.md) ·
[셋업 증빙](docs/evidence/deep-research-setup/README.md)

### xlsx

상세: [reports/04-xlsx-experiment.md](reports/04-xlsx-experiment.md)

공개 `xlsx` `SKILL.md`로 Excel 도구 선택까지는 확인했다.
대량 cell JSON이 context와 timeout 병목이었다.
xlsx 보조 스크립트와 요청 파일은 저장소에서 뺐고, 당시 증빙만 남겼다.

[runtime 이슈](reports/xlsx-runtime-issues.md) ·
[증빙](docs/evidence/xlsx-runtime/README.md) ·
[known-issues](docs/known-issues.md)

---

## 6. 아직 남은 것

상세: [reports/07-future-work.md](reports/07-future-work.md)

B1에서 “없다”고 적었던 병렬 세션과 Wave 재계획은 B2 모듈로 구현했다.
아래는 아직이다.

- Coordinator부터 Independence까지 한 프로세스로 잇기
- Evidence Pack으로 최종 보고서 작성. 계약과 한국어 출력 규칙만 있다
- Resource Loader, Tool Registry, 자동 Compatibility Eval
- 긴 조사에서 600초 ReadTimeout과 순차 recovery로 늘어지는 실행 시간

---

## 폴더 안내

| 경로 | 역할 |
|---|---|
| `research_run.py` / `run.py` | B1 단일 세션 실행기 |
| `research_b2.py` | B2 설정 검증만. Worker는 실행하지 않는다 |
| `src/research_b2/` | B2 Coordinator, Worker, Gate, Pool, Replanner, Matcher, Independence |
| `runtime/b2/` | B2 실행 계약. 연구 방법 본문은 Skill에 둔다 |
| `tasks/` | 요청 문서 |
| `docs/` | B2 설명, known-issues, 증빙 |
| `reports/` | B1 실험·개요 기록 |
| `outputs/` | 실행 로그. Git에 포함한다 |
| `inputs/` | 실제 입력 파일 (Git 제외) |
| `vendor/` | 공개 Skill 저장소 |
