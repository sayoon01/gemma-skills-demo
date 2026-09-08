# B2 Evidence Verification Contract

## Purpose

Validate research-worker output before it can be aggregated by the controller.

Worker output is untrusted until it passes this verification stage.

## Verification principle

A citation is not valid merely because the worker returned a URL.

A source must have actually been read by the runtime.

A successfully fetched URL is necessary but not sufficient.

The retrieved content must also be relevant to the claim it is supposed to support.

## Verification states

Each worker source must receive one state:

- VERIFIED
- UNREAD
- FETCH_FAILED
- CONTENT_MISMATCH
- INSUFFICIENT_SUPPORT

### VERIFIED

Use VERIFIED only when:

1. the source was actually read by the worker runtime;
2. the retrieved source corresponds to the cited source;
3. the retrieved content contains evidence relevant to the claim.

### UNREAD

The worker cited a URL or file that was never actually read.

UNREAD sources must not be passed to final synthesis.

### FETCH_FAILED

The runtime attempted to read the source but failed.

Examples:

- HTTP error;
- 404;
- blocked page;
- unsupported content.

FETCH_FAILED sources must not be treated as evidence.

### CONTENT_MISMATCH

The requested URL was successfully fetched, but the retrieved document is not the source that the worker thought it was.

Examples:

- incorrect paper ID;
- wrong product page;
- different version;
- unrelated article.

CONTENT_MISMATCH sources must be rejected.

### INSUFFICIENT_SUPPORT

The source was correctly fetched, but the retrieved text does not sufficiently support the associated claim.

The source may remain useful as a lead but cannot support that claim.

## Claim validation

A worker claim can be:

- TRIANGULATED
- SINGLE_SOURCE
- UNSUPPORTED
- CONFLICTING

### TRIANGULATED

At least two independent VERIFIED sources support the material claim.

### SINGLE_SOURCE

Exactly one VERIFIED independent source supports the claim.

### UNSUPPORTED

No VERIFIED source supports the claim.

Do not pass an unsupported claim as a factual finding.

### CONFLICTING

Verified sources materially disagree.

Preserve the disagreement for controller review.

## Independence

Source independence primarily means different organizations or publishers.

Multiple URLs from the same organization do not automatically count as independent sources.

## Runtime boundary

The verifier must not invent missing evidence.

It may:

- reject invalid evidence;
- downgrade claims;
- identify gaps;
- request targeted follow-up research.

It must not silently repair a factual claim using model memory.

## Output

Return or store a validated evidence object containing:

- accepted claims;
- rejected sources;
- unsupported claims;
- single-source claims;
- conflicts;
- verification gaps.

Only accepted VERIFIED evidence may enter the Evidence Pack.

## Semantic audit output

When performing semantic verification, return one valid JSON object only.

Do not perform new web searches.

Judge only the claims and retrieved source contents supplied in the audit packet.

Schema:

{
  "claims": [
    {
      "claim_id": "C001",
      "verdict": "TRIANGULATED",
      "reason": "brief explanation",
      "evidence": [
        {
          "evidence_id": "C001-E001",
          "state": "VERIFIED",
          "reason": "why the retrieved content does or does not support the claim",
          "audited_source_type": "academic_paper",
          "audited_tier": 2
        }
      ]
    }
  ],
  "quality_flags": [
    {
      "type": "SOURCE_CLASSIFICATION",
      "target_id": "C001-E001",
      "message": "brief issue"
    }
  ]
}

Allowed evidence states:

- VERIFIED
- CONTENT_MISMATCH
- INSUFFICIENT_SUPPORT

Allowed claim verdicts:

- TRIANGULATED
- SINGLE_SOURCE
- UNSUPPORTED
- CONFLICTING

Rules:

- `VERIFIED` means the retrieved content itself materially supports the claim.
- A matching URL alone is not enough.
- If the retrieved document is unrelated to the expected source, use `CONTENT_MISMATCH`.
- If the correct source was retrieved but its contents do not sufficiently support the claim, use `INSUFFICIENT_SUPPORT`.
- Determine source quality using the active Skill's source-tier rules.
- Do not trust the worker's source_type or tier without checking.
- Do not add new URLs or evidence.
- Do not use general model knowledge to repair a weak claim.
- Return one JSON object only, with no Markdown before or after it.

## Whole-claim support rule

Semantic verification applies to the complete claim exactly as written.

A source may be marked `VERIFIED` for a claim only when the retrieved content materially supports every important factual component of that claim.

If the source supports only part of a compound claim:

- do not mark the evidence `VERIFIED`;
- mark it `INSUFFICIENT_SUPPORT`;
- explain which portion is supported and which portion is not.

Examples of insufficient support include:

- one product example being used to establish an industry-wide trend;
- evidence for one technology being used to support another technology mentioned in the same claim;
- evidence for one product version being generalized to other versions;
- evidence for a component feature being used to support a broader commercialization conclusion.

Do not use `worker_support` text itself as evidence.

Only the actual `retrieved_source.content` may establish factual support.

## Claim-verdict consistency

Claim verdicts must be consistent with evidence states.

- 0 `VERIFIED` evidence items => `UNSUPPORTED`
- exactly 1 `VERIFIED` evidence item => `SINGLE_SOURCE`
- 2 or more independent `VERIFIED` evidence items => `TRIANGULATED`
- materially disagreeing verified evidence => `CONFLICTING`

`CONTENT_MISMATCH` and `INSUFFICIENT_SUPPORT` do not count as verified evidence.

Do not return a verdict that contradicts the evidence-state counts above.
