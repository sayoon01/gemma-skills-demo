# Gemma4 Deep Research Skill OFF vs ON 비교 결과

## 1. 실험 목적

공개 Agent Skill인 `deep-research`를 Claude Code가 아닌 자체 Gemma4 런타임에서 사용할 수 있는지 검증하고, 동일 모델·동일 질문·동일 웹 도구 조건에서 Skill 적용 전후의 조사 행동 및 결과 차이를 비교하였다.

본 실험은 병렬 sub-agent 기능이 없는 B1 Partial Compatibility Test이다.

---

## 2. 공통 실험 조건

- Model: `gemma4:31b`
- Context: 65,536 tokens
- Temperature: 0
- Max generation: 4,096 tokens
- User request: `tasks/physical-ai-research.md`
- Max turns: 20
- Tools:
  - `web_search`
  - `fetch_page`

### Skill OFF Run

`outputs/research-runs/run-zqa3vu3e`

### Skill ON Run

`outputs/research-runs/run-il0bppa7`

### 활성 Skill

`deep-research`

Skill SHA-256:

`e8440a6a0cf41739fd5ddce6f66fc1da69e77ee3597162ed35177b86162e1159`

Skill path:

`vendor/community-skills/deep-research`

---

## 3. 정량 비교

| 항목 | Skill OFF | Skill ON |
|---|---:|---:|
| 실행 상태 | completed | completed |
| Turn 수 | 3 | 3 |
| Tool Call | 8 | 10 |
| Tool Error | 0 | 1 |
| Web Search | 8 | 8 |
| Fetch Page | 0 | 2 |
| 고유 검색 URL | 40 | 35 |
| 실제 읽은 URL | 0 | 2 |
| 최종 답변 길이 | 3,822자 | 5,508자 |
| 전체 실행시간 | 473.015초 | 642.762초 |
| 실행시간 증가율 | 기준 | 약 35.9% |

Skill ON 결과는 Skill OFF 대비 약 1.36배의 수행시간이 필요하였다.

---

## 4. Skill ON 모델 응답시간

| Turn | Model response time | Prompt eval | Eval | Tool calls |
|---|---:|---:|---:|---:|
| 1 | 143.139초 | 3,831 | 1,235 | 5 |
| 2 | 96.667초 | 8,473 | 794 | 5 |
| 3 | 383.130초 | 12,834 | 3,292 | 0 |

- 모델 총 처리시간: 622.936초
- 전체 실행시간: 642.762초

전체 실행시간의 대부분이 웹 검색이나 페이지 다운로드가 아니라 Gemma4 모델 처리에 사용되었다.

특히 최종 보고서를 합성하는 Turn 3에서 383초가 소요되었다.

초기 Skill ON 시험에서는 HTTP read timeout이 300초였기 때문에 동일한 Turn 3에서 실패하였다. Timeout을 600초로 확장한 이후 동일 조건의 Skill ON 시험이 정상 완료되었다.

---

## 5. Skill OFF 조사 행동

Skill OFF에서도 Gemma4는 사용자 요청을 여러 검색어로 분해하였다.

주요 검색 영역:

- 피지컬 AI 기술 동향
- 이동·자율주행·온디바이스 AI
- Tesla / Figure AI / NVIDIA / Boston Dynamics
- 국내 기업
- VLA
- 상용화 병목
- 국가로봇테스트필드

총 8회의 검색을 수행하여 40개의 고유 검색 결과 URL을 확보하였다.

그러나 `fetch_page` 호출은 0회였다.

즉 검색 결과의 title 및 snippet은 사용했지만 실제 원문 페이지를 열어 확인하는 절차 없이 최종 보고서를 작성하였다.

또한 최종 보고서에는 주장별 URL, 체계적인 출처 등급, Counter-evidence, Gaps and unknowns 등의 Deep Research 절차가 없었다.

---

## 6. Skill ON 조사 행동

Skill ON에서는 8회의 web search와 2회의 fetch_page를 실행하였다.

실제로 읽은 페이지:

1. VLA Survey
2. Deloitte Physical AI and Humanoid Robots

검색 영역도 다음과 같이 세분화되었다.

- 피지컬 AI 전체 기술 동향
- VLA 모델
- On-device AI
- 글로벌 휴머노이드 기업
- 국내 로봇 기업
- 로봇 상용화 병목
- ISO 로봇 안전 표준
- Sim-to-Real 검증
- 국내 공용 시험 인프라

Skill OFF와 달리 검색 결과를 다시 실제 페이지로 읽는 동작이 발생하였다.

---

## 7. 최종 보고서 구조 변화

### Skill OFF

사용자 요청의 5개 분석 항목을 중심으로 일반 기술 분석 보고서를 작성하였다.

### Skill ON

최종 출력에 다음 Deep Research 구조가 나타났다.

- TL;DR
- Scope and framing
- Sub-goals investigated
- Key findings
- Evidence
- Counter-evidence and dissent
- Gaps and unknowns
- Sources
- Markdown footnote citation

이는 `deep-research` Skill의 지침이 Gemma4의 최종 출력 구조에 실제 영향을 주었음을 보여준다.

---

## 8. Skill 적용 효과

### 8.1 명시적 연구 Sub-goal 생성

