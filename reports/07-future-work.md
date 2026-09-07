# 7. 향후 적용

상위 문서: [README.md](../README.md)

관련:

- [deep-research-off-vs-on-final.md](deep-research-off-vs-on-final.md)
- [ollama-timeout-and-prompt-growth.md](ollama-timeout-and-prompt-growth.md)
- [source-tier-vs-search-rank.md](source-tier-vs-search-rank.md)
- [xlsx-runtime-issues.md](xlsx-runtime-issues.md)
- [06-validation-results.md](06-validation-results.md)

---

현재 B1 실험에서는 공개 `SKILL.md`를 Gemma4에 적용하여 Skill Discovery, Activation,
Tool Calling 및 Agent Loop가 동작하는 것을 확인하였다.

다만 `deep-research` 원본 Skill의 요구사항을 기준으로 보면 일부 기능은 아직 미지원이거나
부분적으로만 충족되었다. 또한 Skill 적용에 따른 Runtime 비용과 Tool 안정성 문제도
확인되었다.

따라서 향후 적용에서는 아래 항목을 우선적으로 보완할 예정이다.

---

## 7.1 현재 미충족·부분충족 사항

| 항목 | 현재 상태 | 실험에서 확인된 내용 |
|---|---|---|
| 병렬 Sub-agent | 미충족 | 현재 Runtime은 단일 Gemma4 Agent만 실행하며 deep-research가 요구하는 병렬 조사 구조는 지원하지 않음 |
| Multi-wave Research | 미충족 | 1차 조사 후 Gap을 분석하여 추가 조사 Wave를 수행하는 반복 구조가 없음 |
| 모든 Citation 원문 검증 | 부분충족 | 최종 Sources 6개 중 `fetch_page`로 실제 원문을 읽은 URL은 2개 |
| 2-source Triangulation | 부분충족 | 일부 주장에 복수 Citation이 존재하지만 모든 출처가 실제 원문 검증된 것은 아님 |
| Web Search 안정성 | 부분충족 | Skill ON 실행에서 `web_search` 1회 오류 발생 |
| Source Quality 관리 | 부분충족 | 최종 결과에 Tier 4~5 수준의 산업자료·블로그 출처가 포함됨 |
| Runtime 성능 | 개선 필요 | Skill ON 실행시간이 Skill OFF 대비 약 35.9% 증가함 |

---

## 7.2 Parallel Sub-agent 지원

`deep-research` Skill은 하나의 Agent가 모든 조사를 순차 수행하는 방식이 아니라
여러 Sub-agent가 독립적인 조사 범위를 병렬로 수행하는 구조를 요구한다.

현재:

```text
Gemma4
  ↓
검색
  ↓
검색
  ↓
원문 확인
  ↓
최종 분석
```

향후:

```text
Gemma4 Controller
      │
      ├── Research Agent A
      │      └── 기술 구조 조사
      │
      ├── Research Agent B
      │      └── 기업·제품 조사
      │
      ├── Research Agent C
      │      └── 표준·안전 조사
      │
      └── Research Agent D
             └── 시험 인프라 조사
                    │
                    ▼
              Evidence Merge
                    │
                    ▼
               Final Agent
```

형태로 확장한다. 이를 통해 원본 `deep-research` Skill의 병렬 조사 요구사항을 검증한다.

---

## 7.3 Multi-wave Research 및 Convergence

현재 B1에서는 검색과 원문 확인 후 바로 최종 보고서를 생성한다.

향후에는 다음 구조를 적용한다.

```text
Wave 1 조사
    ↓
Evidence 수집
    ↓
Claim / Gap 분석
    ↓
근거 부족?
 ┌──YES───────────┐
 │                ↓
 │           Wave 2 조사
 │                ↓
 │          Evidence 보강
 │                ↓
 └────────── 재평가
                  ↓
            Convergence 판단
                  ↓
              최종 보고서
```

예를 들어 기업의 실제 판매 단계에 대한 근거가 부족하면 새로운 검색 query를 생성하고
추가 원문을 조사하도록 한다.

