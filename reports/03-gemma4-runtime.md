# 3. Gemma4 적용 구조 (Runtime)

상위 문서: [README.md](../README.md)

관련 코드:

- [src/skill_loader.py](../src/skill_loader.py)
- [src/ollama_client.py](../src/ollama_client.py)
- [run.py](../run.py)
- [research_run.py](../research_run.py)
- [src/web_tools.py](../src/web_tools.py)

---

## 3.1 목적

Gemma4/Ollama에는 Claude Code와 동일한 Skill Runtime이 기본 제공되지 않는다.
본 프로젝트에서는 Agent Skills의 핵심 실행 과정을 직접 구현하였다.

```text
Public Skill Repository
        │
        ▼
   Skill Loader
        │
        ├── Discovery
        ├── Validation
        └── Activation
        │
        ▼
     SKILL.md
        │
        ▼
 Gemma4 System Context
        │
        ▼
     Gemma4:31b
        │
        ▼
   Tool Selection
        │
        ▼
   Runtime Tool
        │
        ▼
   Tool Result
        │
        └──────────────┐
                       ▼
                    Gemma4
                       │
                 반복 Agent Loop
                       │
                       ▼
                  Final Answer
```

---

## 3.2 Skill Loader

`src/skill_loader.py`가 공개 Skill directory를 탐색한다.

현재 검색 위치:

- `vendor/anthropic-skills/skills/`
- `vendor/community-skills/`

Loader는 `SKILL.md`를 발견한 후 YAML Frontmatter를 읽어 `name`, `description` 등
기본 메타데이터를 검사한다.

현재 구현에서 수행하는 작업:

- Skill directory 검색
- `SKILL.md` 확인
- YAML parsing
- name / description validation
- 중복 Skill 검사
- SHA-256 기록
- Skill Activation

---

## 3.3 Skill Activation

사용자가 `--skill deep-research` 와 같이 Skill을 지정하면 해당 Skill의 전체
`SKILL.md` Body를 읽는다. 이후 Gemma4의 System Prompt에 활성 Skill을 포함한다.

```text
Available Skills
      ↓
Metadata Discovery
      ↓
deep-research 선택
      ↓
전체 SKILL.md Load
      ↓
Gemma4 Context에 추가
```

이는 Agent Skills Progressive Disclosure 중 Discovery → Activation 단계를
자체 Runtime에서 재현한 것이다.

---

## 3.4 Tool Binding

`SKILL.md`는 업무 방법을 설명하지만 실제 Tool 자체를 생성하지는 않는다.

예를 들어 Deep Research Skill이 웹 검색 → 원문 확인 → 복수 출처 비교를 요구한다면
Runtime에는 실제로 사용할 수 있는 `web_search`, `fetch_page` Tool이 있어야 한다.

본 프로젝트에서는 Ollama의 Tool Calling 형식으로 Tool Schema를 모델에 제공한다.
Gemma4는 Skill 지침과 사용자 요청을 참고하여 필요한 Tool을 선택한다.

| 요소 | 의미 |
|---|---|
| `SKILL.md` | 무엇을 어떻게 해야 하는가 |
| Tool | 실제로 무엇을 실행할 수 있는가 |

---

## 3.5 Agent Loop

실행기는 Gemma4 응답의 `tool_calls`를 확인한다.

```text
User Request
    ↓
Gemma4
    ↓
tool_calls 존재?
   ├── YES → Tool 실행 → 결과를 messages에 추가 → Gemma4 재호출
   └── NO  → Final Answer
```

Deep Research 실험에서는 실제로 다음과 같은 Loop가 수행되었다.

```text
Gemma4 → web_search → web_search → fetch_page → (추가 검색) → 최종 분석
```

성공 Run에서는 Turn별 모델 응답 시간도 `_runtime.model_elapsed_seconds` 및
`metrics.json`의 `model_response_times_seconds` / `model_total_seconds`로 기록한다.

Ollama HTTP read timeout은 `(10, 600)`으로 설정되어 있다
([reports/ollama-timeout-and-prompt-growth.md](ollama-timeout-and-prompt-growth.md)).

---

## 3.6 현재 구현 범위

| 기능 | 상태 |
|---|---|
| SKILL.md Discovery | O |
| Skill Validation | O |
| Skill Activation | O |
| System Prompt Injection | O |
| Ollama Tool Calling | O |
| Tool Result Feedback | O |
| Multi-turn Agent Loop | O |
| Run Logging | O |
| scripts/ 자동 실행 | X |
| references/ On-demand Loader | X |
| assets/ Resource Loader | X |
| allowed-tools 자동 Binding | X |
| Parallel Sub-agent | X |
| Multi-wave Research | X |
| Context Compaction | X |

따라서 현재 구현은 Agent Skills **전체 Runtime 호환 구현이 아니라**,
`SKILL.md` 중심의 **핵심 Compatibility 검증 Runtime**이다.

후속: [07-future-work.md](07-future-work.md)
