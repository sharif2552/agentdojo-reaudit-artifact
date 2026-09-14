# v5.1f Balanced Free-Tier Completion Amendment

Date: 2026-09-03

The 13,920-cell Groq census is discontinued because free-tier token limits caused
severe, condition-dependent missingness. No existing record is deleted.

Confirmatory completion is restricted to a 1,096-cell panel containing the two
GPT-OSS models, all four frozen defenses, and both frozen attack templates. The
panel uses the benign tasks, security tasks, and injection tasks already recorded
in `results/design_v5_3.json`. That selection was frozen before this amendment and
before the latest Groq recovery outcomes, preventing outcome-based cherry-picking.

The panel contains 17 benign tasks and 10 security tasks crossed with six injection
tasks. At amendment preparation, 369 panel cells had a valid completion and 727 did
not. Only incomplete panel cells with rate-limit, timeout, transport, or provider
failures may be retried, up to 30 total attempts. Invalid model output and harness
failures remain visible and are not silently converted to completed results.

Groq is used only to complete this pre-existing matched panel. Any later experiment
expansion will be a separately frozen OpenRouter stratum. Provider strata will not
be silently pooled.
