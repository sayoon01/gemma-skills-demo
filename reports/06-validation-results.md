# 06. Agent Skills — Gemma4 최종 검증 결과

> 검증 기준일: 2026-09-07  
> 대상 모델: `gemma4:31b`  
> 목적: 공개 Agent Skills를 Claude Code가 아닌 자체 Gemma4 Runtime에서 사용할 수
> 있는지 xlsx 및 deep-research 실험 결과를 종합하여 판정한다.

상위 문서: [README.md](../README.md)

관련:

- [04-xlsx-experiment.md](04-xlsx-experiment.md)
- [deep-research-off-vs-on-final.md](deep-research-off-vs-on-final.md)
- [07-future-work.md](07-future-work.md)

---

## 1. 검증 질문

> 공개 Skill 파일을 다운로드하여 Claude Code 말고 Gemma4에서 사용할 수 있는가?

| 단계 | 질문 |
|---|---|
| A | Skill 파일을 다운로드할 수 있는가? |
| B | `SKILL.md`를 자동 발견할 수 있는가? |
| C | Metadata를 읽고 Skill을 활성화할 수 있는가? |
| D | Gemma4가 Skill Instruction을 이해하는가? |
| E | Skill 지침에 따라 Tool을 선택하는가? |
| F | 실제 Tool을 실행할 수 있는가? |
| G | Tool Result 기반 Multi-turn Agent Loop가 가능한가? |
| H | Skill OFF와 ON에서 행동 변화가 발생하는가? |
| I | 공개 Skill 원본 Workflow를 완전히 실행할 수 있는가? |

---

## 2. 전체 판정

### 최종 판정: **B1 PARTIAL COMPATIBILITY — SUCCESS**

의미: 공개 `SKILL.md` 기반 Agent Skill을 Claude Code 없이 자체 Runtime에서 Gemma4에
적용하여, 실제 Tool Calling과 업무 행동 변화를 발생시키는 것이 가능함을 확인하였다.

의미하지 않는 것: 공개 Skill을 받기만 하면 Gemma4가 모든 Skill을 Native하게 그대로
실행한다 — **아니다**. Tool·Script·Reference·Sub-agent·Sandbox·Context 관리를 제공하는
별도 Agent Runtime이 필요하다.

---

## 3. 검증한 Skill

| Skill | 출처 | 목적 |
|---|---|---|
| `xlsx` | `vendor/anthropic-skills/skills/xlsx` | Skill-driven Excel Tool Calling |
| `deep-research` | `vendor/community-skills/deep-research` | OFF/ON 비교, Web Search/Fetch, Workflow 변화 |

SHA-256 (deep-research):
`e8440a6a0cf41739fd5ddce6f66fc1da69e77ee3597162ed35177b86162e1159`

---

## 4. xlsx 검증 결과

실제 선택·실행 Tool: `inspect_workbook`×2, `read_excel_range`×2.

```text
SKILL.md → Gemma4 → Excel Tool Choice → Actual File Read
```

가 성립함을 확인하였다.

한계: ~32K에서 History 손실, 64K에서 Context 유지 + ReadTimeout 300초.
Skill 자체 문제라기보다 **Tool Result / Context Runtime** 문제.

상세: [04-xlsx-experiment.md](04-xlsx-experiment.md)

---

## 5. deep-research 비교 실험

공통: `gemma4:31b`, `tasks/physical-ai-research.md`, max turn 20,
Tools `web_search` / `fetch_page`.  
변수: Skill OFF vs ON.

### Skill OFF — `run-zqa3vu3e`

| 항목 | 결과 |
|---|---:|
| 상태 | completed |
| Turn / Tool Call / Error | 3 / 8 / 0 |
| Web Search / Fetch | 8 / **0** |
| 고유 Search URL / 읽은 URL | 40 / **0** |
| 답변 길이 / 실행시간 | 3,822자 / 473.015초 |

검색 Query 분해는 있었으나 `fetch_page=0`. title/snippet 중심 최종 보고서.
체계적 Sources / Counter-evidence / Gaps / 명시적 Sub-goal 관리 없음.

### Skill ON 1차 실패 — `run-wp1hegvs`

검색 세분화(ISO/IEC, Testbed, NPU 등) 후 Turn 3에서 ReadTimeout 300초.
elapsed 575.859초. prompt_eval: 3,827 → 9,152.

### Skill ON 재실행 성공 — `run-il0bppa7`

timeout 600초로 조정 후 완료.

| 항목 | OFF | ON |
|---|---:|---:|
| 상태 | completed | completed |
| Turn | 3 | 3 |
| Tool Call / Error | 8 / 0 | 10 / 1 |
| Web Search / Fetch | 8 / 0 | 8 / **2** |
| 고유 Search URL / 읽은 URL | 40 / 0 | 35 / **2** |
| 답변 길이 | 3,822자 | 5,508자 |
| 실행시간 | 473.015초 | **642.762초 (+35.9%)** |

### Skill ON 모델 응답시간

| Turn | Model | Prompt eval | Eval | Tools |
|---|---:|---:|---:|---:|
| 1 | 143.139초 | 3,831 | 1,235 | 5 |
| 2 | 96.667초 | 8,473 | 794 | 5 |
| 3 | **383.130초** | 12,834 | 3,292 | 0 |

Model total 622.936초 / 전체 642.762초 → 대부분 Gemma4 추론.
최종 Synthesis가 최대 병목 (초기 300초 timeout 실패 원인과 일치).

