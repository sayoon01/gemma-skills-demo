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
| [claim-merge.md](../runtime/b2/claim-merge.md) | Wave claim의 **의미 관계와 novelty** 출력 형식 |
| [source-independence.md](../runtime/b2/source-independence.md) | SAME family의 **출처 독립성** 판정 계약 |
| [independence-challenge.md](../runtime/b2/independence-challenge.md) | Independence 판정에 대한 **adversarial 재검토** 계약 |
| [synthesis.md](../runtime/b2/synthesis.md) | 최종 작성 시 **Evidence Pack 경계**와 출력 언어 |

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

사용자 요청이 한국어이면 claim, gap, 설명은 한국어로 쓴다.
출처 제목, 고유명사, 모델명, 표준명, URL, 인용 용어는 원문을 유지한다.

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

- 수렴 조건은 활성 `SKILL.md`가 정한다. 이 계약은 그 규칙을 복사하지 않는다
- Runtime은 wave 수, 읽은 출처 수, novel claim 수, unresolved gap 같은 측정값만 제공한다
- timeout, 모델/도구 오류, max_waves, 비용·시간 한도는 convergence가 아니다
- max_waves에 먼저 닿으면 `stop_reason = "resource_cap"` (convergence로 기록하지 않음)

Runtime은 실제 종료 이유와 측정값을 남긴다. 그 의미는 활성 Skill이 해석한다.

Claim Merge가 남기는 running novelty는 이 측정값이다.
관계 이름과 `is_novel` 기준은 [claim-merge.md](../runtime/b2/claim-merge.md)에 있고, Skill 숫자를 여기로 복사하지 않는다.

---

## claim-merge.md

최신 Wave의 검증된 claim을 이전 누적 claim과 비교하는 **의미 관계 계약**이다.

- 관계는 `SAME` / `EXTENDS` / `CONTRADICTS` / `NOVEL` 중 하나
- `is_novel`은 문장 차이가 아니라 새로운 factual finding인지
- `matched_prior_claim_refs`는 입력에 있는 prior claim만
- 새 조사, claim ID 생성·삭제·병합을 하지 않는다

설명: [b2-claim-merge.md](b2-claim-merge.md)

---

## source-independence.md

SAME claim family의 VERIFIED 출처가 서로 독립인지 보는 **provenance 계약**이다.

- pair 관계는 `INDEPENDENT` / `DEPENDENT` / `UNKNOWN`
- family verdict는 `TRIANGULATED` / `NOT_TRIANGULATED` / `UNKNOWN`
- domain이나 publisher 이름만으로 독립을 단정하지 않는다
- 공통 발표·보도자료의 별도 provenance가 없으면 `UNKNOWN`
- `CONTRADICTS`를 supporting family로 합치지 않는다

설명: [b2-source-independence.md](b2-source-independence.md)

`load_b2_contracts()`의 기본 묶음에는 넣지 않는다.
Matcher와 Independence Auditor가 자기 단계에서만 읽는다.

---

## synthesis.md

최종 작성 시 **Evidence Pack 경계**를 정의한다.

- 검증된 Evidence Pack만으로 보고서를 쓴다
- 합성 단계에서 새 조사를 하지 않는다
- Pack에 없는 URL, 출판사, 페이지, 제목, 날짜, tier를 만들지 않는다
- triangulated / single-source / unsupported / conflicting을 구분한다
- search-only 출처는 Sources에 넣지 않는다
- Worker 대화 원문이나 웹페이지 원문 전체를 다시 읽지 않고, compact Evidence Pack을 쓴다
- 다른 언어를 명시하지 않으면 최종 보고서는 한국어다
- 고유명사와 기술 식별자, citation URL은 원문 Evidence를 가리킨다

합성 모듈은 아직 없다. 이 파일은 작성 경계와 출력 언어만 정한다.

---

## 로딩

`src/research_b2/contracts.py`의 `load_b2_contracts()`가 Controller부터 synthesis까지의 기본 Markdown을 읽어 문자열로 제공한다.
`claim-merge.md`와 `source-independence.md`는 해당 단계 모듈이 직접 읽는다.
Deep Research 절차 본문은 Skill 쪽에 남기고, 이 Loader는 계약 파일만 연다.
