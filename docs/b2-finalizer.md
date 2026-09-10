# B2 Independence Finalizer

Challenge에서 이미 결정된 family verdict를 cumulative state에 deterministic하게 적용한다.
이 단계는 LLM을 호출하지 않는다.

코드: [finalizer.py](../src/research_b2/finalizer.py)  
상위: [b2-source-independence.md](b2-source-independence.md) · [b2-e2e.md](b2-e2e.md)

---

## 입력

```text
cumulative state
source independence result
independence challenge result
```

세 입력의 validation이 `ok`이고 family 집합이 일치해야 한다.

---

## 상태 전이

| Challenge verdict | resolved status |
|---|---|
| `TRIANGULATED` | `TRIANGULATED` |
| `NOT_TRIANGULATED` | `SINGLE_SOURCE` |
| `UNKNOWN` | `MULTI_SOURCE_PENDING_INDEPENDENCE` |

핵심:

```text
family의 모든 claim을 바꾸지 않는다.
Source Independence가 지정한 claim_status_updates만 전이한다.
```

---

## 이 단계가 하지 않는 것

- provenance나 claim 의미를 다시 판단하지 않는다
- Challenge verdict를 Python이 뒤집지 않는다
- 최종 사용자 보고서를 쓰지 않는다
