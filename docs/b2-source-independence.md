# B2 Source Independence: 같은 사실의 출처 독립성

Independence Auditor는 이미 검증된 Evidence만 보고, 같은 사실 family를 받치는 출처가 서로 독립인지 판정한다.

URL이 두 개라는 이유만으로 triangulated가 되지 않는다.
독립 여부는 Gemma가 정한다. Python은 family와 pair를 만들고 schema만 검사한다.

상위: [b2-claim-merge.md](b2-claim-merge.md) · [b2-evidence-pool.md](b2-evidence-pool.md)  
코드: [source_independence.py](../src/research_b2/source_independence.py)  
계약: [source-independence.md](../runtime/b2/source-independence.md) · [evidence-policy.md](../runtime/b2/evidence-policy.md)

---

## 구조

```text
Cumulative State
      ↓
SAME claim family
      ↓
VERIFIED evidence, canonical URL 중복 제거
      ↓
모든 source pair
      ↓
Gemma Independence Auditor   (thinking OFF, 도구 없음)
      ↓
Generic schema repair
```

대상은 `MULTI_SOURCE_PENDING_INDEPENDENCE` claim이 속한 SAME family다.
`CONTRADICTS` claim은 한 supporting family로 합치지 않는다.

---

## Python이 하는 일

- SAME relation으로 claim family를 묶는다
- family 안의 `VERIFIED` evidence만 모은다
- 같은 canonical URL은 한 source로 접는다
- 서로 다른 source의 pair를 모두 만든다
- 활성 Skill, evidence policy, independence 계약을 Gemma에 넘긴다
- family ref, claim ref, source ref, pair 완전성을 검사한다
- invalid면 generic repair를 최대 2번 돌린다

pair 관계 `INDEPENDENT` / `DEPENDENT` / `UNKNOWN`은 Gemma가 고른다.
family verdict `TRIANGULATED` / `NOT_TRIANGULATED` / `UNKNOWN`도 Gemma가 고른다.

publisher 이름이나 domain이 다르다는 것만으로 `INDEPENDENT`를 쓰지 않는다.
별도 provenance가 패킷에서 확인되지 않으면 `UNKNOWN`이다.
그 기준은 [source-independence.md](../runtime/b2/source-independence.md)의 provenance sufficiency rule에 있다.

---

## Adversarial Challenge

초기 Independence Audit 이후 별도 session이 previous INDEPENDENT 판단을 다시 공격한다.

```text
Source Independence Audit
      ↓
Adversarial Challenge
      ↓
Finalizer (deterministic state update)
```

코드: [independence_challenge.py](../src/research_b2/independence_challenge.py) · [finalizer.py](../src/research_b2/finalizer.py)  
계약: [independence-challenge.md](../runtime/b2/independence-challenge.md)  
문서: [b2-finalizer.md](b2-finalizer.md)

---

## 상태를 어디에 붙이는가

Finalizer가 Challenge verdict를 pending claim에만 붙인다.

| family verdict | resolved status |
|---|---|
| `TRIANGULATED` | `TRIANGULATED` |
| `NOT_TRIANGULATED` | `SINGLE_SOURCE` |
| `UNKNOWN` | `MULTI_SOURCE_PENDING_INDEPENDENCE` |

이 매핑은 verdict 이름을 그대로 옮기는 것이다.
Python이 출처를 다시 읽어 독립성을 뒤집지 않는다.

---

## 이 단계가 하지 않는 것

- 새 검색, 새 fetch, 새 URL을 만들지 않는다
- URL 개수나 domain 개수로 독립성을 세지 않는다
- 출처 품질 tier를 독립성이라는 이유로 올리지 않는다
- factual contradiction을 여기서 해소하지 않는다
- 최종 사용자 보고서를 쓰지 않는다. 합성은 [b2-synthesis.md](b2-synthesis.md)다