Skill ON은 다음 5개의 조사 sub-goal을 최종 보고서에 명시하였다.

1. 피지컬 AI의 기술적 정의 및 VLA 구조
2. 글로벌·국내 기업 제품 및 상용화 단계
3. On-device AI와 Sim-to-Real
4. 로봇 안전 표준 및 검증 요구사항
5. 공용 시험 인프라

Skill OFF에서는 검색 질문 분해는 존재했지만 이를 연구 sub-goal로 명시적으로 관리하지 않았다.

### 8.2 실제 페이지 읽기

Skill OFF:

`fetch_page = 0`

Skill ON:

`fetch_page = 2`

따라서 Skill 적용 후 검색 결과의 실제 원문을 확인하려는 행동 변화가 나타났다.

### 8.3 Counter-evidence

Skill ON 보고서에는 휴머노이드 회의론 및 AI Overtrust 문제를 별도의 Counter-evidence 항목으로 기록하였다.

Skill OFF에서는 이러한 반대 근거 조사 구조가 없었다.

### 8.4 Gap 관리

Skill ON은 다음 항목을 확인되지 않은 정보 또는 조사 한계로 분리하였다.

- 실제 판매 대수
- 국내 공용 인프라 세부 현황
- 병렬 sub-agent 부재에 따른 교차검증 한계

Skill OFF에서는 미확인 정보를 별도의 Gap으로 관리하지 않았다.

### 8.5 Citation 구조

Skill ON에서는 Markdown footnote 방식의 Sources section을 생성하였다.

Skill OFF에서는 체계적인 citation 구조가 없었다.

---

## 9. 확인된 한계

### 9.1 모든 Citation을 실제 원문까지 읽은 것은 아님

Skill ON의 최종 Sources는 6개지만 실제 fetch_page를 통해 원문을 읽은 URL은 2개이다.

따라서 일부 출처는 검색 결과 snippet을 기반으로 사용된 것으로 판단된다.

즉 "모든 근거가 실제 원문 검증되었다"고 평가할 수는 없다.

### 9.2 Triangulation은 부분 충족

일부 주장은 2개의 footnote를 사용하지만 두 출처 모두 실제 fetch_page를 거친 것은 아니다.

따라서 중요한 주장에 대해 2개 이상의 독립 원문을 확인하는 엄격한 triangulation은 아직 완전히 검증되지 않았다.

### 9.3 Source quality 편차

최종 Sources에는 연구자료뿐 아니라 일반 블로그 및 산업 웹사이트도 포함되었다.

향후 Source tier 정책을 더 엄격하게 적용할 필요가 있다.

### 9.4 Parallel Sub-agent 미지원

원본 `deep-research` Skill은 병렬 sub-agent 기반 조사를 핵심 원칙으로 요구한다.

현재 B1 Runtime에서는 별도의 Agent Tool이 없기 때문에 단일 Gemma4 agent가 순차적으로 조사하였다.

따라서 원본 Skill의 완전한 실행 환경은 아니다.

### 9.5 Runtime 비용 증가

Skill ON 전체 수행시간은 642.762초로 Skill OFF의 473.015초보다 약 35.9% 증가하였다.

긴 SKILL.md 지침, 증가된 prompt context, 보다 복잡한 조사 계획 및 최종 synthesis가 주요 원인으로 판단된다.

---

## 10. B1 Compatibility 판정

### 판정: 성공 — Partial Compatibility

확인된 기능:

- 공개 SKILL.md 다운로드
- 자체 Skill discovery
- Skill activation
- Gemma4 system context에 Skill 지침 적용
- Gemma4 Tool Calling
- Skill에 따른 조사 전략 변화
- 실제 원문 fetch 유도
- 연구 sub-goal 구성
- Counter-evidence 생성
- Gaps and unknowns 관리
- Sources 및 citation 구조 생성
- Skill의 실행 한계 자체 명시

부분 충족 또는 미지원:

- 병렬 sub-agent
- Multi-wave research
- 모든 citation의 원문 검증
- 엄격한 2-source triangulation
- 완전한 source quality enforcement

---

## 11. 결론

본 실험을 통해 Claude Code를 사용하지 않고도 공개 `SKILL.md` 기반 Agent Skill을 Gemma4 런타임에서 로드하고 사용할 수 있음을 확인하였다.

Skill OFF 대비 Skill ON에서는 단순 검색 결과 생성에서 실제 원문 확인, 연구 sub-goal 구성, Counter-evidence, Gap 관리, Sources 및 citation 기반 보고서 작성으로 조사 행동이 변화하였다.

따라서 Agent Skill의 핵심 개념인 "외부 SKILL.md의 지침을 모델 실행 시 동적으로 제공하여 모델의 Tool 사용 및 업무 수행 방식을 변경하는 것"은 Gemma4에서도 구현 가능한 것으로 확인된다.

다만 원본 `deep-research` Skill은 병렬 sub-agent 사용을 핵심 요구사항으로 포함하므로, 현재 결과는 Full Compatibility가 아닌 B1 Partial Compatibility로 판정한다.

이 문서는 B1 단일 세션 비교다.
이후 독립 세션 병렬 조사와 Evidence Pool, Replanner는 [README.md](../README.md)의 B2 절과 [docs/b2-sub-agents.md](../docs/b2-sub-agents.md)를 본다.
