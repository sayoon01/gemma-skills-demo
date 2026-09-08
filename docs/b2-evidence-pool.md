# B2 Evidence Pool: 검증된 고유 URL 모음

Evidence Pool은 세 Worker가 이미 읽어 둔 자료만 모아, URL 기준으로 한 번씩만 남긴 출처 집합이다.

새 웹 조사는 하지 않는다.
검색을 다시 돌리거나, 읽지 않은 페이지를 새로 fetch하지 않는다.
대상은 `SG01` / `SG02` / `SG03`이 이번 배치에서 실제로 읽어 둔 자료뿐이다.

`SG01` / `SG02` / `SG03`은 이번 plan의 assignment id다.
Python이 주제 문장을 다시 쓰지 않는다.

상위: [b2-parallel-workers.md](b2-parallel-workers.md) · [b2-semantic-auditor.md](b2-semantic-auditor.md)  
검증 계약: [verification.md](../runtime/b2/verification.md) · [evidence-policy.md](../runtime/b2/evidence-policy.md)

---

## 구조

```text
SG01 result ─┐
SG02 result ─┼─→ Deterministic Gate
SG03 result ─┘
                    ↓
            Semantic Auditor
                    ↓
             Post-Audit Gate
                    ↓
            Validated Claims
                    ↓
        unique URL Evidence Pool
```

Worker는 동시에 조사할 수 있다.
이 단계의 Auditor는 세 결과를 **동시에 돌리지 않고 순차 실행**한다.

한 Worker의 claim과 이미 fetch된 본문을 끝내 판정한 뒤에 다음 Worker로 넘어간다.
Auditor끼리 context를 합치지 않는다.
각 호출은 그 Worker의 검증 packet만 보는 독립 `messages[]`다.

---

## 각 단계가 남기는 것

### Deterministic Gate

의미는 보지 않는다.
Worker가 인용한 URL이 그 Worker 세션에서 실제로 fetch됐는지, fetch가 성공했는지, 인용 URL과 읽은 URL이 같은지만 본다.

검색 snippet만 있는 URL, fetch 실패, UNREAD는 여기서 떨어진다.
Auditor에게 넘기지 않는다.

### Semantic Auditor

질문 하나다. 이미 읽힌 본문이 그 claim을 실제로 지지하는가.

`web_search` / `fetch_page`를 주지 않는다.
세 Worker를 한 Context에 모아 다시 조사하지 않는다.
판정은 [verification.md](../runtime/b2/verification.md)의 semantic audit JSON을 따른다.

### Post-Audit Gate

Auditor가 준 evidence state는 쓰되, claim verdict는 그대로 믿지 않는다.
Runtime이 `VERIFIED` 개수를 다시 센다.

- `VERIFIED` 0개 → 그 claim은 Pool에 들어가지 않는다
- `CONTENT_MISMATCH`, `INSUFFICIENT_SUPPORT`는 채택 출처가 아니다
- 출처 독립성과 최종 triangulation은 이 단계에서 확정하지 않는다

### Validated Claims

Gate를 통과한 claim만 남는다.
각 claim에는 채택된 출처 URL과, 어느 Worker assignment에서 왔는지가 붙어 있다.

### unique URL Evidence Pool

Validated Claims에 붙은 웹 URL을 **canonical URL 하나당 한 레코드**로 모은다.

같은 페이지를 `SG01`과 `SG02`가 각각 인용했어도 Pool에는 URL이 한 번만 있다.
그 레코드에 그 URL을 쓴 claim / assignment만 여럿 붙는다.

Pool에 들어가는 URL은 전부 이번 배치에서 누군가 실제로 읽은 페이지다.
Worker 결과 JSON에 적혀 있다는 이유만으로 넣지 않는다.

---

## Pool에 넣는 것 / 넣지 않는 것

| 넣는 것 | 넣지 않는 것 |
|---|---|
| 이번 Worker 세션에서 fetch 성공한 URL | 검색 결과 제목·snippet만 있는 URL |
| Post-Audit 이후 `VERIFIED`로 남은 출처 | UNREAD, fetch 실패 |
| claim에 연결된 excerpt·publisher·tier | `CONTENT_MISMATCH`, `INSUFFICIENT_SUPPORT` |
| 그 URL을 인용한 assignment / claim id | 모델 기억으로 보충한 URL·수치·인용 |
| 같은 URL의 중복을 접은 고유 목록 | 아직 읽지 않은 lead, gap용 후보 URL |

로컬 파일 도구는 이 배치에서 쓰지 않는다.
Pool의 웹 항목은 공개 페이지 URL만 대상으로 한다.

---

## 왜 고유 URL인가

Worker 결과에는 같은 글이 claim마다 반복될 수 있다.
그걸 그대로 이어 붙이면 출처 수가 부풀고, 서로 다른 출판사인지와 같은 페이지를 여러 번 센 것인지가 섞인다.

Evidence Pool은 그 중복을 URL에서 제거한 뒤의 출처 경계다.

이후 합성은 이 Pool 밖에 있는 URL을 새로 인용하지 못한다.
[synthesis.md](../runtime/b2/synthesis.md)의 Evidence Pack은 이 Pool을 넘지 않는다.
Pack에 없는 URL, 출판사, 제목, 날짜, tier를 합성 단계에서 만들지 않는다.

---

## 이 단계가 하지 않는 것

- 새 검색, 새 fetch, 새 URL 발굴을 하지 않는다
- 실패한 Worker의 빈 결과를 다른 Worker 자료로 메우지 않는다
- Auditor 세 개를 동시에 돌려 서로의 본문을 섞지 않는다
- 사용자용 최종 보고서를 쓰지 않는다
- lead를 보고 다음 Wave assignment를 만들지 않는다. 그건 [b2-replanner.md](b2-replanner.md)다
