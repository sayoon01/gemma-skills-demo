# 03. Gemma4 Agent Skills 적용 Runtime

> 실험 기준일: 2026-09-07  
> 목적: Claude Code가 아닌 Ollama 기반 `gemma4:31b`에서 공개 Agent Skill을 사용할 수
> 있도록 구성한 Runtime 구조와 구현 범위를 설명한다.

상위 문서: [README.md](../README.md)

관련 코드: [src/skill_loader.py](../src/skill_loader.py) ·
[src/ollama_client.py](../src/ollama_client.py) · [run.py](../run.py) ·
[research_run.py](../research_run.py) · [src/web_tools.py](../src/web_tools.py)

---

## 1. 목표

핵심 질문: **공개 Agent Skill 파일을 다운로드하여 Claude Code가 아닌 Gemma4에서도
사용할 수 있는가?**

여기서 "사용한다"는 `SKILL.md`를 Prompt에 넣는 것만으로 정의하지 않았다.
최소한 다음이 실제로 동작해야 한다.

1. 공개 Skill 발견
2. Skill Metadata 검사
3. Skill 활성화
4. Gemma4 Context에 Skill Instruction 전달
5. Skill에 필요한 Tool 제공
6. Gemma4가 Tool을 선택
7. 실제 Tool 실행
8. Tool Result를 다시 Gemma4에 전달
9. 필요한 만큼 반복
10. 최종 결과 생성

즉 **Skill-driven Agent Runtime**을 구성하는 것이 목표이다.

---

## 2. 전체 구조

```text
Public Skill Repository
          ↓
      Skill Loader
     Discovery / Validation / Activation
          ↓
     Full SKILL.md → Gemma4 System Context
          ↓
       gemma4:31b → Tool Calling
          ↓
   Tool Registry / Handler → Tool Result
          ↓
       Gemma4 (Agent Loop 반복) → Final Answer
```

---

## 3. 외부 Skill 관리

```text
vendor/
├── anthropic-skills/skills/   # xlsx, pdf, pptx, ...
└── community-skills/
    └── deep-research/SKILL.md
```

```python
DEFAULT_SEARCH_ROOTS = [
    ROOT / "vendor" / "anthropic-skills" / "skills",
    ROOT / "vendor" / "community-skills",
]
```

개별 Skill 이름을 코드에 하드코딩하지 않는다. 올바른 형식의 Directory가 추가되면
Loader가 자동 발견할 수 있도록 한다.

---

## 4. Skill Discovery / Validation

Loader는 `<root>/SKILL.md`, `<root>/*/SKILL.md`를 탐색하고 `name`, `description`,
경로, Body, SHA-256을 얻는다.

검사: `name` 형식·디렉터리 일치, `description` 비어 있지 않음(공개 Spec 기준 최대
1024자), YAML Body 존재, 중복 name.

선택 전 Metadata 중심, 활성화 시 전체 Body — Progressive Disclosure의 일부 재현.

참고: 공개 Spec을 엄격 적용하는 Loader와 실제 Repository 작성 관행 사이에 차이가
생길 수 있다. 향후 Strict Validation + Compatibility Warning Mode 분리를 고려한다.

---

## 5. Skill Activation

```bash
python3 research_run.py \
  --skill deep-research \
  --request tasks/physical-ai-research.md
```

기록 예:

- `skill`: deep-research
- `skill_base_dir`: `vendor/community-skills/deep-research`
- `skill_sha256`: `e8440a6a0cf41739fd5ddce6f66fc1da69e77ee3597162ed35177b86162e1159`

SHA-256으로 Skill 버전 추적·OFF/ON 재현성·소스 연결을 확보한다.

B1에서는 원본 Skill이 병렬 Sub-agent를 요구하지만 단일 세션만 쓰므로,
Runtime 제약을 System Context에 명시하고 Gaps에 한계를 적도록 한다.
이후 B2는 별도 세션으로 Coordinator와 Worker를 나눈다.
상위: [README.md](../README.md) · [docs/b2-sub-agents.md](../docs/b2-sub-agents.md)

