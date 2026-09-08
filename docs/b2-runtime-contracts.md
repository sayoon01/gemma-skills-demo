# B2 Runtime 계약 역할 구분

Deep Research B2에서 **연구 방법**과 **Runtime 실행 계약**을 분리한다.
Python은 Deep Research 절차 자체를 하드코딩하지 않고, 아래 파일을 읽어 적용한다.

원본 계약: `runtime/b2/`
로더: `src/research_b2/contracts.py`

---

## 한눈에 보기

| 파일 | 역할 |
|---|---|
| 활성 `SKILL.md` | Deep Research가 **어떻게 동작해야 하는지** (연구 행동의 1차 출처) |
| [controller.md](../runtime/b2/controller.md) | Runtime에서 **Controller** 역할을 어떻게 수행할지 |
| [worker.md](../runtime/b2/worker.md) | Worker에게 줄 **실행 계약** |
| [evidence-policy.md](../runtime/b2/evidence-policy.md) | **Evidence integrity**를 Runtime에서 어떻게 보장할지 |
| [verification.md](../runtime/b2/verification.md) | Worker 출력을 Evidence Pack에 넣기 전 **검증 상태**를 어떻게 붙일지 |
| [replan.md](../runtime/b2/replan.md) | 다음 Wave의 **입력·재계획 계약** |
| [convergence.md](../runtime/b2/convergence.md) | Skill convergence와 **resource cap**을 어떻게 기록할지 |
| [synthesis.md](../runtime/b2/synthesis.md) | 최종 작성 시 **Evidence Pack 경계** |

활성 Skill은 Controller가 대체하거나 무시하지 않는다.
Controller/Worker 계약은 Skill을 실행하는 방법만 정의한다.

---

## SKILL.md

Deep Research가 **어떻게 동작해야 하는지**를 정의한다.

- 조사 절차, 출처 우선순위, triangulation, 보고서 구조
- 도메인(Physical AI, 로봇 규격 등)에 종속되지 않은 연구 지침
- Runtime이 다시 짜는 로직이 아니라, 모델이 따라야 할 **1차 행동 규범**

Controller는 활성 `SKILL.md`를 기본 연구 행동으로 삼고, 그 위에 Runtime 계약만 얹는다.

---

## controller.md

우리 Runtime에서 **Controller 역할**을 어떻게 수행할지 정의한다.

- 요청 이해, Skill 준수, 독립 sub-goal 분해, Worker 배정
- Worker가 돌려준 compact evidence 검토
- 근거 부족·충돌·단일 출처에 대한 추가 배정, Wave 필요 여부 판단
- 최종 합성은 검증된 Evidence Pack만 사용

경계: Controller는 대량 웹 페이지를 직접 읽지 않는다. 검색·원문 읽기는 Worker에 위임한다.

---

## worker.md

각 Gemma4 Sub-agent에게 줄 **실행 계약**이다.

- 할당받은 한 개 assignment만 조사한다. 최종 사용자 보고서 전체를 쓰지 않는다.
- 검색 snippet은 발견용이다. 중요 주장은 실제 원문을 읽은 뒤에만 근거가 된다.
- 로컬 문서는 실제 페이지·범위를 읽고 경로·페이지를 남긴다.
- 출처 품질은 Skill과 assignment의 source priority를 따른다. 검색 순위만으로 낮은 tier를 쓰지 않는다.
- 교차검증, 반대 근거, 단일본 출처·충돌은 숨기지 않는다.

출력은 JSON 계약(claims / gaps / leads)만 반환한다.

---

## evidence-policy.md

**Evidence integrity**를 Runtime에서 어떻게 보장할지 정의한다. 연구 주제와 무관하다.

출처 후보는 `DISCOVERED` / `VERIFIED` / `REJECTED` / `CONFLICTING`으로만 취급한다.

- `DISCOVERED`(검색만 됨)는 최종 인용 불가
- `VERIFIED`(실제로 읽고 관련 구절을 추출함)만 최종 인용 가능
- material claim은 가능하면 독립된 VERIFIED 출처 2개
- 하나면 single-source, 없으면 findings에서 제외하거나 근거 부족으로 표시
- 검색 snippet은 최종 증거가 될 수 없다
- 최종 합성은 Evidence Pack에 없는 URL·출처를 새로 넣지 못한다

---

## replan.md

Wave 이후 **다음 Wave 입력 계약**이다.

입력이 되는 compact summary:

- 완료된 sub-goal, validated claims, source counts/tiers
- single-source / unsupported / conflicting claims
- worker gaps, leads

전체 조사를 다시 시작하지 않는다. 남은 gap을 닫는 **표적 assignment**만 만든다.
추가 Wave가 필요 없으면 `needs_another_wave: false`와 빈 assignments를 반환한다.

---

## convergence.md

**Skill convergence**와 **resource cap**을 어떻게 기록할지 분리한다.

- converged로 기록하는 조건은 활성 Skill의 convergence 조건이 충족될 때만
- 현재 deep-research 기준 예: 읽은 고유 출처 10개 이상, 최근 연속 2 wave의 novel claim 비율이 각각 15% 미만
- timeout, 모델/도구 오류, max_waves, 비용·시간 한도는 convergence가 아니다
- max_waves에 먼저 닿으면 `stop_reason = "resource_cap"` (convergence로 기록하지 않음)

Runtime은 실제 종료 이유와 출처·claim·novelty 수치를 남긴다.

---

## synthesis.md

최종 작성 시 **Evidence Pack 경계**를 정의한다.

- 검증된 Evidence Pack만으로 보고서를 쓴다
- 합성 단계에서 새 조사를 하지 않는다
- Pack에 없는 URL, 출판사, 페이지, 제목, 날짜, tier를 만들지 않는다
- triangulated / single-source / unsupported / conflicting을 구분한다
- search-only 출처는 Sources에 넣지 않는다
- Worker 대화 원문이나 웹페이지 원문 전체를 다시 읽지 않고, compact Evidence Pack을 쓴다

---

## 로딩

`src/research_b2/contracts.py`의 `load_b2_contracts()`가 위 6개 Markdown을 읽어 문자열로 제공한다.
Deep Research 절차 본문은 Skill 쪽에 남기고, 이 Loader는 계약 파일만 연다.
