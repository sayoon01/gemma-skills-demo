# 1. Agent Skills 개요

상위 문서: [README.md](../README.md)

공식: [agentskills.io](https://agentskills.io/home)  
내부 정리: [spec_skill.md](../spec_skill.md)  
구조 검사: [docs/skill-validation.md](../docs/skill-validation.md)

---

## 1.1 Agent Skills란

Agent Skills는 AI Agent에 특정 업무 수행 방법, 전문 지식 및 반복 가능한 Workflow를
제공하기 위한 경량 공개 포맷이다.

기본 단위는 하나의 Skill directory이며, 최소한 `SKILL.md` 파일을 포함한다.

```text
skill-name/
├── SKILL.md
├── scripts/
├── references/
├── assets/
└── ...
```

이 중 `SKILL.md`만 필수이며 나머지는 필요에 따라 포함할 수 있다.

Agent Skills는 특정 LLM 모델 자체의 기능이라기보다 **Agent Runtime이 읽고 사용할 수
있는 업무 지침 패키지** 형식으로 보는 것이 적절하다.

따라서 Claude뿐 아니라 해당 구조를 해석할 수 있는 Skill Loader와 Tool Runtime을
구현하면 다른 모델에서도 적용 가능성을 검증할 수 있다. 본 프로젝트의 Gemma4 실험이
바로 그 검증이다.

---

## 1.2 SKILL.md 규격

`SKILL.md`는 크게 두 부분으로 구성된다.

```markdown
---
name: example-skill
description: 이 Skill이 수행하는 작업과 언제 사용해야 하는지 설명
---

# Instructions

실제 Agent가 따라야 할 작업 절차...
```

### YAML Frontmatter 필드

| Field | 필수 여부 | 설명 |
|---|---|---|
| `name` | 필수 | Skill 이름. 디렉토리 이름과 일치해야 함 |
| `description` | 필수 | Skill 기능 및 활성화 조건 |
| `license` | 선택 | 라이선스 정보 |
| `compatibility` | 선택 | 실행환경, 패키지, 네트워크 등의 요구조건 |
| `metadata` | 선택 | 구현체에서 사용할 추가 메타데이터 |
| `allowed-tools` | 선택/실험적 | Skill에서 허용할 Tool 선언 |

현재 Agent Skills Specification에서는 `name`을 최대 64자로 제한하며 영문 소문자,
숫자, 하이픈 형식을 사용하도록 규정한다.

`description`은 최대 1,024자이며 단순한 기능 설명뿐 아니라 **어떤 요청에서 이 Skill을
사용해야 하는지**가 명확해야 한다.

### Markdown Body에 담는 내용

- 단계별 작업 방법
- 입력과 출력 형식
- 검증 방법
- 오류 처리 / 예외 상황
- Tool 사용 방법
- 참고자료를 읽는 시점

---

## 1.3 scripts / references / assets

### scripts/

Agent가 실행할 수 있는 Python, Bash, JavaScript 등의 실행 코드를 저장한다.

```text
scripts/
├── extract.py
├── validate.py
└── convert.sh
```

반복적이거나 결정론적으로 수행해야 하는 작업을 LLM이 매번 생성하는 대신 Script로
분리할 수 있다. Script 실행 가능 여부와 지원 언어는 Agent Runtime 구현에 따라 달라진다.

### references/

작업 수행 시 필요한 상세 참고문서를 저장한다.

```text
references/
├── REFERENCE.md
├── schema.md
└── domain-rules.md
```

Agent는 처음부터 모든 Reference를 Context에 넣는 것이 아니라 **필요한 자료만
선택적으로** 읽을 수 있다.

### assets/

결과 생성에 사용되는 정적 리소스를 저장한다.

```text
assets/
├── template.xlsx
├── report-template.docx
├── schema.json
└── example.png
```

템플릿, 이미지, 설정파일, Lookup table 등이 해당된다.

예: Anthropic `xlsx` — [vendor/anthropic-skills/skills/xlsx](../vendor/anthropic-skills/skills/xlsx)

---

## 1.4 Progressive Disclosure

Agent Skills에서 중요한 개념은 Progressive Disclosure이다.

모든 Skill 파일을 처음부터 Context에 넣는 것이 아니라 다음 단계로 필요한 정보만 로드한다.

```text
1. Discovery
   ↓
   name + description 확인

2. Activation
   ↓
   관련 Skill의 SKILL.md 전체 로드

3. Execution
   ↓
   필요한 scripts / references / assets만 추가 사용
```

이 방식은 Skill 수가 증가해도 모든 Skill 본문이 동시에 Context Window를 차지하지
않도록 하기 위한 구조이다.

본 프로젝트에서도 이를 참고하여 다음 Runtime을 구현하였다.

```text
Skill Discovery
  → Skill Activation
  → SKILL.md 주입
  → Tool Execution
```

현재 B1에서는 `scripts/` · `references/` · `assets/` on-demand Loader는 미구현이다.
상세 Runtime 범위: [03-gemma4-runtime.md](03-gemma4-runtime.md)