---

## 7.4 Citation 원문 검증 강화

Skill ON 결과에서는 총 6개의 출처가 최종 보고서에 포함되었지만 실제 `fetch_page`를
통해 원문을 읽은 Source는 2개였다.

따라서 현재 구조에서는 검색 결과의 title/snippet이 최종 Citation으로 사용될 가능성이 있다.

향후에는 Citation으로 사용할 Source에 대해 다음 조건을 적용한다.

```text
Search Result
    ↓
Citation 후보 선정
    ↓
fetch_page 성공?
 ├── YES → Evidence 등록 가능
 └── NO  → 미검증 Source 표시
```

최종 Sources에는 다음 상태를 기록할 수 있다.

- `VERIFIED`
- `SEARCH_ONLY`
- `FETCH_FAILED`

이를 통해 “검색 결과에서 발견한 자료”와 “실제로 원문까지 검증한 자료”를 구분한다.

---

## 7.5 2-source Triangulation 엄격 적용

`deep-research` Skill은 중요한 주장에 대해 가능한 경우 두 개 이상의 독립 Source를
통한 교차검증을 요구한다.

현재 결과에서는 하나의 주장에 `[^1][^2]`와 같이 복수 Citation이 붙은 사례가 있었지만,
두 출처 모두 실제 페이지를 읽은 것은 아니었다.

향후 Evidence를 다음과 같이 관리한다.

```text
Claim
  │
  ├── Source A → VERIFIED
  ├── Source B → VERIFIED
  │
  └── Independent?
          │
          ├── YES → TRIANGULATED
          └── NO  → SINGLE-SOURCE
```

최종 보고서에서는 다음 상태를 구분하여 표시하도록 한다.

- `TRIANGULATED`
- `SINGLE-SOURCE`
- `UNVERIFIED`

---

## 7.6 Source Quality 관리

Skill ON 결과에서는 연구자료뿐 아니라 Tier 4~5 수준의 산업자료 및 일반 블로그도
최종 Source에 포함되었다.

향후에는 Source의 유형과 신뢰도를 자동 분류하고, 중요한 주장에는 가능한 한 높은 Tier를
우선하도록 한다.

| Tier | 예 |
|---|---|
| 1 | 공식기관 / 제조사 공식문서 / 표준기관 |
| 2 | Peer-reviewed 논문 / 연구기관 |
| 3 | 공신력 있는 전문기관 및 산업보고서 |
| 4 | 산업매체 / 전문 Web 자료 |
| 5 | Blog / Community / 기타 2차 자료 |

검색 순위가 높다는 이유만으로 낮은 Tier의 자료를 바로 Evidence로 사용하는 것을 방지한다.

특히 핵심 기술 사양, 제품 판매 단계, 표준 요구사항 등의 Material Claim에는
Tier 1~2 출처를 우선하도록 한다.

관련 관측점: [source-tier-vs-search-rank.md](source-tier-vs-search-rank.md)

---

## 7.7 Web Tool 안정성 개선

Skill ON 실험에서는 총 10개의 Tool Call 중 `web_search` 1회가 실패하였다.

따라서 Runtime에 다음 기능을 추가한다.

- Search Retry
- Query 변경 후 재검색
- 검색 Backend Fallback
- Timeout 제어
- Tool Error를 Agent에 명확히 반환
- 동일 실패 Query 반복 방지

```text
web_search
    ↓
실패
    ↓
Retry 1
    ↓
계속 실패?
    ↓
Query Reformulation
    ↓
Fallback Search
```

이를 통해 일시적인 검색 서비스 오류가 전체 Deep Research 결과에 영향을 주지 않도록 한다.

---

## 7.8 Runtime 및 Context 최적화

Skill OFF 실험:

- 전체 실행시간: **473.015초**

Skill ON 실험:

- 전체 실행시간: **642.762초** (+약 35.9%)

Skill ON의 모델 처리시간:

