# B2 Deterministic Evidence Gate

Worker가 말한 내용을 그대로 Evidence로 쓰지 않는다.
실제로 읽은 Web page / PDF page 기록이 있을 때만 Gate를 통과한다.

코드: [evidence_gate.py](../src/research_b2/evidence_gate.py)  
계약: [verification.md](../runtime/b2/verification.md) · [evidence-policy.md](../runtime/b2/evidence-policy.md)  
관련: [b2-local-files.md](b2-local-files.md) · [b2-semantic-auditor.md](b2-semantic-auditor.md)

---

## Web

```text
Worker claim
  ↓
worker source URL
  ↓
실제 fetch_page 성공 여부
  ↓
retrieved source
  ↓
Deterministic Gate
```

`web_search` snippet만으로는 Evidence가 되지 않는다.

---

## PDF

```text
Worker claim
  ↓
file path + page
  ↓
실제 read_pdf_pages 기록
  ↓
file SHA-256 확인
  ↓
exact page 확인
  ↓
Deterministic Gate
```

`search_pdf_text`는 후보 page discovery용이다.
Evidence로 인정하려면 반드시 `read_pdf_pages` 실행 기록이 있어야 한다.

통과 예:

```text
source_kind=file
path=inputs/로봇 제품 규격.pdf
page=2
sha256=...
verification_state=READ
```

거절 예:

```text
UNREAD
INVALID_FILE_CITATION
FILE_VERSION_MISMATCH
```

---

## 역할 분리

```text
검색 / 읽기 → Worker
기계적 원문 확인 → Deterministic Gate
의미 판정 → Semantic Auditor
```

Gate는 claim 진위를 의미적으로 판단하지 않는다.
읽었는지, 어떤 URL/path/page인지, SHA가 맞는지 같은 기계적 조건만 본다.