상세: [deep-research-off-vs-on-final.md](deep-research-off-vs-on-final.md)

---

## 6. Skill 적용 후 행동·출력 변화

| 항목 | OFF | ON |
|---|---|---|
| 원문 fetch | 0 | 2 (VLA Survey, Deloitte Physical AI) |
| 출력 구조 | 사용자 5항목 중심 일반 보고서 | TL;DR, Scope, Sub-goals, Findings, Evidence, Counter-evidence, Gaps, Sources, Footnotes |
| Sub-goal | 검색 분해만 | 5개 명시 |
| Counter-evidence / Gaps | 없음 | 별도 Section |
| Sources / Footnote | 미흡 | 생성 |

---

## 7. 미충족 / 부분충족

| 항목 | 상태 | 확인 내용 |
|---|---|---|
| Parallel Sub-agent | 미충족 | 단일 Gemma4만 사용 |
| Multi-wave Research | 미충족 | Gap 후 추가 Wave 없음 |
| 모든 Citation 원문 검증 | 부분충족 | Sources 6개 중 Fetch 2개 |
| 2-source Triangulation | 부분충족 | 복수 Citation ≠ 모두 원문 확인 |
| Web Search 안정성 | 부분충족 | ON에서 Search 1회 Tool Error |
| Source Quality | 부분충족 | Tier 4~5 자료 포함 |
| Runtime Performance | 개선 필요 | OFF 대비 +35.9% |

Citation Formatting은 O, All Citation Full-text Verification은 X.
형식적 Multi-source Citation은 O, 엄격 Independent Triangulation은 부분충족.

---

## 8. 가능한 것 / 아직 안 되는 것

### 가능한 것

Public Skill Download · Discovery · Metadata Parse · Activation · SHA-256 Logging ·
Instruction Injection · Ollama Tool Calling · Excel/Web Tool 실제 실행 ·
Tool Result Feedback · Multi-turn Loop · OFF/ON Behavior Change ·
Skill-driven Output Structure · Runtime Metrics

### 아직 안 되는 것

`scripts/`·`references/`·`assets/` on-demand · `allowed-tools` 자동 Binding ·
Parallel Sub-agent · Multi-wave · Strict Triangulation · All-source Full-text Verify ·
Automatic Source Quality Gate · Context Compaction · Universal Capability Matching

---

## 9. 왜 별도 Runtime이 필요한가

Skill은 업무 지침을 주지만 Capability를 자동 생성하지 않는다.

```text
Public Skills → Skill Runtime
  (Discovery / Activation / Tool Registry / Resource Loader /
   Context Manager / Sub-agent Orchestration / Security)
  → Gemma4
```

---

## 10. 정확한 결론 표현

**과도한 표현:** Gemma4가 Agent Skills를 완전히 지원한다. (현재 실험만으로는 부정확)

**권장 표현:**

> 공개 `SKILL.md` 기반 Agent Skill을 자체 Runtime을 통해 Gemma4에 적용할 수 있으며,
> Skill에 따라 실제 Tool Calling과 Agent 행동이 변화하는 것을 확인하였다. 다만 원본
> Skill이 요구하는 모든 Resource 및 Sub-agent 기능까지 지원하는 Full Compatibility를
> 위해서는 추가 Runtime 구현이 필요하다.

### Stage 판정

| Stage | 내용 | 결과 |
|---|---|---|
| A | Skill Discovery / Activation | SUCCESS |
| B | Gemma4 Tool Calling | SUCCESS |
| C | Actual Tool Execution | SUCCESS |
| D | Skill-driven Behavior Change | SUCCESS |
| E | Full Resource Compatibility | PARTIAL |
| F | Parallel / Multi-agent Workflow | B1에서는 UNSUPPORTED. B2에서 독립 세션으로 구현 |
| **Overall** | **B1 Partial Compatibility** | **SUCCESS** |

위 표는 2026-09-07 B1 판정이다.
B2 단계 구현과 남은 일은 [README.md](../README.md)와 [07-future-work.md](07-future-work.md)를 본다.

---

## 11. 최종 요약

1. `SKILL.md`는 Claude Code 전용 Prompt로만 볼 필요가 없다. Runtime이 구조를 이해하면
   Gemma4에서도 사용할 수 있다.
2. Gemma4는 Skill을 읽고 실제 Tool을 선택했다 (`inspect_workbook` / `read_excel_range`,
   `web_search` / `fetch_page`).
3. OFF: Search → Final. ON: Search → Fetch → Evidence → Counter-evidence → Gaps → Sources.
4. Skill만으로는 부족하다. Context·Tool·Resource·Sub-agent·Security를 잇는 Runtime이 핵심이다.

> Gemma4에서 Agent Skills 적용 가능성을 실제 Tool 실행까지 검증하였으며,
> **B1 수준의 Partial Compatibility를 확인하였다.**
> 병렬 세션과 Evidence Gate는 이후 B2 모듈에서 따로 검증한다.

### 관련 Run (로컬)

- xlsx: `outputs/runs/run-hb_2vzzc`, `run-k_b3sp0q`
- research: `run-zqa3vu3e` (OFF), `run-wp1hegvs` (ON timeout), `run-il0bppa7` (ON success)

### 참고

- [Agent Skills Specification](https://agentskills.io/specification)
- [Client Implementation Guide](https://agentskills.io/client-implementation/adding-skills-support)
