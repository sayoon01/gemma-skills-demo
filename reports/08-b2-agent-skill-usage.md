# Agent Skills on Gemma4

공개 Agent Skills의 `SKILL.md`를 Gemma4에서 실제 실행해보기 위한 실험 프로젝트임.

B1에서는 단일 Gemma4 세션에 Skill을 적용해 Skill OFF/ON 행동 차이를 확인했고,
B2에서는 이를 확장해 **Coordinator + 독립 Worker + Evidence 검증 + Replanner + Multi-Wave Research + Synthesis** 구조로 구현함.

상위: [README.md](../README.md) · [docs/b2-e2e.md](../docs/b2-e2e.md)

핵심 구조는 아래와 같음.

```text
공개 SKILL.md
    ↓
Gemma4가 Skill 절차 해석
    ↓
Coordinator / Replanner가 조사 방향 결정
    ↓
Generic Python Runtime이 실제 실행
```

즉 Deep Research 절차를 Python 코드에 직접 하드코딩한 구조가 아님.

```text
연구 방법 = SKILL.md / Markdown
실행 능력 = Python Runtime
```

---

## B2에서 Agent Skill 사용하는 방법

### 1. 사용할 Skill 준비

B2는 `src/skill_loader.py`를 통해 공개 Skill을 discovery하고 activation함.

현재 Deep Research 실험에 사용한 Skill은 아래에 위치함.

```text
vendor/community-skills/
└── deep-research/
    └── SKILL.md
```

사용 Skill:

```text
ramit-mitra/deep-research-skill
```

현재 실험에 사용한 Skill SHA-256:

```text
e8440a6a0cf41739fd5ddce6f66fc1da69e77ee3597162ed35177b86162e1159
```

Skill 이름은 실행할 때 `--skill`로 전달함.

```bash
--skill deep-research
```

관련: [02-public-skill-installation.md](02-public-skill-installation.md) · [docs/skill-versions.txt](../docs/skill-versions.txt)

---

### 2. 연구 Task 작성

조사할 내용을 별도 Markdown 파일로 작성함.

예:

```text
tasks/physical-ai-research.md
```

B2 Runtime 내부에서 Physical AI 같은 특정 연구 주제를 하드코딩하지 않음.

Task 파일의 내용을 Coordinator가 읽고, 활성화된 Skill의 절차를 기준으로 조사 계획을 생성함.

예시 실행:

```bash
python3 -m src.research_b2.run \
  --task tasks/physical-ai-research.md \
  --skill deep-research \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2
```

---

### 3. Skill이 적용되는 흐름

B2 실행 시 가장 먼저 Coordinator가 실행됨.

```text
Task
 +
Public SKILL.md
 +
controller.md
        ↓
      Gemma4
        ↓
     plan.json
```

Coordinator가 조사 내용을 직접 코드에서 받는 게 아니라,
Gemma4가 Task와 활성화된 Skill을 읽고 조사 단위를 생성함.

예:

```json
{
  "assignment_id": "SG01",
  "title": "...",
  "objective": "...",
  "queries": [
    "..."
  ],
  "source_priority": [
    "official",
    "peer-reviewed"
  ],
  "needs_local_files": false
}
```

생성된 Assignment는 여러 Worker로 전달됨.

관련: [docs/b2-coordinator.md](../docs/b2-coordinator.md)

---

### 4. 독립 Worker 실행

각 Assignment는 독립된 Gemma4 Chat Session에서 실행됨.

```text
Coordinator
   ↓
plan.json
   ↓
├─ Worker SG01
├─ Worker SG02
└─ Worker SG03
```

모델은 모두 동일한 `gemma4:31b`이지만 `messages[]` context는 서로 분리되어 있음.

Worker는 Python에 정의된 연구 절차를 따라가는 게 아니라 `worker.md`, `evidence-policy.md` 등의 Runtime Contract에 따라 generic tools를 사용함.

Web 조사 시 사용할 수 있는 도구:

```text
web_search
fetch_page
```

검색 snippet은 Evidence로 인정하지 않음.

실제 Evidence로 사용하려면 `fetch_page`를 통해 원문을 읽어야 함.

