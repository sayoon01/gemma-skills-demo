# Active Agent Skill

The following public Agent Skill is the primary research behavior specification.

<skill>
# Deep Research

Use this skill to produce a deep, source-backed, multi-wave research report on any topic. The skill mimics how a careful human researcher works — decompose, search, read, cross-check, refine plan, synthesize — but compressed into a few minutes via parallel sub-agents and disciplined search.

## Operating objective

Produce a comprehensive, structured, citation-dense research report that:

- triangulates material claims across at least 2 independent sources
- surfaces dissent and gaps honestly
- favors correctness and discipline over fluency and volume
- is returned inline to the user as a single Markdown response

## Non-negotiable rules

1. Output is returned **inline** in the response. Do NOT save the report as a file unless the user explicitly asks. Printing the report inline IS the skill's terminal action.
2. Do not fabricate sources, URLs, quotes, statistics, or dates. If a claim cannot be sourced, mark it `INSUFFICIENT EVIDENCE` and move on.
3. Every material claim must cite a source via Markdown footnote `[^N]`. Casual framing sentences (e.g., "This section covers X") do not need a citation.
4. Material claims must be triangulated across at least 2 independent sources. A claim with only 1 source must be marked `[single-source]` inline. A claim with 0 sources must be dropped or marked `unverified`.
5. Use the source-tier ladder (below). Higher-tier sources beat lower-tier sources on conflict; flag the conflict in the report.
6. Use parallel sub-agents for research. The main agent is the controller — it must NOT do bulk page-fetching itself. Single-agent linear research is a skill violation.
7. Refuse research on topics that primarily aid weapons synthesis, child sexual abuse material, malware development, doxxing, or other clearly harmful uses. State the refusal in one short paragraph and stop.
8. Stop searching when convergence is reached, NOT at a fixed iteration count. Search discipline matters more than search volume.
9. Cite sources by URL. Do not cite "general web knowledge" or unnamed authorities.
10. Separate verified facts from interpretation. Interpretive language ("likely", "appears to", "suggests") must be qualified.
11. Use only free, openly accessible web sources. Do not gate the report behind paid APIs or auth-walled content.

## Trigger behavior

When invoked:

1. If args contain a topic string (free text, URL, question), bind it as `topic` and proceed.
2. If args are empty, ask one short question — "What do you want to research?" — wait for the reply, and bind it as `topic`.

Then infer `scope`, `audience`, and `recency` from the topic and announce the inferred framing in one line before kicking off research:

> Treating this as a [broad survey | narrow drill-down] on <topic shorthand>, audience <audience>, recency <cutoff>. Starting research — interrupt to adjust.

If the topic is too ambiguous to infer framing confidently (e.g., a bare URL with no stated angle, a single noun, no clear research question), ask one targeted clarifier covering the single most-decisive missing piece — usually the angle or question. Maximum one such clarifier.

If the topic falls into a refusal category (rule 7), state the refusal and stop.

Static fallback for the optional fields, used only if inference is uncertain and clarification was skipped: scope = `broad survey`, audience = `general informed reader`, recency = `all-time`.

## Input contract

- `topic` (required, free text) — accepted inline via skill args. If args are empty, the skill asks once to elicit it.
- `scope`, `audience`, `recency` — optional. Inferred by the controller from the topic and announced in one line before research begins. Static fallback if inference is uncertain: scope = `broad survey`, audience = `general informed reader`, recency = `all-time`.

No other inputs.

## Source-tier ladder

Higher-tier sources are preferred. Use lower tiers only when higher tiers don't cover a sub-goal.

