# 6. 검증 결과

상위 문서: [README.md](../README.md)

최종 deep-research 비교: [deep-research-off-vs-on-final.md](deep-research-off-vs-on-final.md)  
xlsx 실험: [04-xlsx-experiment.md](04-xlsx-experiment.md)

---

## 가능한 것

현재 실험에서 확인된 기능:

- 공개 Agent Skill 다운로드
- `SKILL.md` 발견
- Metadata 검사
- Skill Activation
- Gemma4 Context에 Skill 적용
- Gemma4 Tool Calling
- 외부 Tool 실제 실행
- Tool Result 기반 반복 추론
- Skill에 따른 행동 변화
- Skill 기반 결과 Format 변화

따라서 **Claude Code 없이 Gemma4에서도 Agent Skills의 핵심 실행 개념을 구현할 수
있음**을 확인하였다.

### deep-research에서 구체적으로 확인된 변화

| 항목 | Skill OFF | Skill ON |
|---|---|---|
| 원문 fetch | 0 | 2 |
| 연구 Sub-goal 명시 | 검색 분해만 | 보고서에 명시 |
| Counter-evidence / Gaps | 없음 | 구조화 |
| Sources / footnote | 미흡 | 생성 |
| 실행시간 | 473초 | 643초 (+35.9%) |

판정: **B1 Partial Compatibility 성공**

---

## 현재 제한사항

공개 Skill을 다운로드하는 것만으로 모든 기능이 자동 실행되는 것은 아니다.
Skill이 요구하는 기능에 대응하는 **Runtime Capability**가 필요하다.

| Skill에서 요구 | Runtime에 필요 |
|---|---|
| Web Search | Web Search Tool |
| Excel 읽기 | Excel Tool |
| Script 실행 | Sandbox / Shell |
| Sub-agent | Agent Spawn |

즉 `SKILL.md`는 업무 절차를 제공하지만 **실행환경 자체를 제공하지 않는다.**

따라서 Gemma4에서 범용적으로 Agent Skills를 사용하려면 별도의 Agent Runtime이
필요하다.

### B1에서 부분 충족 / 미지원

- 병렬 sub-agent
- Multi-wave research
- 모든 citation의 원문 검증
- 엄격한 2-source triangulation
- 완전한 source quality enforcement
- scripts / references / assets on-demand load
- Context Compaction

---

## 왜 별도 Runtime이 필요한가

Skill은 지침 파일이고, Gemma는 모델이다. 그 사이에서 다음을 담당하는 Runtime이
있어야 공개 Skill을 Claude Code 없이 재현·비교할 수 있다.

- Loader
- Tool Binding
- Agent Loop
- 검증
- 기록

현재 단계는 **B1 Partial Compatibility 검증 완료**로 정의한다.
