# Agent Skills on Gemma4 — B2 Deep Research Runtime

공개 [Agent Skills](https://agentskills.io/) 규격과 실제 공개 `SKILL.md`를 **Gemma4 (`gemma4:31b`)** 환경에 적용하여,
Skill이 모델의 조사 절차와 행동을 실제로 변화시킬 수 있는지 검증하는 실험 프로젝트이다.

목표는 공개 Skill의 연구 절차를 Python으로 다시 구현하는 것이 아니다.

```text
연구 방법 = Markdown / SKILL.md
실행 능력 = Python Runtime
```

`SKILL.md`와 B2 Markdown contracts가 **무엇을 어떻게 조사할지**를 정의하고,
Python Runtime은 모델 호출, Worker 실행, Web/PDF 도구, Evidence 검증, 상태 저장과 측정 같은
**범용 실행 능력**만 제공한다.

---

## 현재 판정

**B1 Partial Compatibility: 완료**  
단일 Gemma4 세션에서 Skill 로드, Tool Calling, Skill OFF/ON 행동 변화를 확인했다.
공개 `deep-research`의 병렬 sub-agent / multi-wave / triangulation은 단일 세션으로 충족하지 못했다.

**B2 Deep Research Runtime: E2E 구현 / clean 검증 진행 중**  
Coordinator부터 Synthesis까지 한 프로세스로 잇는 runner가 있다.
Physical AI clean E2E는 검증 중이고, Robot Spec + PDF clean E2E는 예정이다.

| 구성 | 상태 | 상세 |
|---|---|---|
| Coordinator | ✅ | [docs/b2-coordinator.md](docs/b2-coordinator.md) |
| Parallel Workers | ✅ | [docs/b2-parallel-workers.md](docs/b2-parallel-workers.md) |
| Sequential Recovery | ✅ | [docs/b2-recovery.md](docs/b2-recovery.md) |
| Web Search / Fetch | ✅ | [src/web_tools.py](src/web_tools.py) |
| Local PDF Search / Read | ✅ | [docs/b2-local-files.md](docs/b2-local-files.md) |
| Deterministic Evidence Gate | ✅ | [docs/b2-evidence-gate.md](docs/b2-evidence-gate.md) |
| Semantic Auditor | ✅ | [docs/b2-semantic-auditor.md](docs/b2-semantic-auditor.md) |
| Evidence Pool | ✅ | [docs/b2-evidence-pool.md](docs/b2-evidence-pool.md) |
| Replanner | ✅ | [docs/b2-replanner.md](docs/b2-replanner.md) |
| Cumulative Claim Matcher | ✅ | [docs/b2-claim-merge.md](docs/b2-claim-merge.md) |
| Source Independence + Challenge | ✅ | [docs/b2-source-independence.md](docs/b2-source-independence.md) |
| Independence Finalizer | ✅ | [docs/b2-finalizer.md](docs/b2-finalizer.md) |
| Final Synthesis / Citation | ✅ | [docs/b2-synthesis.md](docs/b2-synthesis.md) |
| B2 E2E Runner | ✅ 구현 | [docs/b2-e2e.md](docs/b2-e2e.md) |
| Physical AI clean E2E | 🔄 검증 중 | [tasks/physical-ai-research.md](tasks/physical-ai-research.md) |
| Robot Spec + PDF clean E2E | ⏳ 예정 | [tasks/robot-spec-research.md](tasks/robot-spec-research.md) |

하지 않은 것:

- `scripts/` · `references/` · `assets/` on-demand Resource Loader
- 범용 Compatibility Eval
- `--max-waves` 3 이상 cumulative path

---

## 목차

| # | 주제 | 상세 |
|---|---|---|
| 1 | [Agent Skills 개요](#1-agent-skills-개요) | [reports/01-agent-skills-overview.md](reports/01-agent-skills-overview.md) |
| 2 | [공개 Skill 설치](#2-공개-skill-설치-및-사용-방법) | [reports/02-public-skill-installation.md](reports/02-public-skill-installation.md) |
| 3 | [Runtime 구분](#3-runtime-구분) | [reports/03-gemma4-runtime.md](reports/03-gemma4-runtime.md) |
| 4 | [B2 Deep Research](#4-b2-deep-research) | [docs/b2-e2e.md](docs/b2-e2e.md) |
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

이 프로젝트에서 검증하려는 주장:

> Gemma4가 공개 Agent Skill의 `SKILL.md`를 읽고, 해당 Skill에 정의된 절차적 지식을 바탕으로 조사 행동과 실행 계획을 변화시킬 수 있는가?

의도적으로 피하는 구조:

```python
if skill == "deep-research":
    search(...)
    fetch(...)
    triangulate(...)
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

Source: `ramit-mitra/deep-research-skill`  
검증한 Skill SHA-256: `e8440a6a0cf41739fd5ddce6f66fc1da69e77ee3597162ed35177b86162e1159`

```bash
cp .env.example .env
git submodule update --init --recursive
```

버전 기록: [docs/skill-versions.txt](docs/skill-versions.txt)

이 저장소는 Claude Code 설치 경로를 쓰지 않는다.
`vendor/`의 `SKILL.md`를 Gemma Runtime이 직접 읽는다.

수렴 조건 같은 연구 방법은 Python에 복제하지 않고 public Skill에서 가져온다.

---

## 3. Runtime 구분

상세: [reports/03-gemma4-runtime.md](reports/03-gemma4-runtime.md)

| Runtime | 역할 | 진입점 |
|---|---|---|
| B1 | 단일 세션 Skill OFF/ON, xlsx 초기 실험 | [research_run.py](research_run.py), [run.py](run.py) |
| B2 | 독립 세션 조사·검증·재계획·합성 | [src/research_b2/run.py](src/research_b2/run.py) |

공통:

| 구성 | 코드 |
|---|---|
| Skill Loader | [src/skill_loader.py](src/skill_loader.py) |
| Ollama 클라이언트 | [src/ollama_client.py](src/ollama_client.py) |
| 웹 도구 | [src/web_tools.py](src/web_tools.py) |

역할 구분:

```text
SKILL.md                 → 조사 방법과 절차적 지식
B2 Markdown contracts    → 각 Runtime role의 책임과 입출력 규칙
Python                   → 실제 실행 능력과 deterministic validation
```

계약 원문: [runtime/b2/](runtime/b2/) · 설명: [docs/b2-runtime-contracts.md](docs/b2-runtime-contracts.md)

---

## 4. B2 Deep Research

같은 모델, 같은 Ollama endpoint, 서로 다른 `messages[]`다.

```text
Coordinator
    ↓
plan.json
    ↓
Parallel Workers          (독립 chat session)
    ↓
Sequential Recovery       (failed assignment만)
    ↓
Deterministic Gate        (Web fetch / PDF page)
    ↓
Semantic Auditor          (thinking OFF, 도구 없음)
    ↓
Evidence Pool             (VERIFIED only)
    ↓
Replanner                 (Skill + measurements)
    ↓
Wave 2
    ↓
Cumulative Claim Matcher  (SAME / EXTENDS / CONTRADICTS / NOVEL)
    ↓
Cumulative State
    ↓
Source Independence
    ↓
Adversarial Challenge
    ↓
Finalizer                 (deterministic)
    ↓
Stop Record               (convergence / resource cap)
    ↓
Synthesis                 (citation-validated report)
```

| 문서 | 내용 |
|---|---|
| [E2E Runner](docs/b2-e2e.md) | Coordinator부터 Synthesis까지 한 프로세스 |
| [역할별 thinking](docs/b2-thinking-roles.md) | Coordinator/Worker ON, Auditor OFF |
| [Coordinator](docs/b2-coordinator.md) | 첫 계획만 만든다 |
| [병렬 Worker](docs/b2-parallel-workers.md) | 자기 assignment만 조사하고 JSON을 돌려준다 |
| [Sub-agent](docs/b2-sub-agents.md) | 모델 3개가 아니라 독립 세션 3개 |
| [Recovery](docs/b2-recovery.md) | 실패한 assignment만 순차 재실행 |
| [Local PDF](docs/b2-local-files.md) | `list` / `search` / `read_pdf_pages` |
| [Evidence Gate](docs/b2-evidence-gate.md) | 실제로 읽은 Web/PDF만 통과 |
| [Semantic Auditor](docs/b2-semantic-auditor.md) | 이미 읽은 본문만 판정한다 |
| [Evidence Pool](docs/b2-evidence-pool.md) | VERIFIED evidence만 누적한다 |
| [Replanner](docs/b2-replanner.md) | Skill이 다음 Wave를 정하고, Validator는 schema만 본다 |
| [Claim Merge](docs/b2-claim-merge.md) | Wave claim의 SAME / EXTENDS / CONTRADICTS / NOVEL |
| [Source Independence](docs/b2-source-independence.md) | provenance 기반 독립성 + Challenge |
| [Finalizer](docs/b2-finalizer.md) | Challenge verdict를 상태에만 반영 |
| [Stop Record](docs/b2-stop-record.md) | `max_waves`는 resource cap |
| [Synthesis](docs/b2-synthesis.md) | `[SRCxxx]` / `[PDFxxx p.N]` citation 검증 |
| [Runtime 계약](docs/b2-runtime-contracts.md) | `runtime/b2/` 역할 구분 |

수렴 숫자(출처 10개, novelty 15% 등)는 public `SKILL.md`에만 있다.
[convergence.md](runtime/b2/convergence.md)와 [b2-stop-record.md](docs/b2-stop-record.md)는 측정값과 종료 이유만 기록한다.

요청이 한국어이면 Worker claim과 gap은 [worker.md](runtime/b2/worker.md)에 따라 한국어로 쓴다.
최종 보고서도 다른 언어를 요청하지 않으면 [synthesis.md](runtime/b2/synthesis.md)에 따라 한국어다.

### E2E 실행

상세: [docs/b2-e2e.md](docs/b2-e2e.md)

```bash
# Physical AI
python3 -m src.research_b2.run \
  --task tasks/physical-ai-research.md \
  --skill deep-research \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2 \
  --output-root outputs/research-b2/e2e/physical-ai

# Robot Spec + PDF
python3 -m src.research_b2.run \
  --task tasks/robot-spec-research.md \
  --skill deep-research \
  --input-dir inputs \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2 \
  --output-root outputs/research-b2/e2e/robot-spec \
  --report-out reports/robot-spec-comparison.md
```

단계별 수동 호출도 가능하다. 예시 배치: `outputs/research-b2/parallel-smoke/run-asiwjsyn`

```bash
python3 -m src.research_b2.coordinator --request tasks/physical-ai-research.md --skill deep-research
python3 -m src.research_b2.parallel_workers --plan path/to/plan.json --skill deep-research --max-workers 3 --max-turns 6
python3 -m src.research_b2.recovery --batch path/to/run-* --skill deep-research
python3 -m src.research_b2.evidence_pool --batch path/to/run-* --skill deep-research
python3 -m src.research_b2.replanner --batch path/to/run-* --skill deep-research --max-workers 3 --max-waves 2
```

Worker 성공 조건은 6턴을 채우는 것이 아니라, `max-turns` 안에 도구 호출 없는 최종 JSON을 내는 것이다.

---

## 5. B1 기록

B1은 단일 세션 비교다. 병렬 Worker는 없었다.

### deep-research OFF / ON

상세: [reports/deep-research-off-vs-on-final.md](reports/deep-research-off-vs-on-final.md)

| 항목 | Skill OFF | Skill ON |
|---|---:|---:|
| Turns | 3 | 3 |
| Tool Calls | 8 | 10 |
| Search | 8 | 8 |
| Fetch Page | 0 | 2 |
| Answer chars | 3,822 | 5,508 |
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

B1에서 “없다”고 적었던 병렬 세션, Wave 재계획, Evidence Pack 합성은 B2로 구현했다.
아래는 아직이다.

- Physical AI / Robot Spec **clean E2E** 결과 확정
- Resource Loader, Tool Registry, 자동 Compatibility Eval
- Worker system prompt에 full public Skill body를 넣는 방식의 추가 검토
- 긴 조사에서 600초 `ReadTimeout`과 순차 recovery로 늘어지는 실행 시간
- `--max-waves` 3 이상 cumulative architecture

Known limitations 요약: [docs/known-issues.md](docs/known-issues.md) · [docs/b2-stop-record.md](docs/b2-stop-record.md)

---

## 폴더 안내

| 경로 | 역할 |
|---|---|
| `research_run.py` / `run.py` | B1 단일 세션 실행기 |
| `research_b2.py` | B2 설정 검증만. Worker는 실행하지 않는다 |
| `src/research_b2/run.py` | B2 E2E 진입점 |
| `src/research_b2/` | Coordinator, Worker, Gate, Pool, Replanner, Matcher, Independence, Synthesis |
| `runtime/b2/` | B2 실행 계약. 연구 방법 본문은 Skill에 둔다 |
| `tasks/` | 요청 문서 |
| `docs/` | B2 설명, known-issues, 증빙 |
| `reports/` | B1 실험·개요 기록 |
| `outputs/` | 실행 로그. Git에 포함한다 |
| `inputs/` | 실제 입력 파일 (Git 제외) |
| `vendor/` | 공개 Skill 저장소 |

핵심 원칙:

```text
Public SKILL.md      = procedural knowledge
Markdown Contracts   = runtime role boundaries
Gemma4               = reasoning / semantic decisions
Python Runtime       = generic execution / validation / persistence
```
