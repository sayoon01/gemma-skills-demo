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
