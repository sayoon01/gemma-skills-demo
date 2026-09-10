# B2 E2E Runner

한 프로세스에서 Coordinator부터 Synthesis까지 검증된 cumulative path를 이어서 실행한다.

연구 방법과 domain logic은 하드코딩하지 않는다.
`SKILL.md`와 `runtime/b2/` contracts가 조사 절차를 정하고, Runtime은 실행·검증·저장만 한다.

코드: [run.py](../src/research_b2/run.py)  
상위: [README.md](../README.md)

---

## 검증된 범위

```text
Wave 1
  → Replan
  → Wave 2
  → Cumulative Matcher / State
  → Independence Audit / Challenge
  → Finalizer
  → Stop Record
  → Synthesis
```

`--max-waves 2`만 지원한다.
이 값은 semantic convergence 선언이 아니라 resource safety cap이다.
자세한 기록 규칙: [b2-stop-record.md](b2-stop-record.md)

---

## 실행

진입점:

```bash
python3 -m src.research_b2.run
```

### Physical AI

```bash
python3 -m src.research_b2.run \
  --task tasks/physical-ai-research.md \
  --skill deep-research \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2 \
  --output-root outputs/research-b2/e2e/physical-ai
```

### Robot Spec + PDF

```bash
python3 -m src.research_b2.run \
  --task tasks/robot-spec-research.md \
  --skill deep-research \
  --input-dir inputs \
  --max-workers 3 \
  --max-turns 6 \
  --max-waves 2 \
  --output-root outputs/research-b2/e2e/robot-spec \
  --report-out reports/robot-spec-comparison.md
```

`--input-dir`만 capability scope로 넘긴다.
로봇 제품명이나 PDF 파일명은 Runtime에 박아 두지 않는다.

---

## Wave 내부

각 Wave는 같은 순서를 탄다.

```text
Parallel Workers
  → Sequential Recovery
  → Evidence Pool
```

관련: [b2-parallel-workers.md](b2-parallel-workers.md) · [b2-recovery.md](b2-recovery.md) · [b2-evidence-pool.md](b2-evidence-pool.md)

---

## 이 단계가 하지 않는 것

- Skill의 convergence 숫자를 Python으로 재구현하지 않는다
- Wave 1 Replanner가 두 번째 Wave를 요청하지 않으면 임의로 진행하지 않는다
- pending independence claim이 없으면 Challenge verdict를 새로 만들지 않는다
- 3-wave 이상을 지원한다고 가정하지 않는다
