# 04. Anthropic xlsx Skill — Gemma4 적용 실험

> 실험일: 2026-09-07  
> 목적: Anthropic 공개 Repository의 `xlsx` Skill을 Claude Code가 아닌 `gemma4:31b`
> Runtime에서 활성화하고, Skill 지침에 따라 실제 Excel Tool을 호출할 수 있는지 검증한다.

상위 문서: [README.md](../README.md)

관련: [xlsx-runtime-issues.md](xlsx-runtime-issues.md) ·
[docs/evidence/xlsx-runtime/](../docs/evidence/xlsx-runtime/README.md) ·
[docs/evidence/xlsx-demo/](../docs/evidence/xlsx-demo/README.md) ·
[docs/known-issues.md](../docs/known-issues.md)

---

## 1. 실험 대상

- 경로: `vendor/anthropic-skills/skills/xlsx/`
- Skill: `SKILL.md`

Anthropic Repository 설명상 Document Skill(`xlsx` 등)은 소스를 확인할 수 있지만
일반 예제 Skill과 라이선스 성격이 동일하지 않다. 본 문서에서는
**Anthropic 공개 Repository의 xlsx Skill**이라고 표현한다.

---

## 2. 검증 목표

최종 Excel 보고서 품질 평가가 아니라, 다음 핵심 호환성을 확인한다.

1. 공개 `xlsx` `SKILL.md` 발견 · Activation
2. Gemma4에 Skill Instruction 전달
3. Gemma4가 Excel Tool을 스스로 선택
4. 실제 Workbook 구조·Cell Range 읽기
5. Tool Result 기반 후속 추론

목표 Chain:

```text
SKILL.md → Gemma4 Tool Choice → Actual Excel Read
```

---

## 3. 입력·요청

- 입력: 예실대비표 Excel 2개 (`inputs/`, Git 제외)
- 요청: 예산 비교 요청 파일. 저장소에서는 제거했다.

핵심 요구 요약: Sheet/Header 파악, 합계·비교·음수 잔액·한쪽만 있는 항목,
파일명/Sheet/Cell 근거, 이중 합산 방지, 근거 없는 주장 금지, **원본 파일 변경 금지**.

(업무 원본 셀 값은 공개 문서에 포함하지 않는다.
xlsx 보조 스크립트도 저장소에서 뺐다.)

---

## 4. 최초 실행 (`run-hb_2vzzc`)

### Turn 1

사용자가 Tool 이름을 지시하지 않았는데도 Gemma4가 두 Workbook에
`inspect_workbook`을 각각 호출했다. Skill + Tool Schema 기반 자율 선택이다.

### Turn 2

구조 결과를 받은 뒤 두 파일에 `read_excel_range`(예: `A1:R29`)를 호출해
실제 Cell Data까지 읽었다.

숫자형 문자열이 Tool Output에 포함되는 등 정규화 이슈도 관찰되었다.

### 최종 Turn 문제

Skill·Tool Calling은 성공했지만 최종 Turn에서 원래 사용자 요청을 유지하지 못하고
원칙 설명·파일 재요청으로 종료했다.

`prompt_eval_count`가 앞 Turn보다 마지막에서 크게 감소(예: 7609 → 2472)했고,
당시 Runtime Context가 **32768**로 동작한 것과 연관된 History 손실 가능성이 높다.
실행기는 `read_analysis_completed`로 기록했으나 실제는 **분석 미완료**이다.

---

## 5. 64K Context 재실행 (`run-k_b3sp0q`)

`src/ollama_client.py`에 `num_ctx=65536`, `num_predict=4096`을 적용하고
실제 Runtime Context 65536을 확인했다.

History 조기 잘림은 완화되었으나 3번째 Model Call에서 **ReadTimeout 300초**가 발생했다.

| 설정 | 현상 |
|---|---|
| ~32K | Context History 손실 → 분석 미완료 |
| 64K | Context 유지 → 대용량 Tool Result 처리시간 증가 → Timeout |

Excel Tool Call 자체(`inspect_workbook`×2, `read_excel_range`×2)는 성공했다.
핵심 병목은 Tool Error가 아니라 **Tool Result 크기 + Model 처리 비용**이다.

두 Workbook의 넓은 Range를 읽으면서 Cell별 value/type/number_format 등이 반복되어
Tool Message가 크게 증가했다 (대략 수만 자 규모).

```text
User Request + SKILL.md + Inspect×2 + Large Range JSON×2
```

→ Context 누적.

---

## 6. 판정

| 항목 | 결과 |
|---|---|
| 공개 xlsx Skill 발견·Activation | 성공 |
| Gemma4 Skill Instruction 적용 | 성공 |
| Excel Tool 자율 선택·실행 | 성공 |
| 실제 Workbook / Cell 읽기 | 성공 |
| 2개 Workbook 처리 | 성공 |
| 최종 전체 분석 | Runtime 문제로 미완료 |

**판정: Gemma4 Partial Compatibility (xlsx)**

검증된 Chain:

```text
Anthropic xlsx SKILL.md
  → Gemma4 → inspect_workbook → Actual Read
  → read_excel_range → Actual Cell Data
```

의미: Claude Code가 아니어도 공개 `xlsx` `SKILL.md`를 Gemma4 Runtime에 적용하면
Skill 지침에 따라 Excel Tool을 선택·실행할 수 있다. 완전한 실행을 위해서는
Context 관리, Tool Result Compaction, 숫자 정규화, Long-running Inference 관리가 필요하다.

---

## 7. 향후 개선 (기록만, 즉시 심화 최적화하지 않음)

1. **Compact Tool Result** — Cell별 반복 Metadata 축소, 행 단위/compact 표
2. **선택적 Range Read** — Header → Detail → Total 단계적 읽기
3. **숫자 정규화** — comma numeric string → number
4. **Evidence Summary** — Raw JSON 대신 Structured Evidence로 Context 유지

xlsx를 더 깊게 최적화하기보다 community `deep-research` 실험으로 전환하였다.

### 요약

| 항목 | 상태 |
|---|---|
| SKILL.md Load / Skill-driven Tool Choice | O |
| Actual Excel Access / Multi-turn Tool Execution | O |
| Large-context Stable Completion | X |

> Gemma4에서 xlsx Agent Skill의 핵심 실행은 가능하지만, 문서형 Tool이 반환하는
> 대용량 결과를 안정적으로 처리하기 위한 Context/Tool-result 최적화 Runtime이
> 추가로 필요하다.

### 관련

- Runs: `outputs/runs/run-hb_2vzzc`, `outputs/runs/run-k_b3sp0q` (로컬)
- [Anthropic Skills](https://github.com/anthropics/skills)
