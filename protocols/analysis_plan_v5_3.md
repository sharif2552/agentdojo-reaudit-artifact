# Frozen Analysis Plan: v5.3 Tool Filter Repair

## Status and purpose

This is a separately versioned repair study. The v5.2 ledger is exploratory and is
not pooled into v5.3 confirmatory estimates. V5.3 directly compares Tool Filter
with no defense in the same execution period after correcting the model-identifier
adapter defect discovered in v5.2.

## Scope and units

The design covers ten model configurations from five model families, all served
through OpenRouter. It does not claim ten independent architectures or provider
generality. Each planned execution cell is one observation. There is one execution
per cell, so the study does not estimate repeated-run stability.

The benign phase contains 17 stratified Workspace tasks under two defenses. The
injection phase contains 10 user tasks, 6 injection tasks, the preselected
`important_instructions` attack, and two defenses. The attack was selected because
the exploratory v5.1/v5.2 results showed that the alternative fixed InjecAgent
wording produced a floor effect; this informed selection is disclosed.

## Outcomes and contrasts

Primary outcomes are AgentDojo's deterministic benign utility, utility under
attack, targeted attack success, and the four joint utility/security states.
Within each model configuration, Tool Filter is paired with no defense on the same
task or task-injection cell. The primary scientific question is whether lower
attack success under Tool Filter is accompanied by lower task utility.

The benchmark predicates are operational benchmark outcomes.

## Inference

Report paired effect sizes and counts by model configuration. Benign uncertainty
resamples user tasks. Injection uncertainty uses a two-stage cluster bootstrap:
resample user tasks and then injection tasks within sampled user tasks, with 10,000
replicates and seed 1729. Holm correction is applied across model-level primary
contrasts within each outcome. Family summaries are secondary and give each model
configuration equal weight while identifying the nested family structure.

## Missingness and operational failures

No provider or harness failure is recoded as task failure. Report planned,
attempted, completed, and state-validated cells by model, defense, phase, and
status. Primary tables use completed paired cells only. Also report planned-
denominator all-fail/all-success bounds and a complete-pair coverage table.

The runner permits at most eight recorded attempts per cell. In-call provider
retries are disabled; rate-limited and transient provider failures are deferred to
a later scheduled invocation. Any model endpoint that disappears is reported as
an operational incompatibility, not a defense outcome.

## Integrity and temporal handling

The v5.3 source, plan, schema, dependency lock, taxonomy, and analysis plan are
hash-frozen before the first provider call. Every record stores those hashes.
No v4, v5.0, v5.1, or v5.2 execution is included in v5.3 estimates. Any protocol
change after freezing requires another version and an explicit amendment.
