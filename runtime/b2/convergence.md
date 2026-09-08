# B2 Convergence Policy

## Skill convergence

Research is considered converged only when the active Skill's convergence conditions are satisfied.

For the current deep-research Skill, the controller should evaluate:

- at least 10 distinct sources have been read across all waves;
- the last 2 consecutive waves each added fewer than 15% novel claims relative to the running claim total.

The runtime must record the actual reason research stopped.

## Novel claim

A novel claim is a materially new factual finding that was not already represented in the running claim set.

A wording variation of an existing claim is not novel.

## Do not fake convergence

The following are not convergence:

- timeout;
- model error;
- tool error;
- reaching the configured maximum wave count;
- reaching a cost or runtime limit.

These must be recorded separately.

## Runtime safety cap

The B2 experiment may define max_waves as a resource safety limit.

If max_waves is reached before Skill convergence:

stop_reason = "resource_cap"

not:

stop_reason = "convergence"

## Output record

The runtime should record:

{
  "converged": false,
  "stop_reason": "resource_cap",
  "unique_verified_sources": 0,
  "running_claim_count": 0,
  "novel_claim_counts": [],
  "novelty_ratios": []
}