| Turn | Model response time |
|---|---:|
| 1 | 143.139초 |
| 2 | 96.667초 |
| 3 | 383.130초 |
| **Model Total** | **622.936초** |

전체 실행시간 대부분이 Gemma4 추론에 사용되었으며, 특히 최종 Synthesis 단계가
가장 큰 병목으로 확인되었다.

향후 다음 최적화를 적용한다.

- `SKILL.md` Context 최소화
- Progressive Disclosure 강화
- 검색 결과 중복 제거
- Tool Result 요약
- Evidence Pack 기반 Context 압축
- 이전 Turn의 불필요한 검색 결과 제거
- Prompt Token Budget 관리
- 최종 Synthesis 전 Evidence 구조화
- Long-running inference timeout 관리

목표는 Skill 품질을 유지하면서 Skill OFF 대비 증가한 Runtime 비용을 줄이는 것이다.

관련: [ollama-timeout-and-prompt-growth.md](ollama-timeout-and-prompt-growth.md)

---

## 7.9 Skill Resource Loader 확장

현재 B1 Runtime은 주로 `SKILL.md`를 활성화하는 단계까지 구현되어 있다.

향후에는 Skill 내부의 `scripts/` · `references/` · `assets/` 를 필요한 시점에만
읽어 사용하는 Resource Loader를 구현한다.

```text
Skill Activation
      ↓
SKILL.md
      ↓
작업 중 Resource 필요
      │
      ├── references/ 읽기
      ├── scripts/ 실행
      └── assets/ 사용
```

이를 통해 Agent Skills의 Progressive Disclosure 구조를 보다 완전하게 구현한다.

---

## 7.10 Tool Registry 및 Capability Matching

현재 각 Runner가 사용할 Tool을 직접 등록한다.

향후에는 Skill이 요구하는 Capability와 Runtime에 존재하는 Tool을 자동으로 연결한다.

```text
Skill
  │
  └── 필요한 Capability
          │
          ▼
      Tool Registry
          │
   ┌──────┼──────┐
   ▼      ▼      ▼
 Web    Excel   Shell
```

이를 통해 새로운 공개 Skill을 설치할 때 Skill별 전용 Runner를 새로 만드는 대신
공통 Agent Runtime에서 실행할 수 있도록 확장한다.

---

## 7.11 자동 Compatibility Evaluation

향후에는 Skill을 실행한 뒤 호환성을 자동 평가하도록 한다.

평가 항목:

- Skill 발견 성공 여부
- Skill Activation 여부
- 요구 Tool 제공 여부
- Tool Call 성공률
- Search 수 / Fetch 수
- Verified Source 수
- Citation Coverage
- Triangulated Claim 비율
- Source Tier
- Prompt Token / Generation Token
- Turn별 응답시간 / 전체 실행시간
- Skill instruction 준수율

최종적으로 Skill별 결과를 다음 상태로 자동 판정하는 방식을 검토한다.

- `FULL`
- `PARTIAL`
- `UNSUPPORTED`
- `FAILED`

---

## 7.12 B2 검증 목표

다음 단계인 B2에서는 특히 다음 항목을 우선 검증한다.

1. Parallel Gemma4 Sub-agent 실행
2. Sub-goal별 독립 조사
3. Multi-wave Research
4. Evidence Aggregation
5. 모든 주요 Citation 원문 확인
6. 2-source Triangulation
7. Source Quality Gate
8. Convergence 판단
9. Context 및 Runtime 최적화

B2가 완료되면 현재의 **SKILL.md 중심 Partial Compatibility**에서 벗어나
공개 Agent Skill의 원본 Workflow를 보다 충실하게 실행할 수 있는
**범용 Gemma4 Agent Runtime**으로 확장하는 것을 목표로 한다.

| 단계 | 범위 | 상태 |
|---|---|---|
| B1 | SKILL.md 중심 Partial Compatibility | **완료** |
| B2 | Parallel Sub-agent · Multi-wave · Evidence Gate | 예정 |
| B3 | Resource Loader · Eval · Sandbox 강화 | 검토 |
