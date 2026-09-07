# Gemma4 xlsx Skill Runtime 이슈 기록

xlsx Skill 적용 실험에서 확인된 문제이다.
deep-research Baseline(`reports/deep-research-skill-off-baseline.md`)과는 별도 문서이다.

관련 공개 증빙: `docs/evidence/xlsx-runtime/README.md`  
기술 정정: `docs/known-issues.md`

## 1. 실험 배경

Anthropic 공개 xlsx Skill의 `SKILL.md`를 Gemma4 Runtime에 로드하여
엑셀 구조 확인·범위 읽기 도구를 자율 호출하는 실험을 수행했다.

목적: Skill 사용법·공개 Skill 다운로드·Gemma4 적용 가능성 검증.
완성된 xlsx 에이전트 제품화는 목표가 아니다.

## 2. 이슈 A — 약 32K context에서 분석 미완료

| 항목 | 값 |
|---|---|
| 실행 ID | run-hb_2vzzc |
| 모델 | gemma4:31b |
| Skill | xlsx |
| 설정 | 기본 options (약 32K context) |

### 실제 결과

- 입력 파일 2개 구조 확인 성공
- 지정 범위 읽기 성공
- Tool 오류 0건
- 원본 파일 해시 유지
- 최종 답변은 분석 결과 대신 원칙 설명과 파일 재요청으로 종료

### 상태 판정 문제

실행기는 도구 호출과 최종 응답 종료 여부만 검사하여
`read_analysis_completed`로 기록했다.

실제 판정은 **파일 읽기 성공, 요청한 분석 미완료**이다.
원본 실행 기록은 수정하지 않고 이 문서에 정정한다.

### 진단

- 범위 읽기 결과에 셀별 메타데이터가 반복되어 입력이 커짐
- 데이터 추가 후 `prompt_eval_count`가 감소하는 현상 관찰
- 컨텍스트 잘림 또는 대화 유지 문제 가능성이 있으나,
  서버 내부에서 어떤 메시지가 유지되었는지는 확정하지 못함

공개 요약 JSON: `docs/evidence/xlsx-runtime/result-32k.json`

## 3. 이슈 B — 64K context에서 최종 분석 Timeout

| 항목 | 값 |
|---|---|
| 실행 ID | run-k_b3sp0q |
| 모델 | gemma4:31b |
| Skill | xlsx |
| 설정 | `num_ctx=65536`, `num_predict=4096` |

### 실제 결과

- CONTEXT 65536 적용 확인
- 도구 호출 4회까지 진행 (구조 확인·범위 읽기)
- 3번째 모델 호출에서 HTTP ReadTimeout 300초
- 요청을 잊은 형태가 아니라, 대량 tool 결과 처리 시간 초과로 판단

공개 요약 JSON: `docs/evidence/xlsx-runtime/result-64k-timeout.json`

## 4. 해석

| 확인 | 결과 |
|---|---|
| SKILL.md 로드 | 성공 |
| Skill 지침에 따른 도구 자율 선택 | 성공 |
| 실제 엑셀 파일 읽기 | 성공 |
| 요청한 비교 분석 완료 | 실패 |
| 병목 위치 | Skill 지원이 아니라 Runtime 효율 |

병목 요인:

- 셀별 `{cell, type, value, number_format}` 반복으로 tool 결과가 커짐(약 7만 자 규모)
- 65K context + gemma4:31b + 대량 tool 결과를 한 번에 처리하는 데 300초 초과
- timeout만 늘리는 재시도는 좋은 실증이 아님

## 5. 보류한 수정 (기록만, 즉시 구현하지 않음)

1. 셀별 반복 메타데이터를 줄여 도구 결과를 compact하게 전달
2. 원본 셀 위치·자료형은 필요한 범위에서 보존
3. 데이터 수집과 최종 분석 단계 분리
4. 최종 분석 요청에 원래 사용자 요청을 다시 포함
5. 모델 컨텍스트와 출력 제한을 명시적으로 설정
6. 파일 읽기 완료와 분석 검토 완료를 구분

후보 compact 형태 예시는 `docs/evidence/xlsx-runtime/README.md` 참고.

## 6. 이후 방향

xlsx를 더 깊게 최적화하기보다 community deep-research Skill 실험으로 전환한다.
xlsx 관련 실증은 이 문서와 `docs/evidence/xlsx-runtime/`에 고정한다.
