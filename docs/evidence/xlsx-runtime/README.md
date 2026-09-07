# Gemma4 xlsx Skill 적용 및 Runtime 병목 증빙

공개 Anthropic xlsx Skill의 `SKILL.md`를 Gemma4 Runtime에 로드하여
엑셀 구조 확인·범위 읽기 도구를 자율 호출하는 실험을 기록한다.

업무 원본 셀 값은 공개하지 않는다. 상세 로그는 로컬 `outputs/runs/`에 보관한다.

## 실험 목적

Skill 사용법·공개 Skill 다운로드·Gemma4 적용 가능성을 검증한다.
완성된 xlsx 에이전트 제품을 만드는 것이 목적이 아니다.

## 실행 요약

| 단계 | 결과 |
|---|---|
| 1. SKILL.md 로드 | 성공 |
| 2. Gemma4가 skill 지침 이해 | 성공 |
| 3. `inspect_workbook` 자율 선택 | 성공 |
| 4. 두 Excel 구조 확인 | 성공 |
| 5. `read_excel_range` 자율 선택 | 성공 |
| 6. 두 파일 실제 데이터 읽기 | 성공 |
| 7. 기본(약 32K) context | 실패: 앞 context 유실로 분석 미완료 |
| 8. `num_ctx=65536` | context 유지 가능 |
| 9. 64K에서 최종 분석 | 실패: 300초 HTTP ReadTimeout |

## 대상 실행 (로컬)

| 실행 ID | 설정 | 공개 판정 |
|---|---|---|
| `run-hb_2vzzc` | 기본 options | 파일 읽기 성공, 요청 분석 미완료. 실행기는 `read_analysis_completed`로 기록했으나 실제 답변은 원칙 설명·재요청 |
| `run-k_b3sp0q` | `num_ctx=65536`, `num_predict=4096` | 도구 4회 성공 후 3번째 모델 호출에서 ReadTimeout(300초) |

관련 기술 정정: [known-issues.md](../../known-issues.md)

## 보고용 결론

Anthropic 공개 xlsx Skill의 SKILL.md를 Gemma4 Runtime에서 직접 로드하여 시험한 결과, Gemma4가 Skill 지침에 따라 Excel 구조 확인 및 범위 읽기 도구를 자율적으로 선택·실행하는 것을 확인하였다. 다만 대량의 셀별 JSON 결과를 그대로 모델 Context에 전달하는 경우 32K Context에서는 대화 이력이 잘리고, 64K로 확장하면 Context는 유지되나 31B 모델 처리 시간이 증가하여 Timeout이 발생하였다. 따라서 Skill 적용 가능성과 별개로 Tool 결과 압축 및 Context 관리가 Runtime 구현의 주요 고려사항으로 확인되었다.

## 병목 해석

현재 병목은 Skill 지원 여부가 아니라 Runtime 효율이다.

- 셀별 `{cell, type, value, number_format}` 반복으로 tool 결과가 커짐(약 7만 자 규모)
- 65K context + gemma4:31b + 대량 tool 결과를 한 번에 처리하는 데 300초를 초과
- timeout을 늘리는 것은 좋은 실증이 아님

## 보류한 최소 수정 (미구현, 기록만)

`read_excel_range` 결과를 compact 표 형태로 바꾸는 방안을 다음으로 남긴다.

현재(셀별 반복):

```json
{"cell": "D21", "type": "n", "value": 1858000.0, "number_format": "#,##0"}
```

후보(행 단위):

```json
{
  "range": "A1:R29",
  "rows": [
    {"row": 21, "values": {"A": "...", "B": "...", "D": 1858000}}
  ]
}
```

또는 더 compact하게:

```json
{
  "columns": ["A", "B", "C", "D"],
  "rows": [[21, "...", "...", "...", 1858000]]
}
```

xlsx를 더 깊게 최적화하기보다, 이후 community `deep-research` Skill 실험으로 전환한다.

## 파일

- [result-32k.json](result-32k.json): `run-hb_2vzzc` 상태 요약 (업무 데이터 없음)
- [result-64k-timeout.json](result-64k-timeout.json): `run-k_b3sp0q` 상태 요약 (업무 데이터 없음)

## 검증 범위

- 확인: Skill 로드, 도구 자율 선택, 실제 파일 읽기
- 미확인: 요청한 비교 분석 완료, 수치 자동 검증, 결과 엑셀 생성
- 공개 제외: 예실대비표 원본 셀·tool-calls 전문
