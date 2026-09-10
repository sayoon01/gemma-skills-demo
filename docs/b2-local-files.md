# B2 Local Files / PDF Tools

`--input-dir`가 설정되면 Worker에 generic local-file tools가 추가된다.
파일명이나 도메인 주제를 Runtime에 하드코딩하지 않는다.

코드: [local_files.py](../src/research_b2/local_files.py) · [tools.py](../src/research_b2/tools.py)  
연결: [b2-parallel-workers.md](b2-parallel-workers.md) · [b2-evidence-gate.md](b2-evidence-gate.md)

---

## Tools

| Tool | 역할 |
|---|---|
| `list_local_files` | 입력 디렉터리 탐색 |
| `search_pdf_text` | PDF 내 후보 page discovery |
| `read_pdf_pages` | 실제 page 본문 읽기 |

접근 범위는 설정된 `input_dir` 안으로 제한한다.

---

## Evidence 규칙

```text
search_pdf_text  → 위치 찾기
read_pdf_pages   → Evidence 후보
```

같은 PDF의 여러 페이지를 읽어도 Evidence Pool / Independence에서는 SHA-256 우선으로 하나의 문서로 본다.
path fallback은 SHA가 없을 때만 쓴다.

---

## Runtime wiring

| 단계 | `input_dir` |
|---|---|
| Parallel Workers | CLI `--input-dir` |
| Sequential Recovery | 동일 scope 전달 |
| E2E Runner | `--input-dir` → Wave / Recovery |

plan에 `needs_local_files=true`인데 `input_dir`가 없으면 실행을 중단한다.

---

## 이 단계가 하지 않는 것

- PDF 존재만으로 primary-source 품질을 가정하지 않는다
- 제품명·파일명을 코드에 박아 두지 않는다
- 검색 hit만으로 citation을 허용하지 않는다