---

## 6. Tool Binding

| 실험 | Generic Tool |
|---|---|
| xlsx | `inspect_workbook`, `read_excel_range` 등 |
| deep-research | `web_search`, `fetch_page` |

원칙: Skill-specific Workflow를 Python에 하드코딩하지 않는다.

- `SKILL.md` → 행동 지침
- Generic Tool → 실행 Capability

`deep_research()` 전용 Workflow로 결과를 흉내 내는 것이 아니라, Gemma4가
`SKILL.md`를 읽고 Generic Tool을 선택하게 한다.

### Web Tool 설계 요지

- `web_search`: DDGS, title/url/snippet/domain, Raw HTML 미투입
- `fetch_page`: HTTP 수집, script/style 제거, focus 기반 축소, 최대 문자 제한

xlsx에서 대용량 Tool Result가 Context 문제를 일으킨 경험을 반영했다.

---

## 7. Agent Loop

```text
messages → Gemma4 Chat
  → tool_calls? YES → Tool 실행 → role=tool 추가 → 다음 Turn
                 NO  → Final Answer
```

성공 Run에서는 Turn별 `model_elapsed_seconds`와 metrics의
`model_response_times_seconds` / `model_total_seconds`를 기록한다.

---

## 8. Ollama / Gemma4 설정

| 항목 | 값 |
|---|---|
| Model | `gemma4:31b` |
| Temperature | 0 |
| `num_ctx` | 65,536 |
| `num_predict` | 4,096 |
| HTTP read timeout | **600초** |

초기 300초에서 Skill ON Synthesis(~383초)가 실패해 측정 근거로 600초로 확장했다.
상세: [ollama-timeout-and-prompt-growth.md](ollama-timeout-and-prompt-growth.md)

---

## 9. Run Logging

```text
outputs/research-runs/run-xxxx/
├── request.md, run-config.json
├── response-*.json, messages.json, tool-calls.json
├── metrics.json, result.json, answer.md
```

Skill 활성·경로·SHA-256·Model·Tool·Token·Turn별 모델 시간·전체 시간·최종 답변을 남긴다.

---

## 10. 현재 지원 범위

이 문서의 본문은 B1 단일 세션 Runtime이다.
B2 모듈은 `src/research_b2/`에 따로 있다.

| Capability | B1 `research_run.py` | B2 `src/research_b2/` |
|---|---|---|
| Skill Discovery / Activation | O | O |
| Ollama Tool Calling / Agent Loop | O | Worker만 |
| 독립 Chat Session 병렬 조사 | X | O |
| Evidence Gate / Semantic Auditor | X | O |
| Evidence Pool / Replanner | X | O |
| 한 명령으로 Wave 전체 연결 | X | X |
| `scripts/` · `references/` on-demand | X | X |
| Context Compaction | X | X |

---

## 11. 현재 Runtime의 의미

이 파일은 Agent Skills 전체 Spec의 범용 Client가 아니다.

**B1 정의:** `SKILL.md`를 단일 Gemma4 세션에 넣어 Tool Calling과 행동 변화를 확인하는 Runtime.

```text
External SKILL.md → Gemma4 → Tool Selection → Actual Tool Execution → Behavior Change
```

B2는 같은 원칙을 유지한 채 세션을 나눈다.
Python이 연구 주제를 쓰지 않고, 공개 Skill과 Runtime 계약만 읽는다.
설명: [README.md](../README.md) · [docs/b2-runtime-contracts.md](../docs/b2-runtime-contracts.md)

후속으로 남은 것: [07-future-work.md](07-future-work.md)

### 참고

- [Agent Skills Specification](https://agentskills.io/specification)
- [Adding Skills Support](https://agentskills.io/client-implementation/adding-skills-support)
