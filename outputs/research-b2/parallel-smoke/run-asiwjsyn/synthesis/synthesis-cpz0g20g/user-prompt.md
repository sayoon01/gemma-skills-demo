# Original Research Request

자율작업형 피지컬AI 로봇의 기술 동향 분석서를 한국어로 작성해 주세요.

조사 범위:
- 2024년부터 조사 시점까지 공개된 자료
- 이동 플랫폼, 자율주행, 작업 수행, 온디바이스 AI
- 국내외 주요 기업과 대표 제품
- 연구 단계와 실제 판매·현장 도입 단계를 구분

분석 항목:
1. 기술 개요와 구성
2. 주요 기업·제품별 기능 비교
3. 핵심 기술의 발전 방향
4. 상용화 병목과 시험·검증 요구사항
5. 공용 시험 인프라 구축에 대한 시사점

제조사 공식 문서, 연구논문, 표준기관 자료를 우선 사용하세요.
확인된 사실과 분석자의 추론을 구분하고 주요 주장에 출처를 달아주세요.
최종 결과를 reports/physical-ai-trends.md에 저장해 주세요.


# Validated Research Packet

{
  "original_user_task": "자율작업형 피지컬AI 로봇의 기술 동향 분석서를 한국어로 작성해 주세요.\n\n조사 범위:\n- 2024년부터 조사 시점까지 공개된 자료\n- 이동 플랫폼, 자율주행, 작업 수행, 온디바이스 AI\n- 국내외 주요 기업과 대표 제품\n- 연구 단계와 실제 판매·현장 도입 단계를 구분\n\n분석 항목:\n1. 기술 개요와 구성\n2. 주요 기업·제품별 기능 비교\n3. 핵심 기술의 발전 방향\n4. 상용화 병목과 시험·검증 요구사항\n5. 공용 시험 인프라 구축에 대한 시사점\n\n제조사 공식 문서, 연구논문, 표준기관 자료를 우선 사용하세요.\n확인된 사실과 분석자의 추론을 구분하고 주요 주장에 출처를 달아주세요.\n최종 결과를 reports/physical-ai-trends.md에 저장해 주세요.\n",
  "research_state": {
    "summary": {
      "wave_count": 2,
      "wave1_accepted_claim_count": 16,
      "wave2_accepted_claim_count": 13,
      "wave2_novel_claim_count": 12,
      "running_claim_count": 28,
      "physical_claim_node_count": 29,
      "relation_edge_count": 13,
      "same_count": 1,
      "extension_count": 0,
      "contradiction_count": 1,
      "cumulative_verified_source_count": 23,
      "single_source_claim_count": 26,
      "pending_independence_claim_count": 2,
      "unsupported_claim_count": 3,
      "gap_count": 14,
      "triangulated_claim_count": 1,
      "independence_family_count": 3,
      "independence_unknown_family_count": 2
    },
    "novelty": {
      "novel_claim_counts": [
        16,
        12
      ],
      "running_claim_counts": [
        16,
        28
      ],
      "novelty_ratios_running_total": [
        1.0,
        0.42857142857142855
      ],
      "wave2_matcher_ratio_new_claims": 0.9230769230769231,
      "measurement_note": "wave2_matcher_ratio_new_claims measures novel claims / accepted claims in Wave 2. novelty_ratios_running_total measures new materially distinct findings / running cumulative claim total and is kept separately for Skill convergence evaluation."
    },
    "stop": {
      "stage": "B2-9",
      "created_at": "2026-09-10T00:50:02.539680+00:00",
      "converged": false,
      "stop_reason": "user_stop",
      "wave_count": 2,
      "running_claim_count": 28,
      "novel_claim_counts": [
        16,
        12
      ],
      "novelty_ratios_running_total": [
        1.0,
        0.42857142857142855
      ],
      "pending_independence_claim_count": 2,
      "unsupported_claim_count": 3,
      "gap_count": 14,
      "note": "Research was intentionally stopped after Wave 2 by user instruction. This is an operational user stop, not semantic convergence."
    }
  },
  "validated_claims": [
    {
      "claim_ref": "SG01:C001",
      "wave": 1,
      "claim": "2024-2026년 자율작업형 로봇의 핵심 아키텍처는 기존의 작업별 정책 학습에서 시각-언어-행동(VLA, Vision-Language-Action) 모델 기반의 파운데이션 모델 체계로 전환되었다.",
      "runtime_status": "TRIANGULATED",
      "verified_evidence_count": 2,
      "family_resolution": {
        "family_ref": "SG01:C001",
        "final_verdict": "TRIANGULATED",
        "resolved_status": "TRIANGULATED",
        "reason": "The claim is confirmed independent via the pairing of the academic paper (S001) with either of the industry sources."
      },
      "evidence": [
        {
          "evidence_id": "C001-E001",
          "citation_ref": "SRC011",
          "support_reason": "Explicitly states the architectural shift of 2025-2026 is the introduction of foundation model backbones (VLMs pretrained on internet-scale data) paired with action generation, defining the VLA paradigm.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "The architectural shift that defines 2025–2026 is the introduction of foundation model backbones into the policy — specifically, large Vision-Language Models (VLMs) pretrained on internet-scale data — paired with action generation modules capable of producing smooth, continuous motor trajectories. This is the Vision-Language-Action (VLA) paradigm"
        },
        {
          "evidence_id": "C001-E002",
          "citation_ref": "SRC020",
          "support_reason": "Confirms VLA models (like RT-2) allow commanding robots with natural language to complete previously unseen tasks.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "Breakthroughs in Robot Foundation Models are the key driving force behind Physical AI's accelerated deployment — RT-2 and other Vision-Language-Action models (VLA) achieved, for the first time, \"commanding robots with natural language to complete previously unseen tasks\""
        }
      ]
    },
    {
      "claim_ref": "SG01:C002",
      "wave": 1,
      "claim": "NVIDIA의 GR00T N1.6 아키텍처는 SigLIP 비전 인코더와 네이티브 해상도 지원 VLM을 통해 공간 추론 및 객체 정밀 제어 능력을 향상시켰다.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C002-E001",
          "citation_ref": "SRC011",
          "support_reason": "The text explicitly links GR00T N1.6's upgrade to native resolution support (avoiding padding) to improved object localization and spatial reasoning, and mentions the SigLIP vision transformer.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "In GR00T N1.6, the VLM was upgraded to a variant of Cosmos-Reason-2B with native resolution support — meaning the vision encoder processes images at their original aspect ratio rather than padding them to a square. This is architecturally significant: padding introduces artificial boundaries... degrading object localization and spatial reasoning."
        }
      ]
    },
    {
      "claim_ref": "SG01:C003",
      "wave": 1,
      "claim": "작업 수행(Manipulation) 기술은 단순한 파지(Grasping) 예측에서 '파지-배치 시너지(Grasp-for-Placement Synergy)' 기반의 작업 인식형 파지 추정으로 발전하고 있다.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C003-E001",
          "citation_ref": "SRC021",
          "support_reason": "The source explicitly mentions Samsung's task-aware grasp estimation patents (2024-2026) and the concept of 'Grasp-for-Placement Synergy' where downstream placement geometry informs grasp selection.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "Samsung's task-aware grasp estimation patents (US, 2024–2026) demonstrate that grasp selection should be informed by the downstream placement geometry, linking pick-and-place into a unified neural planning problem. This reduces re-grasp events and improves cycle time."
        }
      ]
    },
    {
      "claim_ref": "SG01:C004",
      "wave": 1,
      "claim": "온디바이스 AI 분야에서는 클라우드 없이 기기 자체에서 학습이 가능한 '적응형 AI(Adaptive AI)' 및 연속 학습(Continual Learning) 가속 기술이 개발되었다.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C004-E001",
          "citation_ref": "SRC018",
          "support_reason": "The article confirms the development of an NPU structure based on 2D Systolic Arrays and Microsoft MX multi-precision computing to realize Adaptive AI/Continual Learning on-device without cloud resources.",
          "source_type": "official",
          "tier": 2,
          "excerpt": "적응형 AI의 기반 기술인 ‘연속 학습’ 가속을 위한 NPU(신경망처리장치) 구조 및 온디바이스 소프트웨어 시스템을 최초 개발... 효율적 병렬 프로세싱을 위해 2차원 시스톨릭 배열(Systolic Array) 구조를 기반으로 한다."
        }
      ]
    },
    {
      "claim_ref": "SG01:C005",
      "wave": 1,
      "claim": "물리적 AI 로봇의 실시간 제어를 위해 하드웨어 가속기(NVIDIA Blackwell 등)의 정밀도 최적화와 GPU 파티셔닝 기술이 적용되고 있다.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C005-E001",
          "citation_ref": "SRC011",
          "support_reason": "The text explicitly mentions NVFP4 providing 7.5x higher compute than Orin and the use of MIG to partition the GPU into slices for the perception stack, VLM System 2, and DiT System 1.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "The Blackwell architecture introduces NVFP4 as a first-class inference datatype, enabling 7.5x higher effective AI compute compared to the AGX Orin... Multi-Instance GPU (MIG) support allows the Blackwell GPU to be partitioned into up to seven independent compute slices, enabling simultaneous execution of the perception stack, the VLM System 2 pass, and the DiT System 1 pass"
        }
      ]
    },
    {
      "claim_ref": "SG02:C001",
      "wave": 1,
      "claim": "Tesla Optimus Gen 3 is currently in limited production and deployed within Tesla's own factories for tasks such as bin picking, kitting, and basic assembly.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C001-E001",
          "citation_ref": "SRC004",
          "support_reason": "The source text explicitly states: 'The Gen 3 unit, now in limited production at Tesla’s Fremont facility' and 'Optimus units are primarily deployed inside Tesla factories—performing bin picking, kitting, and basic assembly tasks.'",
          "source_type": "industry_analysis",
          "tier": 4,
          "excerpt": "The Gen 3 unit, now in limited production at Tesla’s Fremont facility... Optimus units are primarily deployed inside Tesla factories—performing bin picking, kitting, and basic assembly tasks."
        }
      ]
    },
    {
      "claim_ref": "SG02:C002",
      "wave": 1,
      "claim": "Figure AI's Figure 02 and 03 are in the commercial deployment stage, with active installations at BMW's Spartanburg plant and Amazon Robotics fulfillment centers.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C002-E001",
          "citation_ref": "SRC004",
          "support_reason": "Confirms Figure 02 installations at BMW’s Spartanburg plant and Amazon Robotics fulfillment centers.",
          "source_type": "industry_analysis",
          "tier": 4,
          "excerpt": "Figure 02 leads in real-world deployments, with confirmed installations at BMW’s Spartanburg plant, Amazon Robotics fulfillment centers, and several automotive Tier 1 suppliers."
        }
      ]
    },
    {
      "claim_ref": "SG02:C003",
      "wave": 1,
      "claim": "Agility Robotics' Digit is in the commercial deployment stage, specifically deployed at Amazon.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C003-E001",
          "citation_ref": "SRC003",
          "support_reason": "The text explicitly states 'Agility deploying Digit at Amazon'.",
          "source_type": "industry_analysis",
          "tier": 5,
          "excerpt": "Agility deploying Digit at Amazon"
        }
      ]
    },
    {
      "claim_ref": "SG02:C004",
      "wave": 1,
      "claim": "Boston Dynamics' electric Atlas is primarily a research platform, though it is being piloted in Hyundai Motor Group factories for moving automotive parts.",
      "runtime_status": "MULTI_SOURCE_PENDING_INDEPENDENCE",
      "verified_evidence_count": 2,
      "family_resolution": {
        "family_ref": "SG02:C004",
        "final_verdict": "UNKNOWN",
        "resolved_status": "MULTI_SOURCE_PENDING_INDEPENDENCE",
        "reason": "The sources are likely dependent on a single common origin (CES 2026 public demonstration), and no separate primary provenance is established."
      },
      "evidence": [
        {
          "evidence_id": "C004-E001",
          "citation_ref": "SRC004",
          "support_reason": "Confirms 'Atlas remains a research platform'.",
          "source_type": "industry_analysis",
          "tier": 4,
          "excerpt": "Atlas remains a research platform, though Boston Dynamics has hinted at a commercial Atlas variant for 2027."
        },
        {
          "evidence_id": "C004-E002",
          "citation_ref": "SRC014",
          "support_reason": "The Korean text confirms Atlas is 'actually being pilot-operated in Hyundai Motor factories' (현대차 공장에서 실제로 시범 운영 중) and moving automotive parts (자동차 부품을 직접 옮기는 장면).",
          "source_type": "industry_analysis",
          "tier": 5,
          "excerpt": "보스턴다이내믹스 ‘아틀라스’가 자동차 부품을 직접 옮기는 장면... 현대차 공장에서 실제로 시범 운영 중인 모습이더군요."
        }
      ]
    },
    {
      "claim_ref": "SG02:C005",
      "wave": 1,
      "claim": "Rainbow Robotics and Tomorrow Robotics have entered a joint development phase to create 'AI-Native' humanoid robots using Robot Foundation Models (RFM) and AI Agents.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C005-E001",
          "citation_ref": "SRC019",
          "support_reason": "The source explicitly details the MOU for 'AI-Native humanoid robot' development, specifically mentioning the use of 'Robot Foundation Model (RFM)' and 'AI Agent'.",
          "source_type": "official",
          "tier": 1,
          "excerpt": "투모로 로보틱스는 지난 21일 레인보우로보틱스와 ‘피지컬 AI 기반 로봇 연구개발 및 사업 협력을 위한 업무협약(MOU)’을 체결했다고 23일 밝혔다... 레인보우로보틱스의 로봇 하드웨어 기술과 투모로 로보틱스의 AI·소프트웨어 기술을 결합해 실제 산업 현장에서 활용할 수 있는 AI-Native 휴머노이드 로봇을 공동 개발하는 것이 핵심이다."
        }
      ]
    },
    {
      "claim_ref": "SG03:C001",
      "wave": 1,
      "claim": "Software architecture and integration have become a primary technical bottleneck for Physical AI, with 27% of developers citing it as their biggest performance constraint, surpassing hardware constraints (16%).",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C001-E001",
          "citation_ref": "SRC013",
          "support_reason": "The content explicitly states that 27% of developers cite software architecture and integration as the biggest bottleneck compared to 16% for hardware.",
          "source_type": "industry",
          "tier": 4,
          "excerpt": "almost one in three developers (27%) cite software architecture and integration as their biggest performance bottleneck, compared to just 16% who cite hardware constraints."
        }
      ]
    },
    {
      "claim_ref": "SG03:C002",
      "wave": 1,
      "claim": "There is a 'Determinism Disconnect' in robotics development where 95% of developers require deterministic, real-time execution for safety, yet 91% still rely on general-purpose operating systems (GPOS) like Linux for some real-time or safety-critical workloads.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C002-E001",
          "citation_ref": "SRC013",
          "support_reason": "The text explicitly mentions the 95% and 91% figures in the 'Determinism Disconnect' section.",
          "source_type": "industry",
          "tier": 4,
          "excerpt": "An overwhelming 95% of developers state that deterministic, real-time execution is essential... 91% of development teams still rely on general-purpose operating systems (GPOS), such as Linux, to run at least some real-time or safety-critical workloads."
        }
      ]
    },
    {
      "claim_ref": "SG03:C003",
      "wave": 1,
      "claim": "The commercialization of Physical AI is hindered by a 'Certification Wall,' with 66% of developers reporting project delays due to industry certification requirements, particularly cybersecurity (ISO/SAE 21434) and functional safety (ISO 10218) standards.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C003-E001",
          "citation_ref": "SRC013",
          "support_reason": "The text explicitly links the 66% project delay rate to certification requirements and names the specific ISO standards.",
          "source_type": "industry",
          "tier": 4,
          "excerpt": "Two-thirds (66%) of developers report experiencing project delays specifically due to industry certification requirements... cybersecurity standards (such as ISO/SAE 21434) and functional safety standards (like ISO 10218), which are cited as the most challenging to navigate"
        }
      ]
    },
    {
      "claim_ref": "SG03:C004",
      "wave": 1,
      "claim": "Physical AI development is bottlenecked by three interlocking factors: heterogeneity, the Sim-to-Real Gap, and data scarcity, with the primary challenge shifting from equipment costs to the availability of skilled operators and data quality.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C004-E001",
          "citation_ref": "SRC009",
          "support_reason": "The content explicitly lists the three challenges and states the bottleneck has shifted from 'equipment' to 'skilled operators and data quality'.",
          "source_type": "industry",
          "tier": 4,
          "excerpt": "The three challenges... heterogeneity, the Sim-to-Real Gap, and scarcity — remain the bottleneck... the bottleneck has shifted from 'equipment' to 'skilled operators and data quality.'"
        }
      ]
    },
    {
      "claim_ref": "SG03:C005",
      "wave": 1,
      "claim": "In South Korea, the commercialization of mobile robots is hindered by fragmented regulations across various laws (e.g., Building Act, Personal Information Protection Act), leading to the proposal of a 'Robot Special Law' to provide integrated support for demonstration, commercialization, and safety management.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C005-E001",
          "citation_ref": "SRC015",
          "support_reason": "The text confirms the representative proposal of the law and explicitly lists the fragmented laws (건축법, 공동주택관리법, 개인정보보호법).",
          "source_type": "industry",
          "tier": 4,
          "excerpt": "활용 관련 규정도 건축법·공동주택관리법·개인정보보호법 등에 흩어져 있어 통합적인 제도 기반이 필요하다는 지적이 제기되어 왔다."
        }
      ]
    },
    {
      "claim_ref": "SG03:C006",
      "wave": 1,
      "claim": "There is a critical need for public testing and certification infrastructure to reduce overseas dependence and support the entire lifecycle of robot development, from performance evaluation to risk assessment.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C006-E001",
          "citation_ref": "SRC022",
          "support_reason": "The text explicitly states that domestic certification infrastructure was lacking, leading to high overseas dependence, and describes KTL's new center as a solution.",
          "source_type": "official",
          "tier": 1,
          "excerpt": "사람과 함께 운용된다는 특성상 제품과 시스템에 대한 안전인증이 필수적이지만, 그동안 국내 시험인증 기반 부족으로 해외 의존도가 높았다."
        }
      ]
    },
    {
      "claim_ref": "SG04:C001",
      "wave": 2,
      "claim": "The robotics industry is shifting toward Vision-Language-Action (VLA) models to enable general-purpose capabilities.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": {
        "family_ref": "SG01:C001",
        "final_verdict": "TRIANGULATED",
        "resolved_status": "TRIANGULATED",
        "reason": "The claim is confirmed independent via the pairing of the academic paper (S001) with either of the industry sources."
      },
      "evidence": [
        {
          "evidence_id": "C001-E001",
          "citation_ref": "SRC005",
          "support_reason": "The retrieved content explicitly states that VLA models aim to learn policies that generalize across diverse tasks, objects, embodiments, and environments by unifying vision, language, and action data at scale.",
          "source_type": "academic_paper",
          "tier": 2,
          "excerpt": "By unifying vision, language, and action data at scale... VLA models aim to learn policies that generalise across diverse tasks, objects, embodiments, and environments."
        }
      ]
    },
    {
      "claim_ref": "SG04:C002",
      "wave": 2,
      "claim": "Tesla Optimus Gen 3 entered mass production in January 2026 but is not yet available for external commercial sale.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C002-E001",
          "citation_ref": "SRC012",
          "support_reason": "The content explicitly mentions mass production commenced January 21, 2026, at Fremont and specifies that these are 'production' in the manufacturing sense, not the commercial sales sense.",
          "source_type": "industry_blog",
          "tier": 4,
          "excerpt": "January 21, 2026: Gen 3 mass production commences at Fremont, California... The units being produced and tested in Fremont are 'production' in the manufacturing sense, not yet in the commercial sales sense."
        }
      ]
    },
    {
      "claim_ref": "SG04:C003",
      "wave": 2,
      "claim": "Tesla Optimus Gen 3 features a significant architectural upgrade in its hands compared to Gen 2.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C003-E001",
          "citation_ref": "SRC012",
          "support_reason": "The content details the shift to a tendon-driven biomimetic design with actuators in the forearm, and lists 50 actuators/22 DoF for Gen 3 vs ~28 actuators/11 DoF for Gen 2.",
          "source_type": "industry_blog",
          "tier": 4,
          "excerpt": "Gen 3 hands — 50 actuators vs ~28 total in Gen 2; 22 DoF per hand vs 11 in Gen 2 — a 4.5× leap"
        }
      ]
    },
    {
      "claim_ref": "SG05:C001",
      "wave": 2,
      "claim": "Samsung Electronics is developing an 'AI-Native' humanoid robot with a target debut at CES 2027 (January 2027).",
      "runtime_status": "MULTI_SOURCE_PENDING_INDEPENDENCE",
      "verified_evidence_count": 2,
      "family_resolution": {
        "family_ref": "SG05:C001",
        "final_verdict": "UNKNOWN",
        "resolved_status": "MULTI_SOURCE_PENDING_INDEPENDENCE",
        "reason": "The high degree of overlap in specific dates and targets suggests a common primary source (press release), making independence unverified."
      },
      "evidence": [
        {
          "evidence_id": "C001-E001",
          "citation_ref": "SRC017",
          "support_reason": "Explicitly states Samsung started a next-gen intelligent humanoid project on 2026-09-07 with a goal to reveal it at CES 2027 in Las Vegas.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "삼성전자가 2026년 9월 7일 차세대 지능형 휴머노이드(인간형 로봇) 개발 프로젝트를 본격화하고 2027년 1월 미국 라스베이거스에서 열리는 세계 최대 전자·정보기술 전시회 CES 2027 공개를 목표로 실무 작업에 착수했다."
        },
        {
          "evidence_id": "C001-E002",
          "citation_ref": "SRC010",
          "support_reason": "Confirms the goal to debut at CES 'next year' (relative to Sept 2026) and explicitly mentions building a custom humanoid optimized for AI algorithms from the initial design stage.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "[Samsung Humanoid to Debut at CES Next Year] ... build a custom humanoid optimized for AI algorithms from the initial design stage"
        }
      ]
    },
    {
      "claim_ref": "SG05:C002",
      "wave": 2,
      "claim": "Samsung Electronics utilizes its own semiconductor and appliance factories as 'data factories' to collect vast amounts of physical data for humanoid training.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C002-E001",
          "citation_ref": "SRC010",
          "support_reason": "Explicitly mentions a 'data factory' under construction at sites including the Gumi plant and states Samsung can use its semiconductor, smartphone, and home appliance production lines as a huge data collection base.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "Technology developed there is applied directly to a \"data factory\" under construction at sites including the Gumi plant for validation. ... Samsung, which operates semiconductor, smartphone and home appliance production lines around the world, can use its own factories as a huge data collection base."
        }
      ]
    },
    {
      "claim_ref": "SG05:C003",
      "wave": 2,
      "claim": "Doosan Robotics has launched 'Scan & Go', an AI-based industrial robot solution that performs tasks like sanding and grinding on large structures without blueprints.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C003-E001",
          "citation_ref": "SRC023",
          "support_reason": "Confirms 'Scan & Go' is an AI robot solution for tasks like sanding and grinding on large structures without blueprints, achieving 0.1mm precision and PLe, Cat4 safety compliance.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "스캔앤고는 협동로봇 팔과 자율이동로봇(AMR)을 결합한 플랫폼에 물리정보 기반 AI와 3D 비전 기술을 적용한 산업용 AI 로봇 솔루션이다. ... 0.1mm 수준의 작업 정밀도를 구현했다. ... 산업용 안전 기준인 PLe, Cat4도 충족했다."
        }
      ]
    },
    {
      "claim_ref": "SG05:C004",
      "wave": 2,
      "claim": "Doosan Robotics is collaborating with NVIDIA to develop an 'Agentic Robot O/S' and aims to release industrial humanoid products by 2028.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C004-E001",
          "citation_ref": "SRC016",
          "support_reason": "Explicitly mentions the collaboration with NVIDIA, the development of the 'Agentic Robot O/S', and the goal to sequentially reveal industrial humanoid products by 2028.",
          "source_type": "industry",
          "tier": 2,
          "excerpt": "두산로보틱스가 엔비디아와 피지컬 인공지능(AI) 기반 로봇 솔루션 개발 협력에 나선다. ... 2028년에는 산업용 휴머노이드 제품을 순차적으로 공개한다는 목표다. ... 로봇 전용 실행 소프트웨어 '에이전틱 로봇 운영체제(Agentic Robot O/S)'와 엔비디아의 AI·로보틱스 시뮬레이션·학습 인프라를 연계"
        }
      ]
    },
    {
      "claim_ref": "SG06:C001",
      "wave": 2,
      "claim": "Real-time VLA (Vision-Language-Action) inference for robotics targets a latency of 10 to 100 milliseconds (10 Hz to 100 Hz) to align with visual signal ingestion rates from standard RGB cameras (24-60 Hz).",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C001-E001",
          "citation_ref": "SRC008",
          "support_reason": "The text directly supports the relationship between camera frame rates and the defined VLA inference frequency targets.",
          "source_type": "academic_paper",
          "tier": 2,
          "excerpt": "Given that standard RGB camera frame rates typically range from 24 to 60 Hz, we define a 10 Hz inference frequency as... What combinations of models and systems are required to support VLA inference at rates from 10 Hz up to and beyond 100 Hz"
        }
      ]
    },
    {
      "claim_ref": "SG06:C003",
      "wave": 2,
      "claim": "The Deltoris framework accelerates diffusion-based VLA inference using a hardware-software co-design that employs temporal-aware bit-sparsity to compute only differences between consecutive inputs and speculative inference to amortize data loading.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C003-E001",
          "citation_ref": "SRC007",
          "support_reason": "The retrieved content contains all technical components of the claim including the specific algorithm names and hardware architecture.",
          "source_type": "academic_paper",
          "tier": 2,
          "excerpt": "we propose a temporal-aware bit-sparsity algorithm that computes only the differences between consecutive inputs... we propose a speculative inference technique, which amortizes data loading across multiple control steps. Lastly, to support these techniques, we co-design a dedicated accelerator with customized 1D systolic bit-serial PE arrays"
        }
      ]
    },
    {
      "claim_ref": "SG06:C004",
      "wave": 2,
      "claim": "VLA-RAIL addresses VLA inference bottlenecks by implementing an asynchronous inference linker that uses a Trajectory Smoother (polynomial fitting) and a Chunk Fuser to ensure continuity in position, velocity, and acceleration.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C004-E001",
          "citation_ref": "SRC006",
          "support_reason": "The retrieved text directly supports the implementation of the Smoother and Fuser and their specific goals for continuity.",
          "source_type": "academic_paper",
          "tier": 2,
          "excerpt": "a Trajectory Smoother that effectively filters out the noise and jitter in the trajectory of one action chunk using polynomial fitting and a Chunk Fuser that seamlessly align the current executing trajectory and the newly arrived chunk"
        }
      ]
    },
    {
      "claim_ref": "SG06:C005",
      "wave": 2,
      "claim": "Humanoid actuator energy efficiency is constrained by a trade-off between battery chemistries: Lithium Iron Phosphate (LFP) provides better thermal stability and cycle life, while Nickel Cobalt Aluminum (NCA) offers higher energy density.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C005-E001",
          "citation_ref": "SRC001",
          "support_reason": "The text explicitly confirms the specific properties of LFP vs NCA chemistries in the context of humanoid power systems.",
          "source_type": "industry_blog",
          "tier": 4,
          "excerpt": "The trade-off between lithium iron phosphate chemistry (LFP) and nickel cobalt aluminum chemistry (NCA) is not academic. LFP offers better thermal stability and cycle life. NCA offers higher energy density."
        }
      ]
    },
    {
      "claim_ref": "SG06:C006",
      "wave": 2,
      "claim": "Rigid actuator systems (e.g., harmonic drives and brushless motors) are energy-inefficient because they require continuous power input to maintain position and generate force, whereas soft actuators can reduce power draw by passively storing and releasing energy.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C006-E001",
          "citation_ref": "SRC002",
          "support_reason": "The retrieved content directly supports the energy efficiency comparison between rigid and soft actuators.",
          "source_type": "industry_blog",
          "tier": 4,
          "excerpt": "Rigid actuator systems, like the harmonic drives and brushless motors used in most humanoid robots, require continuous power input to hold position and generate force. Soft actuators can exploit material compliance to absorb and redirect energy more naturally."
        }
      ]
    },
    {
      "claim_ref": "SG06:C007",
      "wave": 2,
      "claim": "Thermal management is a primary bottleneck for humanoid actuators in production; compact body designs constrain heat paths, leading to thermal throttling or faults during sustained operation.",
      "runtime_status": "SINGLE_SOURCE",
      "verified_evidence_count": 1,
      "family_resolution": null,
      "evidence": [
        {
          "evidence_id": "C007-E001",
          "citation_ref": "SRC001",
          "support_reason": "The text explicitly links compact body heat path constraints to the risk of actuators throttling or faulting during sustained operation.",
          "source_type": "industry_blog",
          "tier": 4,
          "excerpt": "Thermal protection strategy is listed as a distinct design variable... because actuator motors generate heat under load, and in a compact humanoid body the heat paths are constrained."
        }
      ]
    }
  ],
  "semantic_relations": [
    {
      "from_claim_ref": "SG04:C001",
      "to_claim_ref": "SG01:C001",
      "relation": "SAME",
      "is_novel": false,
      "reason": "Both claims state the industry shift toward Vision-Language-Action (VLA) models for general-purpose capabilities."
    },
    {
      "from_claim_ref": "SG04:C002",
      "to_claim_ref": "SG02:C001",
      "relation": "CONTRADICTS",
      "is_novel": true,
      "reason": "SG02:C001 states Optimus Gen 3 is in 'limited production', whereas SG04:C002 specifies it entered 'mass production' in January 2026."
    },
    {
      "from_claim_ref": "SG04:C003",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces a specific architectural detail regarding the hands of Optimus Gen 3 not mentioned in prior claims."
    },
    {
      "from_claim_ref": "SG05:C001",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces Samsung Electronics' specific development timeline and target debut for an AI-Native humanoid."
    },
    {
      "from_claim_ref": "SG05:C002",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces Samsung's specific strategy of using its own factories as 'data factories' for training."
    },
    {
      "from_claim_ref": "SG05:C003",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces a specific product ('Scan & Go') and its capabilities from Doosan Robotics."
    },
    {
      "from_claim_ref": "SG05:C004",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces Doosan Robotics' collaboration with NVIDIA and their 2028 product target."
    },
    {
      "from_claim_ref": "SG06:C001",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Provides specific quantitative latency targets (10-100ms) for VLA inference."
    },
    {
      "from_claim_ref": "SG06:C003",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces the specific technical mechanisms of the Deltoris framework."
    },
    {
      "from_claim_ref": "SG06:C004",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces the specific technical implementation of VLA-RAIL for inference bottlenecks."
    },
    {
      "from_claim_ref": "SG06:C005",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Introduces a specific chemical trade-off (LFP vs NCA) for humanoid battery efficiency."
    },
    {
      "from_claim_ref": "SG06:C006",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Provides a technical comparison between rigid and soft actuators regarding energy efficiency."
    },
    {
      "from_claim_ref": "SG06:C007",
      "to_claim_ref": null,
      "relation": "NOVEL",
      "is_novel": true,
      "reason": "Identifies thermal management as a primary production bottleneck for humanoid actuators."
    }
  ],
  "independence_families": [
    {
      "family_ref": "SG01:C001",
      "claim_refs": [
        "SG01:C001",
        "SG04:C001"
      ],
      "final_verdict": "TRIANGULATED",
      "resolved_status": "TRIANGULATED",
      "reason": "The claim is confirmed independent via the pairing of the academic paper (S001) with either of the industry sources.",
      "pairwise": [
        {
          "source_a_ref": "S001",
          "source_b_ref": "S002",
          "verdict": "CONFIRMED_INDEPENDENT",
          "reason": "S001 is a peer-reviewed academic review paper (arXiv) providing a theoretical and systematic overview, while S002 is a technical engineering guide from a private entity (NeuralCoreTech) focusing on specific hardware implementations (e.g., SigLIP, Blackwell GPU)."
        },
        {
          "source_a_ref": "S001",
          "source_b_ref": "S003",
          "verdict": "CONFIRMED_INDEPENDENT",
          "reason": "S001 is an academic review; S003 is a strategic industry insight piece from a different organization (meta-intelligence.tech) focusing on deployment and the NVIDIA Isaac platform."
        },
        {
          "source_a_ref": "S002",
          "source_b_ref": "S003",
          "verdict": "INSUFFICIENT_PROVENANCE",
          "reason": "Both S002 and S003 are industry-tier sources discussing the same general trend (VLA shift) and referencing the same underlying ecosystem (NVIDIA/Physical AI). There is no evidence of separate primary research or direct reporting; they may both be deriving their claims from the same NVIDIA technical documentation or press releases."
        }
      ]
    },
    {
      "family_ref": "SG02:C004",
      "claim_refs": [
        "SG02:C004"
      ],
      "final_verdict": "UNKNOWN",
      "resolved_status": "MULTI_SOURCE_PENDING_INDEPENDENCE",
      "reason": "The sources are likely dependent on a single common origin (CES 2026 public demonstration), and no separate primary provenance is established.",
      "pairwise": [
        {
          "source_a_ref": "S001",
          "source_b_ref": "S002",
          "verdict": "INSUFFICIENT_PROVENANCE",
          "reason": "S001 (AI Herald) and S002 (rabby.kr) both report on the same event: Atlas being piloted at Hyundai factories. S002 explicitly mentions seeing this in 'CES 2026 videos'. S001 is a general comparison. There is no evidence that either source conducted independent reporting or had separate primary access; they are likely repeating the same public demonstration/press release from CES 2026."
        }
      ]
    },
    {
      "family_ref": "SG05:C001",
      "claim_refs": [
        "SG05:C001"
      ],
      "final_verdict": "UNKNOWN",
      "resolved_status": "MULTI_SOURCE_PENDING_INDEPENDENCE",
      "reason": "The high degree of overlap in specific dates and targets suggests a common primary source (press release), making independence unverified.",
      "pairwise": [
        {
          "source_a_ref": "S001",
          "source_b_ref": "S002",
          "verdict": "INSUFFICIENT_PROVENANCE",
          "reason": "S001 (Seoul Economic Daily) and S002 (Gonggam Shinmun) report nearly identical specific details (the date 2026.09.07 and the CES 2027 target). The phrasing and specific data points suggest they are both reporting on the same single press release or industry leak rather than conducting independent investigative journalism."
        }
      ]
    }
  ],
  "unsupported_claims": [
    {
      "wave": 1,
      "claim_ref": "SG01:C006",
      "claim": "자율주행 및 이동 플랫폼 기술은 시뮬레이션 기반의 초고속 학습(Sim-to-Real)과 시각-언어 내비게이션(VLN)으로 진화하고 있다.",
      "reason": "While the source verifies the Sim-to-Real speed (1,000x), it contains no mention of 'Vision-Language Navigation (VLN)' or 'UAV-VLN', making the claim only partially supported."
    },
    {
      "wave": 1,
      "claim_ref": "SG02:C006",
      "claim": "Unitree has entered the commercial market with the G1 humanoid robot, significantly lowering the price point to approximately $4,000.",
      "reason": "The claim identifies the robot as 'G1', but the retrieved source explicitly mentions 'Unitree drops the R1 to $4K'. This is a content mismatch regarding the product model name."
    },
    {
      "wave": 2,
      "claim_ref": "SG06:C002",
      "claim": "Diffusion-based VLA models are compute-intensive and often create a performance gap where the robot's 'brain' is too slow for its 'body,' resulting in motion jitter, stalling, and safety risks in dynamic environments.",
      "reason": "While the source confirms diffusion-based VLAs are compute-intensive and require high frequency (50-200 Hz), it does not mention 'motion jitter', 'stalling', 'safety risks', or the 'brain vs body' performance gap."
    }
  ],
  "research_gaps": [
    {
      "assignment_id": "SG01",
      "type": "WORKER_GAP",
      "detail": "Tesla Optimus 및 Figure AI의 구체적인 하드웨어-소프트웨어 통합 아키텍처 세부 명세(SoC 설계 등)에 대한 공식 기술 문서 부족",
      "wave": 1
    },
    {
      "assignment_id": "SG01",
      "type": "WORKER_GAP",
      "detail": "VLA 모델의 추론 지연 시간(Latency) 문제를 해결하기 위한 최신 하드웨어 가속 기법의 구체적인 벤치마크 수치",
      "wave": 1
    },
    {
      "assignment_id": "SG01",
      "type": "UNSUPPORTED_CLAIM",
      "claim_id": "C006",
      "detail": "자율주행 및 이동 플랫폼 기술은 시뮬레이션 기반의 초고속 학습(Sim-to-Real)과 시각-언어 내비게이션(VLN)으로 진화하고 있다.",
      "reason": "While the source verifies the Sim-to-Real speed (1,000x), it contains no mention of 'Vision-Language Navigation (VLN)' or 'UAV-VLN', making the claim only partially supported.",
      "wave": 1
    },
    {
      "assignment_id": "SG02",
      "type": "WORKER_GAP",
      "detail": "Specific current 'Physical AI' product names and commercialization stages for Samsung Electronics and Doosan Robotics were not explicitly detailed in the verified sources, although general investment trends were noted.",
      "wave": 1
    },
    {
      "assignment_id": "SG02",
      "type": "WORKER_GAP",
      "detail": "Detailed technical specifications (payload, battery life) for the latest 2026 versions of Optimus and Figure 03 were partially omitted in the read excerpts.",
      "wave": 1
    },
    {
      "assignment_id": "SG02",
      "type": "UNSUPPORTED_CLAIM",
      "claim_id": "C006",
      "detail": "Unitree has entered the commercial market with the G1 humanoid robot, significantly lowering the price point to approximately $4,000.",
      "reason": "The claim identifies the robot as 'G1', but the retrieved source explicitly mentions 'Unitree drops the R1 to $4K'. This is a content mismatch regarding the product model name.",
      "wave": 1
    },
    {
      "assignment_id": "SG03",
      "type": "WORKER_GAP",
      "detail": "Detailed technical specifications and a comprehensive equipment list for a 'state-of-the-art' public robotics testbed (beyond the mention of '11 types of equipment').",
      "wave": 1
    },
    {
      "assignment_id": "SG03",
      "type": "WORKER_GAP",
      "detail": "Verification of the 'six coupled challenges' of Physical AI (data ecosystems, sim-to-real resilience, lifelong adaptation, safety assurance, workforce integration, and sustainable hardware) due to access restrictions on the primary source.",
      "wave": 1
    },
    {
      "assignment_id": "SG04",
      "type": "WORKER_GAP",
      "detail": "Verification of the exact number of Agility Digit robots deployed at Amazon (conflict between 75 and 10,000 units).",
      "wave": 2
    },
    {
      "assignment_id": "SG04",
      "type": "WORKER_GAP",
      "detail": "Official confirmation from Tesla regarding the external commercial availability date for Optimus Gen 3.",
      "wave": 2
    },
    {
      "assignment_id": "SG05",
      "type": "WORKER_GAP",
      "detail": "Detailed numeric specifications (e.g., exact dimensions, load capacities, or sensor precision) for the KIRIA public testbed equipment beyond the mentioned ISO standards and general categories.",
      "wave": 2
    },
    {
      "assignment_id": "SG06",
      "type": "WORKER_GAP",
      "detail": "Specific numeric energy efficiency benchmarks (e.g., Joules per movement) for soft vs. rigid actuators were not provided.",
      "wave": 2
    },
    {
      "assignment_id": "SG06",
      "type": "WORKER_GAP",
      "detail": "Detailed hardware specifications for the 'Jetson AGX Thor' in the context of VLA acceleration were mentioned but not deeply detailed in the read sources.",
      "wave": 2
    },
    {
      "assignment_id": "SG06",
      "type": "UNSUPPORTED_CLAIM",
      "claim_id": "C002",
      "detail": "Diffusion-based VLA models are compute-intensive and often create a performance gap where the robot's 'brain' is too slow for its 'body,' resulting in motion jitter, stalling, and safety risks in dynamic environments.",
      "reason": "While the source confirms diffusion-based VLAs are compute-intensive and require high frequency (50-200 Hz), it does not mention 'motion jitter', 'stalling', 'safety risks', or the 'brain vs body' performance gap.",
      "wave": 2
    }
  ],
  "verified_sources": [
    {
      "citation_ref": "SRC001",
      "url": "https://actuatorhq.com/blog/humanoid-robot-engineering-barriers-prototype-to-production-2025",
      "title": "Humanoid Robot Engineering Barriers: Motion Control, Thermal and Power Trade-offs",
      "publisher": "actuatorhq.com",
      "domain": "actuatorhq.com",
      "audited_source_type": "industry_blog",
      "audited_tier": 4,
      "worker_excerpt": "The trade-off between lithium iron phosphate chemistry (LFP) and nickel cobalt aluminum chemistry (NCA) is not academic. LFP offers better thermal stability and cycle life. NCA offers higher energy density.",
      "support_reason": "The text explicitly confirms the specific properties of LFP vs NCA chemistries in the context of humanoid power systems.",
      "claim_refs": [
        "SG06:C005",
        "SG06:C007"
      ],
      "evidence_refs": [
        "SG06:C005:C005-E001",
        "SG06:C007:C007-E001"
      ]
    },
    {
      "citation_ref": "SRC002",
      "url": "https://actuatorhq.com/blog/new-research-robotics-energy-efficiency-breakthroughs-2026",
      "title": "New Research: Robots Push Energy Limits in Three Different Directions",
      "publisher": "actuatorhq.com",
      "domain": "actuatorhq.com",
      "audited_source_type": "industry_blog",
      "audited_tier": 4,
      "worker_excerpt": "Rigid actuator systems, like the harmonic drives and brushless motors used in most humanoid robots, require continuous power input to hold position and generate force. Soft actuators can exploit material compliance to absorb and redirect energy more naturally.",
      "support_reason": "The retrieved content directly supports the energy efficiency comparison between rigid and soft actuators.",
      "claim_refs": [
        "SG06:C006"
      ],
      "evidence_refs": [
        "SG06:C006:C006-E001"
      ]
    },
    {
      "citation_ref": "SRC003",
      "url": "https://andrew.ooo/answers/boston-dynamics-vs-figure-vs-agility-vs-1x-humanoid-landscape-july-2026",
      "title": "Boston Dynamics vs Figure vs Agility vs 1X (Humanoid Robots July 2026) — andrew.ooo",
      "publisher": "andrew.ooo",
      "domain": "andrew.ooo",
      "audited_source_type": "industry_analysis",
      "audited_tier": 5,
      "worker_excerpt": "Agility deploying Digit at Amazon",
      "support_reason": "The text explicitly states 'Agility deploying Digit at Amazon'.",
      "claim_refs": [
        "SG02:C003"
      ],
      "evidence_refs": [
        "SG02:C003:C003-E001"
      ]
    },
    {
      "citation_ref": "SRC004",
      "url": "https://artificialintelligenceherald.com/robotics/boston-dynamics-atlas-vs-tesla-optimus-vs-figure-02-2026-showdown",
      "title": "Boston Dynamics Atlas vs Tesla Optimus vs Figure 02: 2026 Showdown - AI Herald",
      "publisher": "AI Herald",
      "domain": "artificialintelligenceherald.com",
      "audited_source_type": "industry_analysis",
      "audited_tier": 4,
      "worker_excerpt": "The Gen 3 unit, now in limited production at Tesla’s Fremont facility... Optimus units are primarily deployed inside Tesla factories—performing bin picking, kitting, and basic assembly tasks.",
      "support_reason": "The source text explicitly states: 'The Gen 3 unit, now in limited production at Tesla’s Fremont facility' and 'Optimus units are primarily deployed inside Tesla factories—performing bin picking, kitting, and basic assembly tasks.'",
      "claim_refs": [
        "SG02:C001",
        "SG02:C002",
        "SG02:C004"
      ],
      "evidence_refs": [
        "SG02:C001:C001-E001",
        "SG02:C002:C002-E001",
        "SG02:C004:C004-E001"
      ]
    },
    {
      "citation_ref": "SRC005",
      "url": "https://arxiv.org/abs/2510.07077",
      "title": "[2510.07077] Vision-Language-Action Models for Robotics: A Review Towards Real-World Applications",
      "publisher": "arXiv",
      "domain": "arxiv.org",
      "audited_source_type": "academic_paper",
      "audited_tier": 2,
      "worker_excerpt": "By unifying vision, language, and action data at scale... VLA models aim to learn policies that generalise across diverse tasks, objects, embodiments, and environments.",
      "support_reason": "The retrieved content explicitly states that VLA models aim to learn policies that generalize across diverse tasks, objects, embodiments, and environments by unifying vision, language, and action data at scale.",
      "claim_refs": [
        "SG04:C001"
      ],
      "evidence_refs": [
        "SG04:C001:C001-E001"
      ]
    },
    {
      "citation_ref": "SRC006",
      "url": "https://arxiv.org/abs/2512.24673",
      "title": "[2512.24673] VLA-RAIL: A Real-Time Asynchronous Inference Linker for VLA Models and Robots",
      "publisher": "arxiv.org",
      "domain": "arxiv.org",
      "audited_source_type": "academic_paper",
      "audited_tier": 2,
      "worker_excerpt": "a Trajectory Smoother that effectively filters out the noise and jitter in the trajectory of one action chunk using polynomial fitting and a Chunk Fuser that seamlessly align the current executing trajectory and the newly arrived chunk",
      "support_reason": "The retrieved text directly supports the implementation of the Smoother and Fuser and their specific goals for continuity.",
      "claim_refs": [
        "SG06:C004"
      ],
      "evidence_refs": [
        "SG06:C004:C004-E001"
      ]
    },
    {
      "citation_ref": "SRC007",
      "url": "https://arxiv.org/abs/2608.04428",
      "title": "[2608.04428] Deltoris: Enabling Real-time VLA Inference in Embodied AI via Bit-level Sparsity and Speculative Inference",
      "publisher": "arxiv.org",
      "domain": "arxiv.org",
      "audited_source_type": "academic_paper",
      "audited_tier": 2,
      "worker_excerpt": "we propose a temporal-aware bit-sparsity algorithm that computes only the differences between consecutive inputs... we propose a speculative inference technique, which amortizes data loading across multiple control steps. Lastly, to support these techniques, we co-design a dedicated accelerator with customized 1D systolic bit-serial PE arrays",
      "support_reason": "The retrieved content contains all technical components of the claim including the specific algorithm names and hardware architecture.",
      "claim_refs": [
        "SG06:C003"
      ],
      "evidence_refs": [
        "SG06:C003:C003-E001"
      ]
    },
    {
      "citation_ref": "SRC008",
      "url": "https://arxiv.org/html/2602.18397v1",
      "title": "How Fast Can I Run My VLA? Demystifying VLA Inference Performance with VLA-Perf",
      "publisher": "arxiv.org",
      "domain": "arxiv.org",
      "audited_source_type": "academic_paper",
      "audited_tier": 2,
      "worker_excerpt": "Given that standard RGB camera frame rates typically range from 24 to 60 Hz, we define a 10 Hz inference frequency as... What combinations of models and systems are required to support VLA inference at rates from 10 Hz up to and beyond 100 Hz",
      "support_reason": "The text directly supports the relationship between camera frame rates and the defined VLA inference frequency targets.",
      "claim_refs": [
        "SG06:C001"
      ],
      "evidence_refs": [
        "SG06:C001:C001-E001"
      ]
    },
    {
      "citation_ref": "SRC009",
      "url": "https://blog.pebblous.ai/project/PhysicalAI/physical-ai/en",
      "title": "What Is a VLA (Vision-Language-Action) Model? — Physical AI Model Evolution & Data Strategy (2026 Edition) | Pebblous",
      "publisher": "Pebblous",
      "domain": "blog.pebblous.ai",
      "audited_source_type": "industry",
      "audited_tier": 4,
      "worker_excerpt": "The three challenges... heterogeneity, the Sim-to-Real Gap, and scarcity — remain the bottleneck... the bottleneck has shifted from 'equipment' to 'skilled operators and data quality.'",
      "support_reason": "The content explicitly lists the three challenges and states the bottleneck has shifted from 'equipment' to 'skilled operators and data quality'.",
      "claim_refs": [
        "SG03:C004"
      ],
      "evidence_refs": [
        "SG03:C004:C004-E001"
      ]
    },
    {
      "citation_ref": "SRC010",
      "url": "https://en.sedaily.com/finance/2026/09/07/samsung-builds-ai-into-robot-design-to-speed-humanoid-push",
      "title": "Samsung Builds AI Into Robot Design to Speed Humanoid Push - Seoul Economic Daily",
      "publisher": "Seoul Economic Daily",
      "domain": "en.sedaily.com",
      "audited_source_type": "industry",
      "audited_tier": 2,
      "worker_excerpt": "[Samsung Humanoid to Debut at CES Next Year] ... build a custom humanoid optimized for AI algorithms from the initial design stage",
      "support_reason": "Confirms the goal to debut at CES 'next year' (relative to Sept 2026) and explicitly mentions building a custom humanoid optimized for AI algorithms from the initial design stage.",
      "claim_refs": [
        "SG05:C001",
        "SG05:C002"
      ],
      "evidence_refs": [
        "SG05:C001:C001-E002",
        "SG05:C002:C002-E001"
      ]
    },
    {
      "citation_ref": "SRC011",
      "url": "https://neuralcoretech.com/physical-ai-architecture-vla-robotics",
      "title": "Physical AI Architecture: The Ultimate 2026 VLA Engineering Guide - NeuralCoreTech",
      "publisher": "NeuralCoreTech",
      "domain": "neuralcoretech.com",
      "audited_source_type": "industry",
      "audited_tier": 2,
      "worker_excerpt": "The architectural shift that defines 2025–2026 is the introduction of foundation model backbones into the policy — specifically, large Vision-Language Models (VLMs) pretrained on internet-scale data — paired with action generation modules capable of producing smooth, continuous motor trajectories. This is the Vision-Language-Action (VLA) paradigm",
      "support_reason": "Explicitly states the architectural shift of 2025-2026 is the introduction of foundation model backbones (VLMs pretrained on internet-scale data) paired with action generation, defining the VLA paradigm.",
      "claim_refs": [
        "SG01:C001",
        "SG01:C002",
        "SG01:C005"
      ],
      "evidence_refs": [
        "SG01:C001:C001-E001",
        "SG01:C002:C002-E001",
        "SG01:C005:C005-E001"
      ]
    },
    {
      "citation_ref": "SRC012",
      "url": "https://optimusk.blog/blog/tesla-optimus-gen-3-vs-gen-2-comparison",
      "title": "Tesla Optimus Gen 3 vs Gen 2: Full Specs Comparison (2026)",
      "publisher": "optimusk.blog",
      "domain": "optimusk.blog",
      "audited_source_type": "industry_blog",
      "audited_tier": 4,
      "worker_excerpt": "January 21, 2026: Gen 3 mass production commences at Fremont, California... The units being produced and tested in Fremont are 'production' in the manufacturing sense, not yet in the commercial sales sense.",
      "support_reason": "The content explicitly mentions mass production commenced January 21, 2026, at Fremont and specifies that these are 'production' in the manufacturing sense, not the commercial sales sense.",
      "claim_refs": [
        "SG04:C002",
        "SG04:C003"
      ],
      "evidence_refs": [
        "SG04:C002:C002-E001",
        "SG04:C003:C003-E001"
      ]
    },
    {
      "citation_ref": "SRC013",
      "url": "https://qnx.software/en/blog/2026/inside-the-robot",
      "title": "Software Architecture: The New Bottleneck for Physical AI",
      "publisher": "QNX",
      "domain": "qnx.software",
      "audited_source_type": "industry",
      "audited_tier": 4,
      "worker_excerpt": "almost one in three developers (27%) cite software architecture and integration as their biggest performance bottleneck, compared to just 16% who cite hardware constraints.",
      "support_reason": "The content explicitly states that 27% of developers cite software architecture and integration as the biggest bottleneck compared to 16% for hardware.",
      "claim_refs": [
        "SG03:C001",
        "SG03:C002",
        "SG03:C003"
      ],
      "evidence_refs": [
        "SG03:C001:C001-E001",
        "SG03:C002:C002-E001",
        "SG03:C003:C003-E001"
      ]
    },
    {
      "citation_ref": "SRC014",
      "url": "https://rabby.kr/physical-ai-robots-korea-cases-2026",
      "title": "피지컬 AI 로봇 2026 한국 7가지 도입 사례 총정리",
      "publisher": "rabby.kr",
      "domain": "rabby.kr",
      "audited_source_type": "industry_analysis",
      "audited_tier": 5,
      "worker_excerpt": "보스턴다이내믹스 ‘아틀라스’가 자동차 부품을 직접 옮기는 장면... 현대차 공장에서 실제로 시범 운영 중인 모습이더군요.",
      "support_reason": "The Korean text confirms Atlas is 'actually being pilot-operated in Hyundai Motor factories' (현대차 공장에서 실제로 시범 운영 중) and moving automotive parts (자동차 부품을 직접 옮기는 장면).",
      "claim_refs": [
        "SG02:C004"
      ],
      "evidence_refs": [
        "SG02:C004:C004-E002"
      ]
    },
    {
      "citation_ref": "SRC015",
      "url": "https://www.betanews.net/article/view/beta202609030109",
      "title": "한병도, ‘로봇특별법’ 대표발의…이동로봇 실증·상용화·안전관리 통합 지원",
      "publisher": "Betanews",
      "domain": "www.betanews.net",
      "audited_source_type": "industry",
      "audited_tier": 4,
      "worker_excerpt": "활용 관련 규정도 건축법·공동주택관리법·개인정보보호법 등에 흩어져 있어 통합적인 제도 기반이 필요하다는 지적이 제기되어 왔다.",
      "support_reason": "The text confirms the representative proposal of the law and explicitly lists the fragmented laws (건축법, 공동주택관리법, 개인정보보호법).",
      "claim_refs": [
        "SG03:C005"
      ],
      "evidence_refs": [
        "SG03:C005:C005-E001"
      ]
    },
    {
      "citation_ref": "SRC016",
      "url": "https://www.etnews.com/20260429000466",
      "title": "두산로보틱스-엔비디아, 피지컬 AI 로봇 협력…2028년 산업용 휴머노이드 선보인다 - 전자신문",
      "publisher": "전자신문",
      "domain": "www.etnews.com",
      "audited_source_type": "industry",
      "audited_tier": 2,
      "worker_excerpt": "두산로보틱스가 엔비디아와 피지컬 인공지능(AI) 기반 로봇 솔루션 개발 협력에 나선다. ... 2028년에는 산업용 휴머노이드 제품을 순차적으로 공개한다는 목표다. ... 로봇 전용 실행 소프트웨어 '에이전틱 로봇 운영체제(Agentic Robot O/S)'와 엔비디아의 AI·로보틱스 시뮬레이션·학습 인프라를 연계",
      "support_reason": "Explicitly mentions the collaboration with NVIDIA, the development of the 'Agentic Robot O/S', and the goal to sequentially reveal industrial humanoid products by 2028.",
      "claim_refs": [
        "SG05:C004"
      ],
      "evidence_refs": [
        "SG05:C004:C004-E001"
      ]
    },
    {
      "citation_ref": "SRC017",
      "url": "https://www.gokorea.kr/news/articleView.html?idxno=877516",
      "title": "삼성전자 휴머노이드 개발 착수 CES 2027 공개 목표 < AI < 미래공감 < 기사본문 - 공감신문",
      "publisher": "공감신문",
      "domain": "www.gokorea.kr",
      "audited_source_type": "industry",
      "audited_tier": 2,
      "worker_excerpt": "삼성전자가 2026년 9월 7일 차세대 지능형 휴머노이드(인간형 로봇) 개발 프로젝트를 본격화하고 2027년 1월 미국 라스베이거스에서 열리는 세계 최대 전자·정보기술 전시회 CES 2027 공개를 목표로 실무 작업에 착수했다.",
      "support_reason": "Explicitly states Samsung started a next-gen intelligent humanoid project on 2026-09-07 with a goal to reveal it at CES 2027 in Las Vegas.",
      "claim_refs": [
        "SG05:C001"
      ],
      "evidence_refs": [
        "SG05:C001:C001-E001"
      ]
    },
    {
      "citation_ref": "SRC018",
      "url": "https://www.industrynews.co.kr/news/articleView.html?idxno=54354",
      "title": "KAIST, 자율주행차·로봇 등 온디바이스 환경서 적응형 인공지능 실현 < 이슈·트렌드 < 자율제조·스마트팩토리 < 산업 < 기사본문 - 인더스트리뉴스",
      "publisher": "인더스트리뉴스",
      "domain": "www.industrynews.co.kr",
      "audited_source_type": "official",
      "audited_tier": 2,
      "worker_excerpt": "적응형 AI의 기반 기술인 ‘연속 학습’ 가속을 위한 NPU(신경망처리장치) 구조 및 온디바이스 소프트웨어 시스템을 최초 개발... 효율적 병렬 프로세싱을 위해 2차원 시스톨릭 배열(Systolic Array) 구조를 기반으로 한다.",
      "support_reason": "The article confirms the development of an NPU structure based on 2D Systolic Arrays and Microsoft MX multi-precision computing to realize Adaptive AI/Continual Learning on-device without cloud resources.",
      "claim_refs": [
        "SG01:C004"
      ],
      "evidence_refs": [
        "SG01:C004:C004-E001"
      ]
    },
    {
      "citation_ref": "SRC019",
      "url": "https://www.kyeonggi.com/article/20260723580350",
      "title": "투모로 로보틱스, 피지컬 AI 상용화 속도…레인보우로보틱스와 '스스로 일하는 로봇' 공동개발",
      "publisher": "경기일보",
      "domain": "www.kyeonggi.com",
      "audited_source_type": "official",
      "audited_tier": 1,
      "worker_excerpt": "투모로 로보틱스는 지난 21일 레인보우로보틱스와 ‘피지컬 AI 기반 로봇 연구개발 및 사업 협력을 위한 업무협약(MOU)’을 체결했다고 23일 밝혔다... 레인보우로보틱스의 로봇 하드웨어 기술과 투모로 로보틱스의 AI·소프트웨어 기술을 결합해 실제 산업 현장에서 활용할 수 있는 AI-Native 휴머노이드 로봇을 공동 개발하는 것이 핵심이다.",
      "support_reason": "The source explicitly details the MOU for 'AI-Native humanoid robot' development, specifically mentioning the use of 'Robot Foundation Model (RFM)' and 'AI Agent'.",
      "claim_refs": [
        "SG02:C005"
      ],
      "evidence_refs": [
        "SG02:C005:C005-E001"
      ]
    },
    {
      "citation_ref": "SRC020",
      "url": "https://www.meta-intelligence.tech/en/insight-physical-ai",
      "title": "Humanoid Robots 2026: Tesla Optimus, Figure 02 & NVIDIA Isaac Status",
      "publisher": "meta-intelligence.tech",
      "domain": "www.meta-intelligence.tech",
      "audited_source_type": "industry",
      "audited_tier": 2,
      "worker_excerpt": "Breakthroughs in Robot Foundation Models are the key driving force behind Physical AI's accelerated deployment — RT-2 and other Vision-Language-Action models (VLA) achieved, for the first time, \"commanding robots with natural language to complete previously unseen tasks\"",
      "support_reason": "Confirms VLA models (like RT-2) allow commanding robots with natural language to complete previously unseen tasks.",
      "claim_refs": [
        "SG01:C001"
      ],
      "evidence_refs": [
        "SG01:C001:C001-E002"
      ]
    },
    {
      "citation_ref": "SRC021",
      "url": "https://www.patsnap.com/resources/blog/rd-blog/robotic-grasping-technology-landscape-2026-patsnap-eureka",
      "title": "Robotic Grasping Technology Landscape 2026 — PatSnap Eureka | Patsnap",
      "publisher": "Patsnap",
      "domain": "www.patsnap.com",
      "audited_source_type": "industry",
      "audited_tier": 2,
      "worker_excerpt": "Samsung's task-aware grasp estimation patents (US, 2024–2026) demonstrate that grasp selection should be informed by the downstream placement geometry, linking pick-and-place into a unified neural planning problem. This reduces re-grasp events and improves cycle time.",
      "support_reason": "The source explicitly mentions Samsung's task-aware grasp estimation patents (2024-2026) and the concept of 'Grasp-for-Placement Synergy' where downstream placement geometry informs grasp selection.",
      "claim_refs": [
        "SG01:C003"
      ],
      "evidence_refs": [
        "SG01:C003:C003-E001"
      ]
    },
    {
      "citation_ref": "SRC022",
      "url": "https://www.yna.co.kr/view/AKR20250930148000052",
      "title": "KTL, 'K-로봇' 글로벌 경쟁력 강화…시험·인증 인프라 확충 | 연합뉴스",
      "publisher": "YNA",
      "domain": "www.yna.co.kr",
      "audited_source_type": "official",
      "audited_tier": 1,
      "worker_excerpt": "사람과 함께 운용된다는 특성상 제품과 시스템에 대한 안전인증이 필수적이지만, 그동안 국내 시험인증 기반 부족으로 해외 의존도가 높았다.",
      "support_reason": "The text explicitly states that domestic certification infrastructure was lacking, leading to high overseas dependence, and describes KTL's new center as a solution.",
      "claim_refs": [
        "SG03:C006"
      ],
      "evidence_refs": [
        "SG03:C006:C006-E001"
      ]
    },
    {
      "citation_ref": "SRC023",
      "url": "https://zdnet.co.kr/view?no=20260107154524",
      "title": "CES 최고혁신상 '스캔앤고'…두산로보틱스, AI 로봇 상용 본격화 - ZDNet korea",
      "publisher": "ZDNet Korea",
      "domain": "zdnet.co.kr",
      "audited_source_type": "industry",
      "audited_tier": 2,
      "worker_excerpt": "스캔앤고는 협동로봇 팔과 자율이동로봇(AMR)을 결합한 플랫폼에 물리정보 기반 AI와 3D 비전 기술을 적용한 산업용 AI 로봇 솔루션이다. ... 0.1mm 수준의 작업 정밀도를 구현했다. ... 산업용 안전 기준인 PLe, Cat4도 충족했다.",
      "support_reason": "Confirms 'Scan & Go' is an AI robot solution for tasks like sanding and grinding on large structures without blueprints, achieving 0.1mm precision and PLe, Cat4 safety compliance.",
      "claim_refs": [
        "SG05:C003"
      ],
      "evidence_refs": [
        "SG05:C003:C003-E001"
      ]
    }
  ]
}

# Task

Produce the final evidence-backed deep research report in Korean.
Use the structure and research behavior specified by the active Skill and synthesis contract.
Cite factual findings using only the provided [SRCxxx] references.
Include a source/reference section mapping every citation used to its provided source title, publisher, and URL.
Return Markdown report text only.