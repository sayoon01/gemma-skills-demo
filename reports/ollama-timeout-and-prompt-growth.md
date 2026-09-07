# Ollama ReadTimeout 및 Prompt 증가 분석

Skill ON (`run-wp1hegvs`) Turn 3에서 발생한 300초 ReadTimeout에 대한 분석과
다음 재시험 조치이다.

관련 실행:

- Skill OFF: `outputs/research-runs/run-zqa3vu3e` (completed, elapsed 473.015초)
- Skill ON: `outputs/research-runs/run-wp1hegvs` (failed, elapsed 575.859초)

## 1. 실패 원인

`src/ollama_client.py`의 HTTP read timeout이 `(10, 300)`이었다.
Ollama API의 3번째 모델 응답이 300초 내 완료되지 않아 `ReadTimeout`으로 종료됐다.

Skill/도구 발견 실패가 아니라 **한 호출 wall time** 문제다.

## 2. OFF vs ON response별 prompt / 시간

| Response | OFF prompt / eval / wall | ON prompt / eval / wall |
|---|---|---|
| 1 | 600 / 711 / 78.7s | **3827** / 1288 / **150.2s** |
| 2 | 4578 / 565 / 70.1s | **9152** / 739 / **93.0s** |
| 3 | 8262 / 2580 / **299.7s** | (미완료, ≥300s timeout) |

관찰:

- ON response-1 prompt는 Skill 본문(~13K자) 때문에 OFF 대비 **6.38×**
- ON response-2 prompt는 검색 누적으로 OFF 대비 **2.00×**
- OFF 최종 답변(response-3)만으로도 **299.7초**로 300초 한계에 거의 붙었다
- ON Turn 3은 response-2 기준 prompt 9k + Turn 2 검색 결과(~9k자 JSON)가 더 붙으므로
  OFF 최종(8.2k / 300초)보다 더 무거운 호출이 거의 확정이다

ON 모델 wall 합: 150.2 + 93.0 + ≥300 ≈ ≥543초 → 전체 elapsed 575.859초와 일치한다.

## 3. Tool 결과 크기 (ON)

| Turn | web_search | result JSON 대략 |
|---|---:|---:|
| 1 | 5 | ~11,190자 |
| 2 | 5 | ~9,200자 |

fetch_page는 실패 시점까지 0회. 검색만으로도 context가 빠르게 커진다.

## 4. 조치 판단

| 조치 | 판정 | 이유 |
|---|---|---|
| `timeout=(10, 600)` | **다음 재시험에 우선 적용** | OFF 최종도 300초에 붙었고 ON은 Skill+검색이 더 큼 |
| `num_predict` 조정 | **지금은 손대지 않음** | 실패는 생성 한도가 아니라 wall time. 줄이면 fetch/보고서 전에 잘릴 수 있음 |
| 검색 결과 compact | **근본 완화용, 재시험 전 필수 아님** | Turn당 ~10k자×2 wave. timeout만으로 버티면 fetch 이후 다시 터질 수 있음. 먼저 600으로 끝까지 가는지 확인 |

## 5. 코드 변경

`src/ollama_client.py`:

- 변경 전: `timeout=(10, 300)`
- 변경 후: `timeout=(10, 600)`

무작정 timeout만 계속 올리지는 않는다.
다음 Skill ON 재시험에서 완료 여부와 response별 prompt/시간을 본 뒤,
필요하면 검색 compact를 후속으로 적용한다.

## 6. 다음 재시험 시 시간 비교

전체 실행시간:

- OFF: `result.json`의 `elapsed_seconds=473.015`
- ON: 동일 필드 + `/usr/bin/time -v` wall clock

모델 응답별 시간:

- 각 `response-*.json`의 `total_duration` / 1e9
