# v5.3b Provider-Failure Recovery Amendment

Date: 2026-09-03

The original v5.3 runner exhausted eight attempts with 985 of 1,540 cells completed.
Post-run diagnosis found that unresolved cells included provider quota failures and
empty OpenAI-compatible responses whose `choices` field was null. AgentDojo indexed
`choices[0]`, so the latter appeared as a generic harness `TypeError`.

The raw append-only ledger is preserved. This amendment reopens only cells whose
latest result is a rate limit, provider error, the exact historical null-choices
crash, or an upstream `Provider returned error`. Genuine `invalid_model_output`
records are not reopened. New null/empty-choices responses are classified as
`provider_error` at the client boundary. Each invocation gives a recovery cell one
new attempt, with an amended ceiling of 30 total attempts, and stops after a batch
that produces no new completion.

The amendment, policy, runner, supervisor, tests, original manifest, and plan are
hash-frozen before recovery calls. Existing completed cells are never rerun.