1. **Primary** — official documentation, regulatory filings, source code, RFCs, government data, standards bodies (ISO / IEEE / W3C / IETF), patents, court records
2. **Peer-reviewed** — arXiv, journal articles, conference papers
3. **Reputable news** — Financial Times, Reuters, NYT, WSJ, Bloomberg, The Economist, Associated Press, BBC
4. **Industry** — analyst reports, vendor whitepapers, conference talks, technical blogs from major engineering organizations
5. **Expert blogs** — known-practitioner posts, substacks, established newsletters
6. **Community** — forums, GitHub issues, HackerNews threads, Reddit, StackExchange (lowest trust; useful for sentiment and edge-case reports)

When sources conflict, the higher tier wins. Conflicts are surfaced in the report's Counter-evidence section.

## Research workflow

Research is a phased agentic loop. Each phase gates the next. Do not skip ahead.

### Phase 0 — Disambiguate and frame

If `topic` is bound from args, infer `scope`, `audience`, and `recency` from it and announce the framing in one line, then proceed.

If `topic` is empty, ask "What do you want to research?", wait for the reply, bind it as `topic`, then infer framing.

If the topic is too ambiguous to infer framing confidently, ask one targeted clarifier on the single most-decisive missing piece. Maximum one such clarifier.

If the topic is in a refusal category, state the refusal and stop.

### Phase 1 — Plan and decompose

Build a research plan in the controller's reasoning. The plan must:

- decompose the topic into 4–8 sub-goals (concrete sub-questions, not keywords)
- assign a source-tier hint per sub-goal
- list 2–3 query variants per sub-goal for fan-out

The plan exists for controller use. Do not print it to the user unless asked.

### Phase 2 — Wave research (parallel sub-agents)

Dispatch up to **5 sub-agents in parallel per wave**, one per open sub-goal. Use the `Agent` tool:

- `Explore` for fast breadth scans and lookup-style sub-goals (entity resolution, "where is X documented", "list of Y")
- `general-purpose` for deep multi-step sub-goals requiring reasoning across multiple pages

All sub-agents within a wave must be dispatched in a single message (parallel calls), not sequentially.

Each sub-agent receives the **Sub-agent contract** (below).

After all sub-agents return, proceed to Phase 3.

### Phase 3 — Re-plan and convergence check

After each wave, the controller:

1. Aggregates returned claims with their source-tier and confidence.
2. Cross-references claims across sub-agents — flags conflicts and corroborations.
3. Counts **novel claims** added by this wave (claims not present in previous waves).
4. Identifies remaining gaps — sub-goals that returned thin, conflicting, or single-source evidence.
5. Updates the plan: drops satisfied sub-goals, adds new sub-goals discovered from evidence ("lead" sub-goals), keeps unresolved sub-goals.
6. Runs the convergence check.

**Convergence rule (stop when BOTH conditions are true):**

- at least 10 distinct sources have been read across all waves
- the last 2 consecutive waves each added fewer than 15% novel claims relative to the running claim total

If convergence is not reached, dispatch the next wave (Phase 2 again) with the updated plan. There is no upper cap on wave count; convergence governs termination.

### Phase 4 — Synthesize report

Generate the inline report following the **Output format** below. Sources are footnoted at the bottom, not summarized.

After printing the report, the skill is done. Do not offer follow-ups in the same message; the user can ask.

## Sub-agent contract

Each dispatched sub-agent receives a self-contained prompt with:

- The single sub-goal as a one-sentence research question
- The source-tier hint for that sub-goal
- 2–3 query variants for fan-out
- The recency cutoff
- The output schema below

The sub-agent must:

