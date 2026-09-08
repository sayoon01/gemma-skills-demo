# B2 Replanner: Wave 이후의 표적 재계획

Replanner는 다음 Wave를 조사하지 않는다.
Wave 1 Evidence Pool과 측정값을 활성 `SKILL.md`에 넘기고,
Gemma가 추가 조사가 필요한지만 판단하게 한다.

Python은 무엇을 더 찾을지 정하지 않는다.
Deep Research 중단 규칙을 Runtime Markdown에 복사하지도 않는다.

상위: [b2-evidence-pool.md](b2-evidence-pool.md) · [b2-coordinator.md](b2-coordinator.md)  
코드: [src/research_b2/replanner.py](../src/research_b2/replanner.py)  
계약: [replan.md](../runtime/b2/replan.md) · [convergence.md](../runtime/b2/convergence.md)

---

## 구조

```text
Wave 1 Evidence
      ↓
Public SKILL.md
      ↓
Gemma Replanner
      ↓
invalid structured plan
      ↓
Generic Validator
      ↓
schema errors
      ↓
Gemma Repair
      ↓
valid structured plan
```

첫 Coordinator는 사용자 요청만 보고 `plan.json`을 만든다.
Replanner는 그 다음이다. 이미 읽은 Evidence와 Runtime 측정값만 본다.

---

## 무엇을 넘기는가

Gemma에게 주는 것은 세 가지다.

- 활성 public `SKILL.md`. 추가 Wave 여부와 표적 gap은 여기가 정한다.
- `replan.md`. 다음 Wave 입력의 JSON 형식만 정한다.
- `convergence.md`. 측정값을 기록하는 방법만 정한다. 10개 출처, 15% novelty 같은 Skill 규칙은 넣지 않는다.

같이 넘기는 compact packet:

- 읽은 고유 URL 수, verified source 수, claim 수
- `SINGLE_SOURCE`, `UNSUPPORTED`, `CONFLICTING`, `MULTI_SOURCE_PENDING_INDEPENDENCE`
- unresolved gap
- claim에는 `claim_ref` (`SG01:C001`)가 이미 붙어 있다

이 값들은 관찰이다. Skill이 그렇게 말하지 않으면 수렴 규칙이 아니다.

---

## Validator와 Repair

Replanner의 성공은 “말이 되는 조사 계획”이 아니다.
`replan.md`가 요구하는 structured plan이 나오는 것이다.

Generic Validator는 연구 내용을 고치지 않는다. schema만 본다.

허용 필드는 이것뿐이다.

- top-level: `needs_another_wave`, `reason`, `assignments`
- assignment: `assignment_id`, `title`, `objective`, `queries`, `source_priority`, `needs_local_files`

그래서 `queries_ko`, `source_priority_ko`, 깨진 키 이름은 invalid다.
`queries`와 `source_priority`는 비어 있지 않은 문자열 list여야 한다.
기존 `SG01` 같은 assignment id를 다시 쓰면 invalid다.

invalid면 Gemma Repair가 최대 2번 돈다.

- thinking은 끈다
- 응답은 JSON만 받는다
- 이전 계획의 조사 의도와 표적 gap은 유지한다
- 없는 필드만 지우고, 잘린 assignment만 형식을 맞춘다
- 새 검색, 새 URL, 새 근거를 만들지 않는다

최종 `replan.json`은 repair 이후의 plan이다.
처음 깨진 출력은 `replan-initial.json`에 남긴다.

---

## 이 단계가 하지 않는 것

- Wave 1 조사를 처음부터 다시 하지 않는다
- Skill의 convergence 문장을 Runtime에 복제하지 않는다
- `max_waves`에 닿은 것을 semantic convergence로 기록하지 않는다
- Validator가 주제 문장을 대신 쓰지 않는다
- Repair가 Evidence Pool 밖에 URL을 추가하지 않는다
- Wave 2 claim이 이전 claim과 같은 사실인지는 여기서 정하지 않는다. 그건 [b2-claim-merge.md](b2-claim-merge.md)다
