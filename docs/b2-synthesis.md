# B2 Final Synthesis

검증된 cumulative state와 stop record만으로 최종 보고서를 작성한다.
Worker raw history나 search snippet을 합성 입력에 넣지 않는다.

코드: [synthesis.py](../src/research_b2/synthesis.py)  
계약: [synthesis.md](../runtime/b2/synthesis.md)  
관련: [b2-stop-record.md](b2-stop-record.md) · [b2-e2e.md](b2-e2e.md)

---

## Citation

### Web

```text
[SRC001]
[SRC002]
```

### PDF

```text
[PDF001 p.2]
[PDF001 p.3]
```

PDF citation은 실제 VERIFIED page만 허용한다.
page 2만 검증했다면:

```text
[PDF001 p.2]   ✅
[PDF001 p.3]   ❌
```

존재하지 않는 source ID, 검증되지 않은 PDF page, 허용되지 않은 URL은 Validator가 거부한다.

---

## Stop wording

합성 프롬프트는 stop record를 존중한다.
`converged=true`가 아니면 semantic convergence를 주장하지 않는다.

관련: [b2-stop-record.md](b2-stop-record.md)

---

## 이 단계가 하지 않는 것

- 새 검색·새 fetch를 하지 않는다
- VERIFIED되지 않은 claim을 사실처럼 쓰지 않는다
- `user_stop` 같은 수동 실험 문구를 하드코딩하지 않는다
