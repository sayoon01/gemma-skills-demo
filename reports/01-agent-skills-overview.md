# 01. Agent Skills 개요

> 조사 기준일: 2026-09-07  
> 목적: Agent Skills의 공개 규격, `SKILL.md` 구조, Progressive Disclosure, 리소스 구성과 Runtime 관점의 의미를 정리한다.

상위 문서: [README.md](../README.md)  
공식: [agentskills.io](https://agentskills.io/home) · [Specification](https://agentskills.io/specification)  
내부: [spec_skill.md](../spec_skill.md) · [docs/skill-validation.md](../docs/skill-validation.md)

---

## 1. Agent Skills란

Agent Skills는 AI Agent에 특정 업무의 **절차적 지식(procedural knowledge)**, 도메인 지식, 반복 가능한 작업 순서를 제공하기 위한 공개 Skill 패키지 형식이다.

핵심은 특정 모델에 새 파라미터를 학습시키는 것이 아니라, Agent가 필요할 때 읽고 따를 수 있는 **파일 기반 업무 지침 패키지**를 제공하는 것이다.

공식 Agent Skills Specification에서 Skill은 최소 하나의 `SKILL.md`를 포함하는 디렉터리로 정의된다.

```text
skill-name/
├── SKILL.md          # 필수: metadata + instructions
├── scripts/          # 선택: 실행 코드
├── references/       # 선택: 참고 문서
├── assets/           # 선택: 템플릿/정적 리소스
└── ...
```

따라서 Agent Skills의 핵심을 다음처럼 볼 수 있다.

```text
Skill = Metadata + Instructions + Optional Resources
```

중요한 점은 Skill 자체가 LLM이나 Tool Runtime을 제공하는 것은 아니라는 것이다.
예를 들어 Skill에 "웹을 검색하고 원문을 읽어라"라고 적혀 있어도, Agent Runtime에 실제
Web Search / Fetch Tool이 없으면 해당 절차를 실행할 수 없다.

| 구분 | 역할 |
|---|---|
| `SKILL.md` | 무엇을, 어떤 절차로 수행해야 하는가 |
| Agent Runtime | 실제로 어떤 Tool과 실행 능력을 사용할 수 있는가 |

---

## 2. SKILL.md 기본 규격

공식 Specification에서 `SKILL.md`는 **YAML Frontmatter + Markdown Body**로 구성된다.

```markdown
---
name: data-analysis
description: Analyze tabular data and generate findings. Use when working with CSV or spreadsheet data.
---

# Instructions

1. Inspect the input data.
2. Validate columns and missing values.
3. Perform the requested analysis.
4. Report assumptions and evidence.
```

### 2.1 필수 Frontmatter

| Field | 필수 | 공개 표준 제약 |
|---|---|---|
| `name` | O | 1~64자, 소문자 영문·숫자·하이픈, 디렉터리명과 일치 |
| `description` | O | 1~1024자, Skill 기능과 **사용 시점**을 설명 |

`description`은 단순 설명이 아니라 Skill Trigger를 위한 핵심 Metadata이다.
Agent는 모든 Skill 본문을 처음부터 읽기보다 우선 `name`과 `description`을 보고
현재 요청에 맞는 Skill인지 판단할 수 있다.

### 2.2 선택 Frontmatter

| Field | 설명 |
|---|---|
| `license` | Skill 라이선스 또는 라이선스 파일 참조 |
| `compatibility` | 필요한 제품, 패키지, 네트워크 등 환경 요구사항 |
| `metadata` | 구현체가 사용할 추가 key-value 정보 |
| `allowed-tools` | 사전 허용 Tool 목록 (현재 Experimental) |

`allowed-tools`는 구현체마다 지원 여부가 다를 수 있다. 필드가 있다고 해서 모든
Agent Runtime에서 Tool이 자동 연결되는 것은 아니다.

---

## 3. Markdown Body

Frontmatter 이후 본문에는 Agent가 따라야 할 업무 지침을 작성한다.
형식 자체에 강제된 Section 구조는 없으며 다음을 포함할 수 있다.

- 단계별 수행 절차
- 입력/출력 규칙
- Tool 사용 절차
- 검증 기준 / 실패 처리 / 예외
- 좋은·나쁜 예시
- 참고 파일을 읽는 조건
- 산출물 형식

Skill은 한 줄 Prompt가 아니라 **재사용 가능한 Workflow Instruction**으로 보는 것이 적절하다.

---

## 4. scripts/

반복적이거나 결정론적 실행이 필요한 코드를 둔다.

```text
scripts/
├── extract.py
├── validate.py
└── convert.sh
```

적합한 예: PDF 페이지 회전, Excel 구조 검사, Schema validation, 파일 변환,
동일하게 반복해야 하는 계산.

장점:

- LLM이 매번 같은 코드를 새로 작성할 필요가 없다
- 결정론적 동작을 Script로 고정할 수 있다
- Context 사용량을 줄일 수 있다

어떤 언어 Script를 실행할 수 있는지는 **Agent Runtime 실행환경**에 따라 달라진다.

---

## 5. references/

필요할 때만 읽는 상세 문서를 둔다.

```text
references/
├── schema.md
├── api-reference.md
├── finance-rules.md
└── output-guidelines.md
```

`SKILL.md`에는 핵심 Workflow와 Navigation만 두고, 긴 API·규정·예제는 `references/`에
분리한다. Context Window가 제한되어 있기 때문이다.

---

## 6. assets/

최종 산출물에 쓰는 정적 리소스를 둔다.

```text
assets/
├── template.xlsx
├── report-template.docx
├── logo.png
├── schema.json
└── frontend-template/
```

`references/`가 Agent가 **읽기 위한 정보**에 가깝다면, `assets/`는 Agent가
**출력 생성에 활용하는 리소스**에 가깝다.

---

## 7. Progressive Disclosure

모든 Skill·리소스를 시작부터 Context에 넣지 않고, 필요한 수준만 단계적으로 공개한다.

| Level | 내용 | 목적 |
|---|---|---|
| 1. Metadata | `name` + `description` | 존재 파악·관련 Skill 선택 |
| 2. Instructions | 선택 Skill의 전체 `SKILL.md` | Activation 후 Workflow 로드 |
| 3. Resources | `scripts/` · `references/` · `assets/` | 실행 중 필요한 것만 |

```text
Discovery → Metadata → Activation → SKILL.md → Execution → Required Resource Only
```

설치된 Skill이 많아질수록 특히 중요하다. 본 프로젝트 Runtime도 Discovery → Activation
→ Tool Execution 흐름을 따른다 (Resource on-demand는 B1에서 미구현).

---

## 8. Agent Skills와 Agent Runtime의 관계

Skill 형식만으로 Agent가 완성되지 않는다. Host/Client는 최소한 다음을 가져야 한다.

- Skill Discovery / Activation / Instruction Injection
- Tool Binding / Execution / Result Feedback
- Agent Loop / Resource Access

호환성 평가는 두 질문을 구분해야 한다.

1. Skill 파일을 읽고 이해할 수 있는가?
2. Skill이 요구하는 Runtime Capability까지 제공할 수 있는가?

본 프로젝트의 Gemma4 실험도 이 두 단계를 분리해 검증하였다.

---

## 9. 표준과 제품별 구현 차이

공개 Specification은 공통 포맷을 정의하지만 실제 제품은 추가 제약을 둘 수 있다.
예: 공개 표준 `description` 최대 1024자 vs Claude Custom Skill의 더 짧은 제품별 가이드.

따라서 "표준을 따른 `SKILL.md`라면 모든 Client에서 완전히 동일하게 동작한다"는 의미가 아니다.

---

## 10. 본 프로젝트에서의 해석

공개 `SKILL.md`를 그대로 다운로드하고, 자체 Runtime이 이를 발견·활성화하여 Gemma4
실행 Context에 제공한 뒤, Gemma4가 Skill 지침에 따라 Tool을 선택하고 반복 업무를
수행할 수 있는지 검증한다.

특정 Skill Workflow를 Python에 다시 하드코딩하는 방식은 검증 목표와 다르다.

```text
Public Skill → Generic Skill Loader → Gemma4 → Generic Tools → Agent Loop
```

---

## 11. 요약

| 구성 | 역할 |
|---|---|
| `SKILL.md` | Metadata + 핵심 Workflow |
| `scripts/` | 반복적·결정론적 실행 코드 |
| `references/` | 필요 시 읽는 상세 참고자료 |
| `assets/` | 최종 결과 생성용 정적 리소스 |
| Progressive Disclosure | 필요한 정보만 단계적으로 Context에 제공 |
| Agent Runtime | Skill을 Tool/파일/Agent 실행 능력과 연결 |

Agent Skills를 새 모델에 적용하려면 `SKILL.md`를 Prompt에 붙이는 것에서 끝나지 않고,
Skill이 요구하는 Capability를 연결하는 Runtime이 필요하다.

### 참고

- [Agent Skills Specification](https://agentskills.io/specification)
- [Adding Skills Support to an Agent](https://agentskills.io/client-implementation/adding-skills-support)
- [Anthropic Public Skills](https://github.com/anthropics/skills)
- [OpenAI Codex Skills](https://developers.openai.com/codex/skills)
