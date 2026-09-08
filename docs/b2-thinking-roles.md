# B2 Gemma4 역할별 thinking

같은 `gemma4:31b`, 같은 Ollama endpoint다.
역할마다 다른 것은 가중치가 아니라 Chat Session과 thinking 사용이다.

조사와 계획에는 thinking을 켜고, 이미 읽은 Evidence를 JSON으로 판정할 때는 끈다.
Runtime Gate는 모델이 아니다. thinking도 도구도 없다.

상위: [b2-sub-agents.md](b2-sub-agents.md) · [b2-semantic-auditor.md](b2-semantic-auditor.md) · [b2-evidence-pool.md](b2-evidence-pool.md)

---

## 역할

```text
Coordinator Gemma4
├─ thinking ON
└─ 연구 계획 판단

Worker Gemma4
├─ thinking ON
├─ Search
├─ Fetch
└─ Claims 생성

Semantic Auditor Gemma4
├─ thinking OFF
├─ Tool 없음
├─ 새 조사 없음
└─ 기존 Evidence → JSON 판정

Runtime Gates
└─ deterministic consistency
```

---

## Coordinator

thinking을 켠다.

하는 일: 요청을 읽고 sub-goal로 나누며, `plan.json`만 만든다.
대량 검색이나 원문 읽기는 하지 않는다.

하지 않는 것: Worker 대화 전문을 이어받지 않는다. 웹 페이지를 대신 읽지 않는다.

---

## Worker

thinking을 켠다.

하는 일: 자기 assignment만 Search하고, 후보 페이지를 Fetch한 뒤 Claims JSON을 만든다.
제목이나 snippet만으로는 근거가 되지 않는다. 이 세션에서 읽은 URL만 인용한다.

하지 않는 것: 전체 사용자 보고서를 쓰지 않는다. 다른 Worker 항목을 대신 조사하지 않는다.

---

## Semantic Auditor

thinking을 끈다.
`web_search` / `fetch_page`를 주지 않는다.
새 조사를 하지 않는다.

하는 일: Deterministic Gate를 통과한 claim과, 이미 fetch된 본문만 보고 JSON으로 판정한다.
질문은 하나다. 놓인 Evidence가 그 claim을 실제로 지지하는가.

세 Worker를 동시에 돌리지 않는다. 한 assignment의 packet을 끝낸 뒤 다음으로 간다.
각 호출은 그 packet만 보는 독립 `messages[]`다.

최종 응답은 content의 JSON이다. thinking 필드에만 답을 넣으면 실패다.

---

## Runtime Gates

모델 호출이 아니다. deterministic consistency만 본다.

- Deterministic Gate: 인용 URL이 그 Worker 세션에서 실제로 fetch됐는지
- Post-Audit Gate: Auditor verdict를 그대로 믿지 않고, `VERIFIED` 개수를 다시 셈

Gate는 새 URL을 만들지 않고, 빈 결과를 다른 Worker 자료로 메우지 않는다.
통과한 claim만 unique URL Evidence Pool로 간다.

---

## 현재 연결

| 역할 | thinking | 코드 |
|---|---|---|
| Semantic Auditor | OFF (`think=False`, `format=json`) | `src/research_b2/auditor.py`에 연결됨 |
| Coordinator | ON으로 둔다 | `client.chat()`에 `think`를 아직 넘기지 않음 |
| Worker | ON으로 둔다 | `client.chat()`에 `think`를 아직 넘기지 않음 |
| Runtime Gates | 해당 없음 | `evidence_gate.py`, `audit_gate.py` |
