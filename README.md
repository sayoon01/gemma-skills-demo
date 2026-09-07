# gemma-skills-demo

공개 Agent Skills 형식의 xlsx 스킬을 Claude Code 없이
Gemma(Ollama)와 Python 도구로 엑셀 생성에 적용할 수 있는지 검증하는 프로젝트입니다.

스킬은 작업 지침을 제공하고, 실제 파일 생성·재계산·검증은 Python 도구가 수행합니다.

## 문서

- [xlsx 검증 보고서](docs/xlsx-validation-report.md) — 센터장님 보고용 결과
- [대표 증빙](docs/evidence/xlsx-demo/README.md) — 보고서에서 참조하는 성공 실행 한 세트
- [스킬 기본 규격 검사](docs/skill-validation.md)

## 폴더 역할

| 경로 | 역할 |
|---|---|
| `docs/xlsx-validation-report.md` | 검증 결과 설명 |
| `docs/evidence/xlsx-demo/` | 대표 증빙 (Git 포함) |
| `outputs/` | 전체 실행 로그·중간 결과·백업 (Git 제외) |
| `examples/` | 합성 시험 입력 |
| `src/` | 스킬 로더, Ollama 클라이언트, 엑셀 도구 |
| `checks/` | 환경·스킬·에이전트 검사 스크립트 |

## 준비

```bash
cp .env.example .env
# OLLAMA_BASE_URL, OLLAMA_MODEL 확인
```

Ollama에 `gemma4:31b`(또는 `.env`의 모델)가 준비되어 있어야 합니다.
의존성: `openpyxl`, `markitdown`, LibreOffice(원본 스킬 `recalc.py`용).

서브모듈:

```bash
git submodule update --init --recursive
```

## 실행 방법

프로젝트 루트에서 `PYTHONPATH=.`를 사용합니다.

```bash
# 환경 확인
python checks/check_environment.py

# 스킬 로더 + Gemma 연결 확인
python checks/check_skill_prompt.py

# 엑셀 도구만 실행 (모델 미사용)
python -m src.tools.sales_workbook --input examples/sales-demo.json

# Gemma가 도구를 호출하는 통합 시험
python checks/check_sales_agent.py --input examples/sales-demo.json

# 행 수·0원·시트 이름 확장 시험
python checks/check_sales_agent.py --input examples/sales-extended.json
```

실행 기록은 `outputs/`에 쌓입니다. 공개용 대표 결과는
`docs/evidence/xlsx-demo/`를 확인하세요.
