# deep-research Skill 로드 및 웹 도구 연결 준비 증빙

xlsx Runtime 병목 확인 이후, community deep-research Skill을
Gemma Runtime에 연결하기 위한 사전 확인 결과이다.

업무 원본 로그는 포함하지 않는다.

## 확인 일시
2026-09-07

## 1. Skill 로드

```bash
python3 -m src.skill_loader \
  --root vendor/community-skills/deep-research \
  --skill deep-research
```

| 항목 | 결과 |
|---|---|
| 발견 | deep-research 1개 |
| 활성화 | 성공 |
| 본문 길이 | 12,995자 |
| SHA-256 | e8440a6a0cf41739fd5ddce6f66fc1da69e77ee3597162ed35177b86162e1159 |

기본 검색 경로에 `vendor/community-skills`와 서브모듈 `vendor/deep-research`를
함께 둔다. 동일 이름이 중복되면 먼저 찾은 경로를 쓰고 나머지는 건너뛴다.

## 2. 네트워크·패키지

| 확인 | 결과 |
|---|---|
| `requests` / `bs4` / `lxml` | 설치됨 |
| `https://example.com` | HTTP 200 |
| DuckDuckGo HTML (`html.duckduckgo.com`) | HTTP 202, 직접 파싱 부적합 |
| `ddgs` 패키지 검색 | 성공 (예: Physical AI 관련 5건) |
| HTML 페이지 읽기 (`requests`+BeautifulSoup) | 성공 |

검색은 DuckDuckGo HTML 스크래핑 대신 `ddgs`를 사용한다.

## 3. 웹 도구 스모크 테스트

코드: `src/web_tools.py`

당시 관찰 결과(요약):

- `web_search`: 질의에 대해 제목·URL·snippet·domain 반환
- `fetch_page`: Wikipedia 등 HTML에서 텍스트 추출, focus 기반 축소 가능
- focus 필터가 과도하면 본문이 짧아지거나 네비게이션 조각이 섞일 수 있음 → 개선 여지

샘플 요약 JSON: [web-tools-smoke.json](web-tools-smoke.json)

## 4. 검색 순위 vs source tier (비교 실험에 유리)

Physical AI 관련 검색에서 **1위는 Wikipedia**였고, 같은 결과 집합에
Qualcomm·AWS·Deloitte 등 산업/공식 성격의 출처도 포함됐다.

원본 deep-research Skill은 source tier를 대략 다음 순으로 평가한다.

1. Primary  
2. Peer-reviewed  
3. Reputable news  
4. Industry  
5. Expert  
6. Community  

Wikipedia는 검색 순위 1위이지만 tier상으로는 Primary(예: Qualcomm 공식 문서)보다
낮다. 따라서 Skill ON 비교에서 Gemma가:

- 검색 순위 1위이므로 Wikipedia부터 쓰는지  
- Qualcomm 등 공식·산업 문서를 더 우선하는지  

를 실제로 가르는 관측점이 된다. 결함이 아니라 Deep Research 시험에 유리한 신호다.

## 5. 아직 하지 않은 것

- Gemma + deep-research Skill ON/OFF 동일 질문 비교
  (위 source tier 우선순위 준수 여부 포함)
- Skill이 요구하는 병렬 sub-agent 전체 구현
- 인용 보고서 품질 검증

## 검증 범위

Skill 파일 인식과 웹 검색·페이지 읽기 도구의 단독 동작 확인이다.
deep-research 전체 워크플로 성공을 의미하지 않는다.
