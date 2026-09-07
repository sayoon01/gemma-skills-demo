# 검색 순위 vs Source Tier 관측점

셋업 검색 스모크에서 확인한 비교 관측점이다.

- Skill OFF Baseline 실행 결과와는 별도 문서
  (`reports/deep-research-skill-off-baseline.md`)
- 셋업 증빙: `docs/evidence/deep-research-setup/README.md` §4
- 스모크 JSON: `docs/evidence/deep-research-setup/web-tools-smoke.json`

## 1. 관찰

Physical AI 관련 검색 테스트에서:

- 첫 번째(검색 순위 1위) 결과: Wikipedia
- 같은 결과 집합의 다른 결과: Qualcomm, AWS, Deloitte 등

즉 검색 엔진 순위와 출처 품질 등급이 일치하지 않는 케이스가 실제로 나왔다.

## 2. 원본 Skill의 source tier

deep-research Skill은 출처를 대략 다음 순으로 평가하도록 요구한다.

1. Primary
2. Peer-reviewed
3. Reputable news
4. Industry
5. Expert
6. Community

Wikipedia는 검색 순위 1위이지만 tier상으로는 Primary(예: Qualcomm 공식 문서)보다 낮다.

## 3. 왜 Deep Research 시험에 유리한가

결함이 아니라 비교 실험에 유리한 신호다.

Skill ON에서 Gemma가:

- 검색 순위 1위이므로 Wikipedia부터 사용하는지
- Qualcomm 같은 공식·산업 문서를 더 우선하는지

를 실제로 가를 수 있다.

## 4. Skill ON에서 확인할 질문

1. 검색 결과 중 어떤 URL을 먼저 `fetch_page`로 읽는가
2. Wikipedia를 Primary처럼 취급하는가, 아니면 tier상 하위로 두는가
3. Qualcomm·AWS 등 공식/산업 출처를 명시적으로 우선하는가
4. 최종 보고서 citation에서 tier 차이가 드러나는가

## 5. 문서 경계

| 문서 | 역할 |
|---|---|
| `reports/deep-research-skill-off-baseline.md` | Skill OFF 실행 Baseline |
| `reports/source-tier-vs-search-rank.md` (본 문서) | 셋업 스모크의 source tier 관측점 |
| `docs/evidence/deep-research-setup/` | 웹 도구·Skill 로드 기술 증빙 |
