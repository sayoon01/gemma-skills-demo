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
