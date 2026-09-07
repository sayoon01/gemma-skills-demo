# gemma-skills-demo

공개 Agent Skills를 Claude Code 없이 Gemma(Ollama) Runtime에 적용할 수 있는지
검증하는 프로젝트입니다.

스킬은 작업 지침을 제공하고, 실제 파일 읽기·검사·생성은 Python 도구가 수행합니다.
일상 실행은 `run.py`로 하며, 작업이 바뀌면 **입력 파일**과 **요청 문서**만 바꿉니다.

## 문서

- [xlsx 검증 보고서](docs/xlsx-validation-report.md) — 매출 데모 보고용 결과
- [대표 증빙 (매출 데모)](docs/evidence/xlsx-demo/README.md) — 성공 실행 한 세트
- [Runtime 병목 증빙](docs/evidence/xlsx-runtime/README.md) — Skill 적용 성공 + context/timeout 한계
- [확인된 문제](docs/known-issues.md)
- [스킬 기본 규격 검사](docs/skill-validation.md)

## 현재까지 확인한 것

| 항목 | 결과 |
|---|---|
| 공개 xlsx Skill 로드 | 성공 |
| Gemma4의 도구 자율 선택·실행 | 성공 |
| 실제 Excel 구조 확인·범위 읽기 | 성공 |
| 대량 tool 결과 + 작은 context | 대화 이력 유실 |
| `num_ctx=65536` | context 유지, 최종 분석은 300초 timeout |
| 병목 | Skill 지원이 아니라 Runtime 효율 |

xlsx를 더 깊게 최적화하기보다 community `deep-research` Skill 실험으로 전환합니다.
`vendor/deep-research` 서브모듈(또는 `vendor/community-skills/deep-research`)을 사용합니다.

## 폴더 역할

| 경로 | 역할 |
|---|---|
| `run.py` | 공통 실행기 (스킬·입력·요청을 받아 실행) |
| `tasks/` | 사용자 요청 문서 |
| `inputs/` | 실제 입력 엑셀 (Git 제외, 로컬 보관) |
| `docs/evidence/xlsx-demo/` | 매출 데모 공개 증빙 |
| `docs/evidence/xlsx-runtime/` | Skill 적용·Runtime 한계 공개 증빙 |
| `outputs/` | 전체 실행 로그 (Git 제외) |
| `examples/` | 합성 시험 입력 |
| `vendor/` | 공개 Skill 저장소 (서브모듈) |
| `src/` | 스킬 로더, Ollama 클라이언트, 전용 도구 |
| `checks/` | 환경·연결·실행 기록 검사·회귀 |

## 준비

```bash
cp .env.example .env
# OLLAMA_BASE_URL, OLLAMA_MODEL 확인
git submodule update --init --recursive
```

Ollama에 `gemma4:31b`(또는 `.env`의 모델)가 필요합니다.
의존성: `openpyxl`, `markitdown`, LibreOffice(매출 도구·원본 `recalc.py`용).

## 공통 실행기 (권장)

현재 `run.py`는 엑셀 **구조 확인·범위 읽기·분석 답변**까지 지원합니다.
결과 엑셀 생성은 아직 포함하지 않습니다.

```bash
python3 run.py \
  --skill xlsx \
  --input "inputs/03_트윈_예실대비표.xlsx" \
  --input "inputs/04_분산_예실대비표.xlsx" \
  --request "tasks/budget-comparison.md"
```

다른 작업은 `--input`과 `--request`만 바꿉니다.
기록은 `outputs/runs/run-*/`에 저장됩니다.

| 파일 | 내용 |
|---|---|
| `request.md` | 요청 문서 복사 |
| `input-manifest.json` | 입력 파일·해시 |
| `tool-calls.json` | 도구 호출과 결과 |
| `answer.md` | 모델 최종 답변 |
| `validation.json` | 자동 검증 항목 |
| `result.json` | 전체 실행 상태 |

실행 기록 점검:

```bash
python checks/inspect_run.py outputs/runs/run-XXXX
```

## 기존 확인용 명령

```bash
python checks/check_environment.py
python checks/check_skill_prompt.py
python -m src.tools.sales_workbook --input examples/sales-demo.json
python checks/check_sales_agent.py --input examples/sales-demo.json
```

`src/tools/sales_workbook.py`는 매출 전용 예제 도구입니다.
`src/tools/budget_reader.py`는 예실대비표 양식 전용 읽기·대조기이며,
공통 실행기의 범용 도구와는 별개입니다.
