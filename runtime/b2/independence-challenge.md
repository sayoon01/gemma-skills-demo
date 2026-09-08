# B2 Independence Challenge Review

## Purpose

Adversarially review a previous source-independence audit.

The previous auditor may have incorrectly treated different publishers,
domains, article types, or writing styles as proof of independent provenance.

Do not perform new research.

Use only the supplied VERIFIED evidence packet and the previous audit.

## Core rule

Different publishers, organizations, domains, article titles, or source
categories are NOT by themselves sufficient proof of independent provenance.

A pair may be confirmed as independent only when the supplied material gives
a positive reason to believe that the relevant factual support comes from
separate evidence origins.

Examples of positive provenance may include:

- separate original research or datasets;
- separate primary observations;
- separate direct interviews or reporting;
- distinct official records;
- clearly independent technical analysis based on different underlying
  evidence.

If the packet merely shows two secondary publications repeating the same
event, announcement, company plan, product launch, press release, unnamed
industry source, or other potentially common origin, and separate provenance
cannot be established, return INSUFFICIENT_PROVENANCE.

When uncertain, prefer INSUFFICIENT_PROVENANCE rather than guessing.

## Pair verdicts

For each supplied pair return exactly one:

- CONFIRMED_INDEPENDENT
- DEPENDENT
- INSUFFICIENT_PROVENANCE

## Family verdict

Return exactly one:

- TRIANGULATED
- NOT_TRIANGULATED
- UNKNOWN

TRIANGULATED requires at least one CONFIRMED_INDEPENDENT pair.

UNKNOWN is appropriate when the supplied packet does not establish whether
two supporting sources are genuinely independent.

NOT_TRIANGULATED is appropriate when the supplied evidence establishes that
the candidate sources are dependent.

## Output

Return JSON only.

{
  "families": [
    {
      "family_ref": "SG01:C001",
      "pairwise": [
        {
          "source_a_ref": "S001",
          "source_b_ref": "S002",
          "verdict": "CONFIRMED_INDEPENDENT",
          "reason": "specific provenance-based justification"
        }
      ],
      "final_verdict": "TRIANGULATED",
      "reason": "family-level explanation"
    }
  ]
}

Every supplied family and every supplied source pair must appear exactly once.
Do not invent source refs, claim refs, or evidence.
