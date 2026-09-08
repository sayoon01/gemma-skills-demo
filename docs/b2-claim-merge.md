# B2 Claim Merge: Wave 사이 의미 비교

Claim Merge는 최신 Wave의 검증된 claim을 이전 누적 claim과 비교한다.
새 조사를 하지 않는다. 입력에 있는 claim과 evidence state만 본다.

의미 관계는 Gemma가 정한다.
Python은 packet을 만들고, JSON과 claim ID만 검사한다.

상위: [b2-evidence-pool.md](b2-evidence-pool.md) · [b2-replanner.md](b2-replanner.md)  
코드: [cumulative_matcher.py](../src/research_b2/cumulative_matcher.py) · [cumulative_state.py](../src/research_b2/cumulative_state.py)  
계약: [claim-merge.md](../runtime/b2/claim-merge.md)

---

## 구조

```text
Wave 1 validated claims
        ↓
Wave 2 validated claims
        ↓
Gemma Matcher          (thinking OFF, 도구 없음)
        ↓
Generic schema repair
        ↓
Cumulative State       (측정과 누적만)
```

Matcher가 정하는 것:

- `SAME` / `EXTENDS` / `CONTRADICTS` / `NOVEL`
- `is_novel`
- `matched_prior_claim_refs`

`cumulative_state.py`는 이 판정을 다시 하지 않는다.
claim 노드, relation edge, running novelty, canonical URL source registry만 남긴다.

---

## 무엇을 넘기는가

Gemma에게 주는 것은 세 가지다.

- 활성 public `SKILL.md`
- `claim-merge.md`. 관계 이름과 novelty 기준, 출력 형식
- compact claim packet. `claim_ref`, claim 문장, runtime status, verified evidence 개수

관계 정의는 Python에 없다.
`RELATIONS`는 출력이 그 네 값 중 하나인지만 본다.

---

## Validator와 Repair

허용 필드는 `comparisons`와, 각 항목의 `new_claim_ref`, `relation`, `matched_prior_claim_refs`, `is_novel`, `reason`뿐이다.

- 새 Wave claim은 정확히 한 번씩 나와야 한다
- prior ref는 이전 누적 집합에 있는 것만 쓴다
- `NOVEL`은 matched prior가 비어 있어야 한다
- `SAME` / `EXTENDS` / `CONTRADICTS`는 matched prior가 있어야 한다

invalid면 Gemma Repair가 최대 2번 돈다. thinking은 끄고, 응답은 JSON만 받는다.
repair는 schema와 ID만 고친다. 새 claim이나 새 URL을 만들지 않는다.

---

## 측정값

Matcher ratio와 Skill convergence용 ratio는 따로 남긴다.

- `wave2_matcher_ratio_new_claims`: Wave 2 accepted claim 중 `is_novel`
- `novelty_ratios_running_total`: 새 materially distinct finding / 누적 running claim total

수렴 숫자 자체는 public `SKILL.md`에만 있다.
[convergence.md](../runtime/b2/convergence.md)는 이 측정값을 어떻게 기록할지만 정한다.

---

## 이 단계가 하지 않는 것

- 새 검색, 새 fetch를 하지 않는다
- 문장 유사도로 SAME을 기계 판정하지 않는다
- `CONTRADICTS`를 SAME으로 숨기지 않는다
- 출처 독립성이나 triangulation을 여기서 확정하지 않는다. 그건 [b2-source-independence.md](b2-source-independence.md)다
- 최종 사용자 보고서를 쓰지 않는다
