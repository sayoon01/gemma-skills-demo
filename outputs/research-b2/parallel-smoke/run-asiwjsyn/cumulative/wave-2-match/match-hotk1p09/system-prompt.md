# Active Agent Skill

Use the following public Skill as the primary research-method specification.

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

# Cumulative Claim Merge Contract

# B2 Cumulative Claim Merge Contract

## Purpose

Compare newly validated claims from the latest research wave against
the previously validated cumulative claim set.

This step determines whether a new claim represents:

- an already represented factual finding;
- a material extension of an existing finding;
- meaningful counter-evidence or contradiction;
- a genuinely new factual finding.

Do not perform new research.

Use only the claims and evidence state supplied in the input.

## Relations

For each new claim, assign exactly one primary relation.

### SAME

The new claim expresses substantially the same factual finding as one or more
existing claims.

Minor wording differences, paraphrases, or equivalent numerical statements
do not make a claim novel.

### EXTENDS

The new claim overlaps an existing claim but adds factual detail, scope,
conditions, dates, values, mechanisms, deployment information, or another
materially useful fact.

An EXTENDS relation may or may not contain a materially novel finding.

Decide `is_novel` separately.

### CONTRADICTS

The new claim materially conflicts with, corrects, narrows, or provides
counter-evidence against an existing claim.

Do not hide contradictions by labeling them as SAME.

Counter-evidence must remain visible to later synthesis and re-planning.

### NOVEL

The new claim contains a materially new factual finding that is not already
represented by any existing validated claim.

## Novelty decision

For every new claim return `is_novel`.

`is_novel` is true only when the latest wave contributes a materially new
factual finding that was not already represented in the prior cumulative
claim set.

A wording variation alone is not novel.

An EXTENDS claim may be novel when the added factual content is material.

A CONTRADICTS claim may be novel when it introduces materially new
counter-evidence.

Do not infer novelty from source count or claim ID.

## Matching

`matched_prior_claim_refs` must contain only claim references supplied in the
prior cumulative set.

It may contain multiple prior claims when the new claim overlaps with more
than one existing finding.

For a NOVEL claim with no meaningful prior match, return an empty list.

## Output

Return JSON only.

{
  "comparisons": [
    {
      "new_claim_ref": "SG04:C001",
      "relation": "SAME",
      "matched_prior_claim_refs": [
        "SG01:C001"
      ],
      "is_novel": false,
      "reason": "brief semantic justification"
    }
  ]
}

Every supplied new claim must appear exactly once.

Do not invent, omit, rename, merge, or split claim IDs.