관련: [docs/b2-parallel-workers.md](../docs/b2-parallel-workers.md) · [docs/b2-sub-agents.md](../docs/b2-sub-agents.md)

---

### 5. PDF / 로컬 자료와 함께 Skill 사용

로컬 자료가 필요한 연구라면 `--input-dir`를 같이 전달함.

예:

```bash
python3 -m src.research_b2.run \
  --task tasks/robot-spec-research.md \
  --skill deep-research \
  --input-dir inputs \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2
```

`input_dir`가 있으면 Worker에 아래 generic capability가 추가됨.

```text
list_local_files
search_pdf_text
read_pdf_pages
```

예:

```text
inputs/
└── 로봇 제품 규격.pdf
```

Runtime에 특정 PDF 파일명이나 로봇 제품명을 하드코딩하지 않음.

Worker가 Task와 Skill을 보고 필요한 파일을 직접 찾고 읽도록 구성함.

관련: [docs/b2-local-files.md](../docs/b2-local-files.md)

---

### 6. PDF Evidence 처리

PDF 검색만 했다고 Evidence로 인정하지 않음.

```text
search_pdf_text
    ↓
후보 page 발견
    ↓
read_pdf_pages
    ↓
실제 page 본문 확보
    ↓
Evidence Gate
```

PDF source에는 실제 파일 SHA-256과 page 정보가 기록됨.

최종 보고서 citation 예:

```text
[PDF001 p.2]
```

실제로 검증하지 않은 page를 사용하면 Synthesis Validator에서 거절됨.

관련: [docs/b2-evidence-gate.md](../docs/b2-evidence-gate.md) · [docs/b2-synthesis.md](../docs/b2-synthesis.md)

---

### 7. Worker 실패 시 Recovery

Parallel Worker 실행 중 Ollama timeout 등이 발생할 수 있음.

예:

```text
ReadTimeout
```

B2에서는 실패한 Assignment만 다시 순차 실행함.

```text
Parallel Workers
      ↓
SG01 completed
SG02 failed
SG03 completed
      ↓
Recovery
      ↓
SG02만 sequential retry
```

결과:

```text
recovery/recovery-index.json
```

이미 성공한 Worker는 다시 실행하지 않음.

관련: [docs/b2-recovery.md](../docs/b2-recovery.md)

---

### 8. Evidence 검증

Worker가 생성한 claim을 그대로 최종 보고서에 사용하지 않음.

```text
Worker
  ↓
Deterministic Evidence Gate
  ↓
Semantic Auditor
  ↓
Post-Audit Gate
  ↓
Evidence Pool
```

Deterministic Gate에서는 실제 원문을 읽었는지 확인함.

Semantic Auditor는 별도의 Gemma4 context에서 실제 Evidence 내용이 claim을 지지하는지 판정함.

Auditor는 새로운 검색을 하지 않고 이미 읽은 Evidence만 사용함.

관련: [docs/b2-evidence-gate.md](../docs/b2-evidence-gate.md) · [docs/b2-semantic-auditor.md](../docs/b2-semantic-auditor.md) · [docs/b2-evidence-pool.md](../docs/b2-evidence-pool.md)

---

### 9. Skill 기반 Replanning

Wave 1이 끝나면 현재 조사 상태를 측정함.

예:

```text
distinct_sources_read
unique_verified_sources
single_source_claim_count
pending_independence_claim_count
unsupported_claim_count
unresolved_gap_count
novelty_ratio
```

이 측정값과 public Skill을 다시 Gemma4 Replanner에 전달함.

```text
Public SKILL.md
 +
현재 Evidence 상태
 +
replan.md
        ↓
      Gemma4
        ↓
needs_another_wave
```

예:

```json
{
  "needs_another_wave": true,
  "reason": "...",
  "assignments": [
    ...
  ]
}
```

즉 다음 조사 주제를 Python `if`문으로 결정하지 않음.

Gemma4가 Skill과 현재 조사 결과를 기반으로 다음 Wave를 결정함.

관련: [docs/b2-replanner.md](../docs/b2-replanner.md)

---

### 10. Multi-Wave 결과 누적

Wave 2의 claim을 Wave 1 결과와 비교함.

판정:

