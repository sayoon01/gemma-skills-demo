# Gemma4 Deep Research Skill OFF vs ON 중간 비교

## 1. 비교 목적

동일한 Gemma4 모델, 동일한 사용자 요청, 동일한 웹 검색 및 페이지 읽기 도구 조건에서 공개 `deep-research` Agent Skill 활성화 여부에 따라 조사 행동이 어떻게 달라지는지 비교한다.

이번 비교의 Skill ON 실험은 병렬 sub-agent가 없는 B1 Partial Compatibility Test이다.

---

## 2. 실행 조건

### 공통 조건

- 모델: gemma4:31b
- 요청: tasks/physical-ai-research.md
- 최대 Turn: 20
- 제공 도구:
  - web_search
  - fetch_page

### Skill OFF

- 실행 모드: baseline
- Run: outputs/research-runs/run-zqa3vu3e
- 상태: completed

### Skill ON

- 실행 모드: skill:deep-research
- Run: outputs/research-runs/run-wp1hegvs
- 상태: failed
- 실패 원인: Ollama API의 3번째 모델 응답이 300초 내 완료되지 않아 ReadTimeout 발생

---

## 3. 정량 비교

| 항목 | Skill OFF | Skill ON |
|---|---:|---:|
| 실행 상태 | completed | failed / timeout |
| 검색 호출 | 8 | 10 이상 실행 |
| 페이지 fetch | 0 | 실패 시점까지 0 |
| Skill | 미적용 | deep-research |
| 최종 답변 | 생성 | 미생성 |
| Tool 오류 | 0 | 검색 Tool 자체 오류 없음 |
| 모델 처리 실패 | 없음 | Turn 3 ReadTimeout |

Skill ON은 최종 결과 생성 전에 종료되었으므로 최종 답변 길이, 인용 품질, Counter-evidence, Gaps, Sources 형식 등은 아직 공정하게 비교할 수 없다.

---

## 4. Skill OFF 관찰 결과

Skill OFF 상태에서도 Gemma4는 사용자 요청을 여러 검색 주제로 분해하였다.

주요 검색 영역:

- 피지컬 AI 전체 기술 동향
- 이동·자율주행·작업수행·온디바이스 AI
- 주요 기업 및 제품
- 국내 기업
- VLA 모델
- 상용화 병목
- 시험·검증
- 국가로봇테스트필드

그러나 총 8회의 web_search 이후 fetch_page를 한 번도 호출하지 않았다.

따라서 실제 원문을 읽지 않고 검색 결과의 title과 snippet을 기반으로 최종 보고서를 생성하였다.

최종 답변에도 주장별 URL과 체계적인 출처 추적 정보가 부족했고, 조사 실행 시점과 일치하지 않는 작성일을 생성하는 오류도 발견되었다.

---

## 5. Skill ON 관찰 결과

Skill ON 상태에서는 첫 두 Turn에서 총 10개의 검색 query를 생성하였다.

검색 범위는 다음과 같이 보다 세분화되었다.

- 피지컬 AI 전체 동향
- 자율작업 및 온디바이스 AI
- Tesla Optimus / Figure AI / Boston Dynamics / Agility Robotics
- 국내 자율작업 로봇 기업
- Robotics Foundation Model
- ISO/IEC 기반 로봇 검증 표준
- 국내외 공용 로봇 테스트베드
- NPU 및 양자화 기반 On-device AI
- 레인보우로보틱스
- 두산로보틱스

Skill OFF보다 기업, 검증 표준, 시험 인프라 및 On-device AI 관련 조사 주제가 세분화되는 경향이 나타났다.

그러나 Turn 3 모델 응답 생성 과정에서 Ollama API가 300초를 초과하여 ReadTimeout이 발생하였다.

따라서 Skill에서 요구하는 다음 동작의 실제 수행 여부는 아직 판정할 수 없다.

- 실제 원문 fetch
- Source tier 적용
- 2개 독립 출처 triangulation
- single-source 표시
- Counter-evidence 탐색
- Gap 추적
- convergence 판단
- 고정된 최종 보고서 형식
- Markdown footnote citation

---

## 6. 현재 판정

### 확인된 사항

1. 공개 deep-research SKILL.md를 자체 Skill Loader에서 발견하고 활성화할 수 있다.
2. Gemma4가 Skill 활성화 상태에서도 정상적으로 Tool Calling을 수행한다.
3. Skill ON에서 조사 query가 보다 세분화되는 행동 변화가 관찰되었다.
4. Web Search Tool 자체에서는 오류가 발생하지 않았다.

### 아직 확인되지 않은 사항

1. Skill ON이 실제 페이지 원문 읽기를 증가시키는지
2. Source tier에 따라 출처를 선별하는지
3. 중요 주장을 복수 독립 출처로 교차검증하는지
4. Counter-evidence 및 Gap을 관리하는지
5. Skill에서 정의한 최종 보고서 구조와 citation 규칙을 준수하는지

### 현재 실패 원인

현재 Skill ON 실패는 Skill 발견 또는 Tool Calling 실패가 아니라 Gemma4 31B의 세 번째 모델 호출이 HTTP read timeout 300초를 초과한 Runtime 성능 문제이다.

따라서 Skill ON 실험을 재실행한 뒤 최종 비교를 수행해야 한다.

---

## 7. 다음 조치

1. 중복된 deep-research Skill 설치 경로 정리
2. Skill discovery warning 제거
3. Ollama HTTP read timeout 조정
4. 동일 요청으로 Skill ON만 재실행
5. fetch_page 수행 여부 확인
6. 최종 Skill OFF vs ON 비교 수행
7. 이후 parallel sub-agent를 추가한 B2 시험 수행

현재 결과만으로는 "deep-research Skill이 최종 연구 품질을 개선하였다"고 결론 내리지 않는다.

현재까지 확인된 결론은 "Gemma4에서 공개 Agent Skill을 로드하고 Skill 지침에 따라 조사 행동 및 Tool Calling을 변화시키는 것이 가능하지만, 장시간 agentic workflow를 안정적으로 수행하기 위한 Runtime의 timeout/context 관리가 추가로 필요하다"이다.
