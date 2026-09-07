# 4. xlsx Skill 실험

상위 문서: [README.md](../README.md)

관련:

- [xlsx-runtime-issues.md](xlsx-runtime-issues.md)
- [docs/evidence/xlsx-runtime/](../docs/evidence/xlsx-runtime/README.md)
- [docs/evidence/xlsx-demo/](../docs/evidence/xlsx-demo/README.md)
- [docs/known-issues.md](../docs/known-issues.md)
- [tasks/budget-comparison.md](../tasks/budget-comparison.md)

---

## 목적

Anthropic 공개 `xlsx` Skill을 Gemma4에서 실행하여 실제 Excel 파일 분석 가능성을
검증하였다.

목표: Skill 사용법·공개 Skill 다운로드·Gemma4 적용 가능성 확인.
완성된 xlsx 에이전트 제품화는 목표가 아니다.

---

## 검증 항목

- 공개 `xlsx/SKILL.md` 발견
- Skill Activation
- Gemma4 Tool Calling
- `inspect_workbook`
- `read_excel_range`
- 실제 Excel cell data 확인

---

## 확인된 성과

Gemma4가 xlsx Skill instruction을 읽고 적절한 Excel Tool을 선택할 수 있음을
확인하였다.

| 단계 | 결과 |
|---|---|
| SKILL.md 로드 | 성공 |
| Skill 지침 이해 | 성공 |
| `inspect_workbook` 자율 선택 | 성공 |
| 두 Excel 구조 확인 | 성공 |
| `read_excel_range` 자율 선택 | 성공 |
| 실제 데이터 읽기 | 성공 |

매출 데모(별도): `create_sales_workbook` 호출 → 수식·차트·재계산 검증 passed.
증빙: [docs/evidence/xlsx-demo/](../docs/evidence/xlsx-demo/README.md)

---

## 발견 문제

대용량 Cell JSON이 Tool Result로 그대로 Context에 누적되면서 다음이 발생했다.

### A. ~32K context (`run-hb_2vzzc`)

- 파일 읽기 성공
- 요청 분석 미완료 (원칙 설명·파일 재요청으로 종료)
- 실행기는 `read_analysis_completed`로 기록했으나 실제는 **분석 미완료**

### B. 64K context (`run-k_b3sp0q`)

- Context 유지 가능
- 도구 4회 성공 후 3번째 모델 호출에서 HTTP ReadTimeout 300초

### 해석

**병목은 Skill 지원이 아니라 Runtime 효율**이다.

- 셀별 `{cell, type, value, number_format}` 반복으로 tool 결과가 커짐
- timeout만 늘리는 재시도는 좋은 실증이 아님

보류한 수정(기록만): Tool Result compact 표 형태, 수집/분석 단계 분리 등.
상세: [xlsx-runtime-issues.md](xlsx-runtime-issues.md)

xlsx를 더 깊게 최적화하기보다 community `deep-research` Skill 실험으로 전환하였다.

---

## 실행 예

```bash
python3 run.py \
  --skill xlsx \
  --input "inputs/....xlsx" \
  --request "tasks/budget-comparison.md"
```
