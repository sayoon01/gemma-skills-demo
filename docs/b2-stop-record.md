# B2 Stop Record와 `max_waves`

`--max-waves`는 semantic convergence 조건이 아니다.
현재 E2E Runtime에서는 resource safety cap으로 쓴다.

코드: [run.py](../src/research_b2/run.py) (`build_stop_record`)  
계약: [convergence.md](../runtime/b2/convergence.md)  
관련: [b2-replanner.md](b2-replanner.md) · [b2-synthesis.md](b2-synthesis.md)

---

## 기록 원칙

Wave 2까지 실행했다고 해서:

```json
{
  "converged": true
}
```

라고 쓰지 않는다.

Skill의 convergence 기준을 충족하지 못한 채 resource cap에 도달하면:

```json
{
  "converged": false,
  "stop_reason": "max_waves_reached"
}
```

로 기록한다.

현재 Replanner schema에 explicit `converged` 필드가 없으면 Runtime이 임의로 `true`를 만들지 않는다.

---

## stop_reason 예

| 조건 | stop_reason |
|---|---|
| Replanner가 `converged=true` | `semantic_convergence` |
| resource cap 도달 | `max_waves_reached` |
| 다음 Wave를 요청했지만 Runtime이 멈춤 | `runtime_stopped_before_requested_next_wave` |
| 그 외 명시적 수렴 없음 | `replanner_stop_without_explicit_convergence` |

이 구분은 실험 결과 해석에 필요하다.
`max_waves` 도달을 Skill 성공으로 읽지 않는다.
