# B2 Sequential Recovery

Parallel Worker batch에서 실패한 assignment만 골라, 같은 assignment를 독립 Worker context로 한 번씩 순차 재실행한다.

이미 성공한 Worker는 다시 돌리지 않는다.
연구 주제나 Skill workflow를 이 모듈에 하드코딩하지 않는다.

코드: [recovery.py](../src/research_b2/recovery.py)  
상위: [b2-parallel-workers.md](b2-parallel-workers.md) · [b2-e2e.md](b2-e2e.md)

---

## 흐름

```text
parallel-result.json
      ↓
status != completed 인 Worker만
      ↓
원본 plan.json assignment 복원
      ↓
run_worker() 순차 재실행
      ↓
recovery/<assignment_id>/run-*/
recovery/recovery-index.json
```

대표적인 실패:

```text
ReadTimeout
```

---

## Local files

실패한 assignment에 `needs_local_files=true`가 있으면 Recovery에도 `--input-dir`가 필요하다.
없으면 capability mismatch로 중단한다.

---

## CLI

```bash
python3 -m src.research_b2.recovery \
  --batch outputs/research-b2/.../run-* \
  --skill deep-research \
  --input-dir inputs
```

실패 Worker가 없어도 빈 `recovery-index.json`을 만들어 Evidence Pool이 안전하게 읽을 수 있게 한다.

---

## 이 단계가 하지 않는 것

- 성공 Worker를 재실행하지 않는다
- assignment 내용을 바꾸거나 새 plan을 만들지 않는다
- timeout 원인을 Skill 규칙으로 재해석하지 않는다
