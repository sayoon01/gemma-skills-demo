# B2-4 Sub-agent 병렬 실행

Coordinator가 만든 `plan.json`의 Assignment를 그대로 읽어,
Worker를 **동시에** 돌리는 단계다.

Assignment 문장은 Python이 만들지 않는다.
`assignments = plan["assignments"]`를 읽어 각 항목마다 `run_worker()`를 호출한다.

상위: [b2-coordinator.md](b2-coordinator.md) · [b2-sub-agents.md](b2-sub-agents.md)

---

## 구조

```text
plan.json
   │
   ├─ SG01
   │    ↓
   │  run_worker()
   │  독립 messages[]
   │
   ├─ SG02
   │    ↓
   │  run_worker()
   │  독립 messages[]
   │
   └─ SG03
        ↓
      run_worker()
      독립 messages[]

      ▲ 동시에 실행 ▲

ThreadPoolExecutor(max_workers=3)
```

`SG01` / `SG02` / `SG03`은 예시 이름이다.
계획에 있는 id와 본문을 그대로 쓴다.
Physical AI나 로봇 규격으로 Worker 입력을 다시 쓰지 않는다.

각 Worker는 새 `messages[]`다.
다른 Worker의 검색 결과나 대화가 섞이지 않는다.

---

## Worker가 하는 일

Worker는 전체 보고서를 쓰지 않는다.
`plan["assignments"]`의 자기 항목 하나만 조사하고, 최종 JSON만 돌려준다.

각 Worker는 자기 항목만 이렇게 한다.

1. 검색으로 후보 출처를 찾는다. 제목이나 요약만으로는 근거가 되지 않는다.
2. 실제로 페이지를 읽는다.
3. 그 문장이 주장을 뒷받침하거나 반박하는지만 적는다.
4. 이 세션에서 읽은 URL만 인용해서 최종 JSON을 낸다.

요청이 한국어이면 claim, gap, 설명은 한국어로 쓴다.
출처 제목과 URL, 고유명사는 원문을 유지한다. 기준은 [worker.md](../runtime/b2/worker.md)다.

최종 JSON은 `assignment_id`, `claims`, `gaps`, `leads`만 담는다.
검색 결과에만 나온 URL, 읽지 않은 페이지, 다른 Worker 항목은 근거로 넣지 않는다.
사용자용 완성 보고서는 Coordinator 이후 단계의 일이다.

---

## 병렬이라고 말하려면

`ThreadPoolExecutor`를 썼다는 것만으로는 충분하지 않다.
Python thread를 띄웠어도 모델 호출이 차례로만 끝나면 병렬이 아니다.

그래서 Worker마다 시간을 남긴다.

- `worker_started_at`
- `worker_finished_at`
- 모델 요청 start / end
- `duration`

그 구간으로 다음을 계산한다.

```text
SG01 실행 중
SG02 실행 중
SG03 실행 중
        └── 실제로 겹치는가
```

겹치는 구간이 로그에 있어야 “동시에 조사했다”고 기록한다.
겹치지 않으면 병렬 실행을 주장하지 않고, 순차 실행으로 남긴다.

---

## 이 단계가 하지 않는 것

- Assignment 내용을 코드에 고정하지 않는다
- Worker끼리 Context를 공유하지 않는다
- Coordinator가 웹 페이지를 대신 읽지 않는다
- 시간 기록이 없으면 parallel로 판정하지 않는다
