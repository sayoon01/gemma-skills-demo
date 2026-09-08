# B2 Coordinator: 조사 계획만 만드는 독립 Gemma4 Session

Coordinator는 Worker를 대신해 웹을 조사하지 않는다.
같은 `gemma4:31b`의 **별도 Chat Session**으로, 사용자 요청을
병렬 Assignment로 나누기만 한다.

이 단계의 성공 기준은 Worker 실행이 아니라 **계획 JSON이 나온다**는 것이다.
다음 단계(B2-3)에서 그 계획을 실제 Worker에 넘긴다.

상위: [b2-sub-agents.md](b2-sub-agents.md) · [b2-runtime-contracts.md](b2-runtime-contracts.md)  
코드: [src/research_b2/coordinator.py](../src/research_b2/coordinator.py)  
계약: [controller.md](../runtime/b2/controller.md)

---

## 구조

```text
사용자 예제 A 전체 요청
        +
public deep-research SKILL.md
        +
controller.md
        ↓
Gemma4 Coordinator
        ↓
[
  SG01,
  SG02,
  SG03
]
```

예제 A는 고정 주제가 아니다.
`tasks/physical-ai-research.md`든 `tasks/robot-spec-research.md`든,
Runtime은 **요청 파일 전체**를 그대로 넘긴다.

---

## Python이 하지 않는 것

`SG01` / `SG02` / `SG03`의 제목, 질문, 검색어를
Python에서 Physical AI나 로봇 규격으로 하드코딩하지 않는다.

Python이 하는 일은 다음뿐이다.

- 활성 `SKILL.md` 읽기
- `controller.md` 읽기
- 사용자 요청 전달
- Gemma4 호출
- 계획 JSON 형식 검사
- 저장

Assignment 내용은 Gemma가 **SKILL.md와 사용자 요청을 읽고** 직접 만든다.
다른 예제를 넣으면 계획도 그 요청에 맞게 바뀌어야 한다.

---

## 이 Session에 넣는 것 / 넣지 않는 것

| 넣는 것 | 넣지 않는 것 |
|---|---|
| 활성 `SKILL.md` | `web_search` / `fetch_page` |
| `controller.md` | Worker 대화 |
| 사용자 요청 전문 | 미리 쓴 sub-goal 목록 |
| 이번 wave 최대 Assignment 수 | 출처 URL, 사실, 수치 |

계획 응답은 조사가 아니다.
출처를 만들지 않고, 발견 결과를 쓰지 않는다.

출력 형식은 `controller.md`의 planning JSON이다.
`assignment_id`, `title`, `objective`, `queries`, `source_priority`,
`needs_local_files`를 가진다.
개수는 Runtime의 `max_workers`를 넘지 않는다.

---

## B2-3으로 넘어가는 지점

Coordinator가 유효한 계획을 내면, 그다음이 진짜 B2-3이다.

```text
Coordinator plan
    ↓
SG01 → Worker A (새 messages[])
SG02 → Worker B (새 messages[])
SG03 → Worker C (새 messages[])
```

각 Worker는 자기 Assignment만 받는다.
Coordinator가 적어 둔 문장을 Worker가 그대로 조사 범위로 쓴다.
Python이 그 문장을 주제별로 다시 쓰지 않는다.
그다음 동시 실행과 overlap 로그는 [b2-parallel-workers.md](b2-parallel-workers.md)에 둔다.
