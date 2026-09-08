# B2 Source Independence Contract

## Purpose

Evaluate whether VERIFIED evidence sources supporting the same factual
claim family are genuinely independent.

Do not perform new research.

Use only the supplied source metadata, excerpts, retrieved content,
publisher information, and claim-family relationships.

Independence is not determined by URL count alone.

## Claim family

Claims linked by a SAME semantic relation represent one factual claim family.

Evidence attached to every member of that SAME family may be considered
together when evaluating triangulation.

Do not combine CONTRADICTS claims into one supporting evidence family.

## Independence relations

For every supplied pair of distinct VERIFIED sources, assign exactly one:

### INDEPENDENT

Use when the sources represent meaningfully separate publisher,
organization, reporting, research, or evidence origins.

Different organizations may be independent even when discussing the same
event or technology, if one is not merely copying, translating,
syndicating, or deriving its factual support from the other.

### DEPENDENT

Use when the two sources are not genuinely independent.

Examples include:

- the same publisher or organization;
- translated or mirrored versions of the same publication;
- syndication or republication;
- one source explicitly deriving the relevant factual claim from the other;
- both items merely repeating the same single underlying report,
  announcement, press release, or unnamed origin without separate
  verification.

### UNKNOWN

Use when the supplied material is insufficient to determine independence.

Do not guess independence merely because domains or publisher names differ.

## Provenance sufficiency rule

Different publisher names, domains, article titles, or source categories
alone are not sufficient evidence of independence.

For an INDEPENDENT judgment, the supplied material must provide a reasonable
basis to conclude that the relevant factual support originates independently.

If two secondary reports discuss the same company announcement, event,
product launch, press release, unnamed industry source, or other common
underlying origin, and the supplied material does not establish separate
verification or separate primary provenance, return UNKNOWN rather than
INDEPENDENT.

When provenance cannot be established from the supplied evidence packet,
prefer UNKNOWN over guessing independence.

## Source quality

Independence and quality are separate judgments.

A pair of low-quality sources may be independent while still being weak
evidence.

Preserve source types and tiers for later re-planning and synthesis.

Do not upgrade source quality merely because sources are independent.

## Family verdict

For every claim family return exactly one:

### TRIANGULATED

Use only when the supplied VERIFIED evidence contains at least two
meaningfully independent source origins supporting the factual claim family.

### NOT_TRIANGULATED

Use when the evidence does not contain two independent origins and the
dependency can be determined from the supplied material.

### UNKNOWN

Use when independence cannot be established or rejected from the supplied
material.

## Conflicts

This step does not resolve factual contradictions.

If evidence belongs to a CONTRADICTS relation, preserve that contradiction
for later synthesis and re-planning.

## Output

Return JSON only.

{
  "families": [
    {
      "family_ref": "SG01:C001",
      "claim_refs": [
        "SG01:C001",
        "SG04:C001"
      ],
      "pairwise": [
        {
          "source_a_ref": "S001",
          "source_b_ref": "S002",
          "relation": "INDEPENDENT",
          "reason": "brief provenance-based reason"
        }
      ],
      "verdict": "TRIANGULATED",
      "independent_verified_source_count": 2,
      "reason": "brief family-level reason"
    }
  ]
}

Every supplied family must appear exactly once.

Every supplied source pair within a family must appear exactly once.

Do not invent, omit, rename, merge, or split family refs or source refs.
