# B2 Sub-agent: 독립 Gemma4 Chat Session

Deep Research B2의 Sub-agent는 별도 모델이 아니다.
같은 `gemma4:31b`를 **같은 Ollama endpoint**에
서로 다른 request / `messages[]`로 동시에 호출하는 독립 Chat Session이다.

새 모델 3개를 만들지 않는다.
`gemma4:31b` 하나다.

상위: [b2-runtime-contracts.md](b2-runtime-contracts.md)  
동시 실행·overlap 로그: [b2-parallel-workers.md](b2-parallel-workers.md)

---

## Parallel Sub-agents

```text
              Coordinator Gemma4
                     │
                  plan.json
                     │
          ┌──────────┼──────────┐
          │          │          │
         SG01       SG02       SG03
          │          │          │
          ▼          ▼          ▼
      Gemma4      Gemma4      Gemma4
      Worker 1    Worker 2    Worker 3
      context A   context B   context C
          │          │          │
      Search/Fetch Search/Fetch Search/Fetch
          │          │          │
          └──────────┼──────────┘
                     ▼
                Worker Results
```

- **Coordinator**: 요청을 sub-goal로 나누고 `plan.json`만 만든다. 대량 검색·원문 읽기는 하지 않는다.
- **Worker**: `plan["assignments"]`의 자기 항목만 조사한다. 각자 새 `messages[]`에서 Search/Fetch를 한 뒤 JSON만 돌려준다.
- Coordinator는 Worker 대화 원문이 아니라 그 JSON(및 compact evidence)만 이어받는다.

`SG01` / `SG02` / `SG03`은 계획에 나온 id다.
Python이 그 내용을 주제별로 다시 쓰지 않는다.
Wave당 Worker 수는 Runtime의 `max_workers`를 따른다.

같은 Ollama endpoint에 독립 request 3개를 동시에 보낸다.
모델 파일이나 서버를 Worker마다 새로 띄우지 않는다.

---

## 왜 같은 모델인가

Sub-agent는 다른 가중치나 별도 Ollama 서버가 아니다.

| 구분 | 내용 |
|---|---|
| 모델 | `gemma4:31b` 하나 |
| 호출 | 같은 Ollama endpoint에 독립 request/session을 동시에 |
| 차이 | **Chat Session / messages[]** |
| 공유하지 않는 것 | Worker 사이의 Context, 도구 결과, thinking |
| 다시 모으는 곳 | Coordinator가 Worker JSON만 집계 |

A의 검색 결과가 B의 prompt에 자동으로 섞이지 않는다.
그래서 같은 주제를 병렬로 나눠도 Context가 한곳으로 몰리지 않는다.

---

## Session이 갈라지는 지점

1. Coordinator가 Assignment JSON을 만든다. (`SG01`, objective, queries, source_priority 등)
2. Runtime이 Worker마다 **빈 messages[]**를 연다.
3. 그 Session에는 Worker 계약(`worker.md`)과 **해당 Assignment만** 넣는다.
4. Worker는 자기 도구 호출을 자기 messages에만 쌓는다.
5. 끝나면 claims / gaps / leads JSON을 반환하고 Session은 닫는다.
6. Coordinator Session은 그 요약만 받아 다음 Wave 또는 합성을 판단한다.

Coordinator messages[]와 Worker messages[]는 하나로 이어 붙이지 않는다.

---

## 독립 Context가 하는 일

- Worker A가 읽은 페이지가 Worker B의 prompt를 키우지 않는다.
- 한 Worker가 실패해도 다른 Worker Session은 그대로다.
- 최종 합성은 Worker 대화 전문이 아니라 Evidence Pack만 본다.  
  ([synthesis.md](../runtime/b2/synthesis.md))

B1은 단일 Gemma4가 검색 결과를 한 Context에 계속 쌓았다.
B2는 조사를 Session으로 쪼개서 그 누적을 줄이는 쪽에 가깝다.

---

## 하지 않는 것

- 새 모델 3개를 만들거나, Worker마다 다른 Ollama 서버를 띄우는 것이 아니다.
- Worker가 Coordinator의 전체 대화 이력을 물려받지 않는다.
- Worker가 최종 사용자 보고서를 쓰지 않는다.
- 검색 snippet을 Worker 사이에서 검증된 근거처럼 공유하지 않는다.

계약 쪽 규칙: [controller.md](../runtime/b2/controller.md), [worker.md](../runtime/b2/worker.md)

Worker JSON 이후의 의미 검증은 별도 Session이다: [b2-semantic-auditor.md](b2-semantic-auditor.md)
계획만 만드는 Coordinator Session: [b2-coordinator.md](b2-coordinator.md)