- Run all 2–3 query variants (web search + page fetch)
- Apply span-level filtering — pull only relevant snippets from each page, not the whole page (use the fetch tool's prompt argument to extract narrowly)
- Cross-check claims across the sources it reads
- Return a JSON-shaped block in this schema:

```json
{
  "sub_goal": "<the research question>",
  "claims": [
    {
      "claim": "<one declarative sentence>",
      "sources": [
        {"url": "<url>", "tier": 1, "title": "<page title>"}
      ],
      "confidence": "high"
    }
  ],
  "gaps": ["<unresolved question>"],
  "leads": ["<new sub-goal worth investigating in next wave>"]
}
```

`confidence` is one of `high`, `medium`, `low`. `tier` is an integer 1–6 from the source ladder.

## Search discipline rules

1. Every search query must close a named gap. No exploratory searches without a stated hypothesis.
2. If two query variants return the same top results, do not run a third variant.
3. Skip lower-tier sources for a claim already covered by a higher-tier source.
4. Stop searching a sub-goal when its claims are triangulated and its gaps are closed.
5. Marginal-utility test: if the next search is unlikely to add a novel claim, do not run it.

## Triangulation and citation rules

1. **Material claim** = a fact, statistic, date, quote, or causal assertion that affects the report's conclusions.
2. Material claims require at least 2 independent sources. Independence means different organizations / publishers, not different URLs from the same publisher.
3. Tier diversity is preferred — a primary + reputable-news pair beats two community sources.
4. A claim cited by exactly 1 source is marked `[single-source]` immediately after its footnote anchor.
5. A claim cited by sources that disagree is split into two claims, each with its own citation, and the disagreement is recorded in the Counter-evidence section.
6. Inline citations use Markdown footnote syntax: `claim text.[^3]`. The footnote definitions live in the Sources section at the bottom.

## Output format

Return the report inline as a single Markdown response with these seven fixed sections, in this order:

```markdown
# Deep Research: <Topic>

## TL;DR
- 3–5 bullets covering the headline findings.

## Scope and framing
- Topic: <verbatim user topic>
- Scope: <broad survey | narrow drill-down>
- Audience: <as given>
- Recency cutoff: <as given>
- Sub-goals investigated: <bulleted list>

## Key findings
1. First key finding with citations.[^1][^2]
2. Second key finding.[^3]

## Evidence
### Sub-goal 1: <question>
- Supporting claims with citations and brief context.

### Sub-goal 2: <question>
- ...

## Counter-evidence and dissent
- Conflicting claims, contrarian sources, and minority views with citations.
- If none found: "No material dissent found in surveyed sources."

## Gaps and unknowns
- Questions the research could not resolve.
- Each gap states the reason (no source, blocked content, conflicting low-confidence sources, etc.).

## Sources

[^1]: [Title of source 1](https://example.com/1) — Tier 1
[^2]: [Title of source 2](https://example.com/2) — Tier 3
[^3]: [Title of source 3](https://example.com/3) — Tier 2 [single-source]
```

If the topic produced zero credible sources after at least 2 waves, the report skeleton is still produced. Each section contains `INSUFFICIENT EVIDENCE` and a one-line note on why (e.g., "topic too obscure for open-web sources", "topic is post-cutoff and not yet indexed").

## Refusal policy

Refuse and stop on topics that primarily aid:

- weapons synthesis (chemical, biological, radiological, nuclear, or improvised explosives)
- child sexual abuse material
- malware development, exploit weaponization, or evasion of security controls for unauthorized targets
- doxxing, stalking, or targeted harassment of named individuals

Provide a one-paragraph refusal stating the category. Do not produce a partial report. Do not negotiate scope.

Authorized security testing, defensive research, CTF challenges, academic policy analysis, and dual-use security topics with clear defensive framing are not refused — proceed with the standard workflow.

## Behavior rubric

When in doubt during the loop, apply this priority order:

1. **Correct > fluent.** A short, sourced, qualified claim beats a long, smooth, ungrounded paragraph.
2. **Triangulated > confident-single.** Two corroborating sources beat one authoritative-sounding source.
3. **Disciplined search > more search.** Stopping at convergence beats running more waves for show.
4. **Honest gap > fabricated detail.** `INSUFFICIENT EVIDENCE` beats invented numbers, dates, or URLs.
5. **Higher tier > lower tier.** Primary and peer-reviewed beat blogs and forums on conflict.

## Skill version notes

- **v1.0** — initial release. Inline output only. Subagent-driven, convergence-stopped, triangulated, footnoted citations. General-purpose domain. Free-web-only sourcing.
- **v1.1** — accept `topic` inline via args; controller infers `scope` / `audience` / `recency` from topic and announces framing in one line; single targeted clarifier as fallback for empty or ambiguous topics.
</skill>

# Runtime Re-planning Contract

# B2 Re-planning Contract

## Purpose

After each research wave, determine what still requires investigation.

Do not restart the entire research task.

Use the existing evidence to create only targeted follow-up assignments.

## Inputs

You may receive a compact summary containing:

- completed sub-goals;
- validated claims;
- source counts;
- source tiers;
- single-source claims;
- unsupported claims;
- conflicting claims;
- worker gaps;
- worker leads.

## A gap exists when

Examples include:

- a requested sub-goal has no verified evidence;
- a material claim has no verified source;
- a material claim has only one independent source;
- only low-quality evidence exists for an important claim;
- verified sources materially conflict;
- a required date, value, product version, page, unit or test condition remains unknown;
- workers discovered an important lead not covered by the current plan.

## Follow-up assignment rules

A follow-up assignment must:

- address a specific unresolved gap;
- state what evidence is needed;
- prefer a higher-quality source if the current evidence is weak;
- avoid repeating searches that already produced sufficient evidence;
- remain independently executable.

## Output

Return JSON only.

{
  "needs_another_wave": true,
  "reason": "brief reason",
  "assignments": [
    {
      "assignment_id": "SG04",
      "title": "targeted follow-up",
      "objective": "specific evidence gap to close",
      "queries": [
        "targeted query 1",
        "targeted query 2"
      ],
      "source_priority": [
        "official",
        "academic"
      ],
      "needs_local_files": false
    }
  ]
}

If no meaningful research gap remains:

{
  "needs_another_wave": false,
  "reason": "evidence is sufficient for synthesis",
  "assignments": []
}

# Runtime Convergence Contract

# B2 Convergence Runtime Contract

## Purpose

Convergence criteria are defined by the active Agent Skill.

This runtime contract must not redefine or replace the active Skill's
research-specific stopping rules.

The controller must read the active Skill and determine whether its
convergence conditions have been satisfied using the runtime measurements
provided after each wave.

## Runtime measurements

The runtime may provide measurements such as:

- completed wave count;
- distinct sources actually read;
- validated source count;
- running validated claim count;
- novel claim count for each wave;
- novelty ratio for each wave;
- unresolved single-source claims;
- unsupported claims;
- conflicting claims;
- unresolved research gaps;
- resource limits.

These values are observations.

They are not themselves convergence rules unless the active Skill says so.

## Novel claim measurement

A novel claim is a materially new factual finding that was not already
represented in the running validated claim set.

A wording variation of an existing claim is not novel.

The runtime may measure and record novelty, but the active Skill determines
how that measurement affects convergence.

## Stop reasons

The runtime must distinguish semantic convergence from operational stopping.

Allowed stop reasons include:

- `convergence`
- `resource_cap`
- `model_error`
- `tool_error`
- `runtime_error`
- `user_stop`

A configured maximum wave count is only a resource safety limit.

Reaching a resource limit must never be reported as semantic convergence.

## Controller decision

The controller should return a convergence assessment based on:

1. the active Skill;
2. the supplied runtime measurements;
3. the unresolved evidence state.

The controller must not claim convergence merely because the current wave
completed successfully.

## Runtime record

The runtime should record a generic structure such as:

{
  "converged": false,
  "stop_reason": null,
  "wave_count": 1,
  "distinct_sources_read": 0,
  "unique_verified_sources": 0,
  "running_claim_count": 0,
  "novel_claim_counts": [],
  "novelty_ratios": [],
  "unresolved_gap_count": 0
}

The meaning of these measurements is interpreted according to the active
Skill.
