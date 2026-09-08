# B2 Semantic Auditor: 독립 Gemma4 Chat Session

Semantic Auditor는 다른 모델이 아니다.
Worker와 같이 **같은 `gemma4:31b`의 별도 독립 Context**다.

새 `messages[]`를 연다. Worker 대화, Coordinator 대화와 이어 붙이지 않는다.

상위: [b2-sub-agents.md](b2-sub-agents.md) · [b2-runtime-contracts.md](b2-runtime-contracts.md)  
검증 계약: [verification.md](../runtime/b2/verification.md)

---

## 구조

```text
Worker Gemma
    ↓
Claims + sources
    ↓
Deterministic Gate
    ↓
실제로 fetch된 것만 남김
    ↓
                ┌─────────────────────────────┐
                │ Semantic Auditor Gemma4     │
                │                             │
                │ SKILL.md                    │
                │ + verification.md           │
                │ + evidence-policy.md        │
                │ + actual fetched content    │
                └──────────────┬──────────────┘
                               ↓
                  Claim ↔ Source 판정
                               ↓
          VERIFIED / MISMATCH / INSUFFICIENT
```

앞단 Deterministic Gate는 URL이 이번 Worker 세션에서 실제로 fetch됐는지만 본다.
의미 판단은 하지 않는다.

Auditor는 Gate를 통과한 항목만 받는다.
검색만 된 URL, fetch 실패, UNREAD 출처는 이 Context에 넣지 않는다.

---

## 무엇을 읽고 무엇을 주지 않는가

| 넣는 것 | 넣지 않는 것 |
|---|---|
| 활성 `SKILL.md` | `web_search` / `fetch_page` Tool |
| `verification.md` | Worker 대화 전문 |
| `evidence-policy.md` | 새 URL을 찾아 올 권한 |
| 실제로 fetch된 본문 | 모델 기억으로 claim을 보강할 여지 |

Tool을 주지 않는 이유: 검증 Agent가 새 근거를 찾아 기존 Claim을 살려 버리면 안 된다.

---

## 역할

Auditor의 질문은 하나다.

> 주어진 Evidence가 맞냐?

즉 이미 읽힌 본문이 그 claim을 실제로 지지하는지, 문서가 인용과 같은 자료인지,
출처 등급을 Skill tier 규칙으로 다시 볼지만 판단한다.

하지 않는 것:

- 웹을 다시 검색하지 않는다
- 새 URL·인용·수치를 만들지 않는다
- URL이 맞다는 이유만으로 `VERIFIED`로 올리지 않는다
- 약한 claim을 일반 지식으로 고치지 않는다
- 최종 사용자 보고서를 쓰지 않는다

판정 예:

- `VERIFIED` — 읽은 본문이 claim을 실질적으로 지지함
- `CONTENT_MISMATCH` — fetch는 됐지만 기대한 자료가 아님
- `INSUFFICIENT_SUPPORT` — 자료는 맞지만 본문이 claim을 충분히 지지하지 않음

claim 단위 verdict(`TRIANGULATED`, `SINGLE_SOURCE`, `UNSUPPORTED`, `CONFLICTING`)와
출력 JSON은 [verification.md](../runtime/b2/verification.md)의 Semantic audit output을 따른다.

---

## 독립 Context인 이유

Auditor Session에는 **이미 회수된 본문과 검증 계약만** 있다.

Worker가 무엇을 검색했는지, Coordinator가 어떤 assignment를 줬는지는
Audit packet으로 압축된 범위 안에서만 보인다.

그래서 Auditor는 “이 claim을 살리려면 무엇을 더 찾을까”가 아니라
“지금 놓인 페이지가 이 문장을 받치느냐”만 답한다.
