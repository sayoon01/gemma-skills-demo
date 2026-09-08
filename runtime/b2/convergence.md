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