```text
SAME
EXTENDS
CONTRADICTS
NOVEL
```

그 결과를 기반으로 cumulative state를 생성함.

```text
Wave 1 Evidence
      +
Wave 2 Evidence
      ↓
Claim Matcher
      ↓
Cumulative State
```

관련: [docs/b2-claim-merge.md](../docs/b2-claim-merge.md)

---

### 11. Source Independence 확인

출처 URL이 2개라고 무조건 triangulation하지 않음.

예를 들어 서로 다른 뉴스 사이트가 같은 기업 보도자료를 그대로 인용했을 수도 있음.

따라서 별도의 Source Independence 단계에서 provenance를 검토함.

```text
Verified Sources
      ↓
Source Independence Audit
      ↓
Adversarial Challenge
```

최종 verdict:

```text
TRIANGULATED
NOT_TRIANGULATED
UNKNOWN
```

`UNKNOWN`이면 충분히 독립적인 출처인지 확인되지 않았다는 의미임.

관련: [docs/b2-source-independence.md](../docs/b2-source-independence.md)

---

### 12. Finalizer

Finalizer는 LLM을 호출하지 않음.

Challenge가 이미 내린 verdict를 cumulative state에 반영만 함.

```text
TRIANGULATED
    → TRIANGULATED

NOT_TRIANGULATED
    → SINGLE_SOURCE

UNKNOWN
    → MULTI_SOURCE_PENDING_INDEPENDENCE
```

Semantic 판단과 Python 상태 처리를 분리하기 위한 구조임.

관련: [docs/b2-finalizer.md](../docs/b2-finalizer.md)

---

### 13. 최종 보고서 생성

검증된 cumulative state만 Synthesis 단계로 전달함.

```text
Final Cumulative State
        +
Stop Record
        +
Task
        ↓
     Gemma4
        ↓
    report.md
```

Web citation:

```text
[SRC001]
```

PDF citation:

```text
[PDF001 p.2]
```

검증되지 않은 source/page citation은 허용하지 않음.

관련: [docs/b2-synthesis.md](../docs/b2-synthesis.md) · [docs/b2-stop-record.md](../docs/b2-stop-record.md)

---

## 실행 예시

### Web 기반 Deep Research

```bash
python3 -m src.research_b2.run \
  --task tasks/physical-ai-research.md \
  --skill deep-research \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2
```

### Web + PDF Deep Research

```bash
python3 -m src.research_b2.run \
  --task tasks/robot-spec-research.md \
  --skill deep-research \
  --input-dir inputs \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2 \
  --report-out reports/robot-spec-comparison.md
```

상세: [docs/b2-e2e.md](../docs/b2-e2e.md)

---

## 다른 Skill을 적용하려면

기본 구조는 동일함.

```text
1. public Skill 준비
2. vendor 경로에 Skill 배치
3. Task 작성
4. --skill <skill-name>으로 실행
```

예:

```bash
python3 -m src.research_b2.run \
  --task tasks/example.md \
  --skill another-skill \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2
```

단, 현재 B2 Runtime이 제공하는 generic capability 범위 내에서 실행 가능한 Skill이어야 함.

현재 주요 capability:

```text
Gemma4 Chat
Web Search
Web Page Fetch
Parallel Worker
Local File Discovery
PDF Text Search
PDF Page Read
Evidence Validation
Semantic Audit
Replanning
Claim Matching
Source Independence
Final Synthesis
```

Skill이 별도 실행 환경이나 새로운 종류의 tool을 요구하면 해당 generic capability를 Runtime에 추가해야 함.

---

## 핵심

B2에서 Skill을 사용하는 방식은 아래와 같음.

```text
SKILL.md를 Python으로 번역
        ❌

SKILL.md를 Gemma4가 직접 읽음
        ↓
Gemma4가 조사 방법 결정
        ↓
Python Runtime이 generic capability 제공
        ✅
```

따라서 B2의 목적은 Deep Research 알고리즘 자체를 새로 만드는 것이 아니라,

> 공개 Agent Skill의 절차적 지식을 Gemma4가 해석하고 실제 multi-agent research runtime에서 실행할 수 있는지 검증하는 것

임.
