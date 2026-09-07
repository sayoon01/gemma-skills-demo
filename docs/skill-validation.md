# 스킬 기본 규격 검사 결과

## 검사 기준
- SKILL.md 존재
- YAML frontmatter의 name과 description 확인
- name 형식 및 부모 폴더 이름 일치
- description 길이 1024자 이하
- 지침 본문 존재

전체 Agent Skills 규격 인증이 아닌 기본 구조 검사이다.

## 대상 스킬 결과
- xlsx: 검사 통과, 본문 로딩 성공
- deep-research: 검사 통과, 본문 로딩 성공

## 전체 저장소 검사 중 발견한 사항
anthropic-skills의 claude-api 스킬은 description이 1068자로,
검사 상한 1024자를 44자 초과했다.

원본은 수정하지 않았으며, 이번 실행 대상인 xlsx와
deep-research는 각각의 폴더를 지정하여 별도로 검사했다.

## 검증 범위
위 결과는 파일 구조와 본문 로딩에 대한 확인이다.
실제 문서 생성, 검색 및 재계산 성공을 의미하지 않는다.
