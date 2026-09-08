# Re-plan Schema Repair

The previous research re-plan failed runtime schema validation.

This is a FORMAT/COMPLETENESS repair pass, not a new research-planning pass.

Preserve the previous plan's research intent and targeted gaps wherever possible. Do not perform research and do not invent evidence.

# Validation Errors

[
  "assignments[2] 허용되지 않은 field: queries_ko, source_priority_ko, source_priority_ko////: ",
  "assignments[2].needs_local_files가 bool이 아닙니다.",
  "assignments[3].objective가 비어 있습니다.",
  "assignments[3].queries는 비어 있지 않은 문자열 list여야 합니다.",
  "assignments[3].source_priority는 비어 있지 않은 문자열 list여야 합니다.",
  "assignments[3].needs_local_files가 bool이 아닙니다."
]

# Invalid Re-plan

{
  "needs_another_wave": true,
  "reason": "The majority of material claims (14/16) are currently single-source, and several critical gaps remain regarding specific hardware architectures, commercialization stages of key Korean companies (Samsung, Doosan), and the same-model mismatch for Unitree.com. Triangulation of core architectural shifts (VLA) and commercial deployment status of Figure/Optimus/Digit is required to meet the 'triangulated across at least 2 independent sources' rule.",
  "assignments": [
    {
      "assignment_id": "SG04",
      "title": "Triangulation of Physical AI Architecture and Commercial Status",
      "objective": "Cross-verify the shift to VLA models, the commercial deployment status of Tesla Optimus Gen 3, Figure 02/03, and Agility Digit, and resolve the conflict/mismatch regarding Unitree's $4k robot model name (G1 vs R1).",
      "queries": [
        "Tesla Optimus Gen 3 commercial deployment status 2026",
        "Figure AI Figure 02 03 commercial installation BMW Amazon",
        "Agility Robotics Digit commercial deployment Amazon",
        "Unitree G1 vs R1 humanoid robot price $4000",
        "Vision-Language-Action (VLA) models robotics foundation models 2024-2026"
      ],
      "source_priority": [
        "official",
        "industry"
      ],
      "needs_local_files": false
    },
    {
      "assignment_id": "SG05",
      "title": "Korean Physical AI Ecosystem and Infrastructure",
      "objective": "Identify specific Physical AI products or projects from Samsung Electronics and Doosan Robotics, and find detailed specifications for public robotics testbeds/certification infrastructure in South Korea.",
      "queries": [
        "삼성전자 자율작업형 로봇 AI-Native humanoid",
        "두산로보틱스 AI-Native 로봇 작업 수행 기술",
        "한국 공용 시험 인프라 로봇 성능 평가 장비 리스트",
        "South Korea public robotics testbed certification infrastructure specifications"
      ],
      "queries_ko": [
        "삼성전자 휴머노이드 로봇 개발 현황 2026",
        "두산로보틱스 AI 로봇 상용화 단계",
        "국가 로봇 시험 인증 센터 성능 평가 항목 및 장비 리스트"
      ],
      "source_priority": [
        "official",
        "official",
        "official",
        "official"
      ],
      "source_priority_ko": [
        "official",
        "official",
        "official",
        "official"
      ],
      "source_priority_ko////: ": ", "
    },
    {
      "assignment_id": "SG06",
      "title": "Technical Bottlenecks and Hardware Acceleration",
      "objective": " "
    }
  ]
}

# Exact Required Shape

{
  "needs_another_wave": true,
  "reason": "brief reason",
  "assignments": [
    {
      "assignment_id": "new unique id",
      "title": "targeted follow-up",
      "objective": "specific evidence gap to close",
      "queries": [
        "targeted query 1"
      ],
      "source_priority": [
        "official"
      ],
      "needs_local_files": false
    }
  ]
}

# Repair Rules

- Return one JSON object only.
- Use only these top-level fields: needs_another_wave, reason, assignments.
- Each assignment must contain exactly: assignment_id, title, objective, queries, source_priority, needs_local_files.
- Remove all other fields.
- Every title and objective must be non-empty.
- queries must be a non-empty list of strings.
- source_priority must be a non-empty list of strings.
- needs_local_files must be true or false.
- Return no more than 3 assignments.
- Preserve already valid assignment IDs when possible.
- Complete malformed or truncated assignments using the same unresolved evidence context and active Skill supplied in the system message.

