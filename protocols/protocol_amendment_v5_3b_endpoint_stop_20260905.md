# v5.3b Endpoint-Unavailability Stop Amendment

Date: 2026-09-05

The v5.3 OpenRouter recovery phase is stopped with incomplete coverage. At the
decision point, 1,431 of 1,540 planned cells had one valid completed result, 103
cells were already terminal or retry-exhausted, and six cells remained formally
retryable. All six retryable cells used `poolside/laguna-xs-2.1:free` and had
repeatedly received HTTP 429 responses. Attempts ranged from 20 to 26 after a
single-cell, single-worker probe also received an upstream shared-pool 429 while
the OpenRouter account endpoint remained healthy.

No completed result is removed and no unresolved cell is converted into a model
failure. The six stopped cells are classified as infrastructure-missing and join
the other unresolved cells only for coverage, missingness, and sensitivity
analysis. Primary outcome denominators contain valid completed cells only. Paired
defense comparisons require valid outcomes for both members of a pair.

The stop decision prevents repeated endpoint-specific retries from consuming the remaining frozen
30-attempt allowance without evidence that the shared upstream endpoint is
available. The discontinued cells may not be silently rerun or replaced by a
different model. Any later endpoint recovery study must be separately versioned
and cannot be merged into this confirmatory snapshot.

The machine-readable decision, exact affected cells, latest statuses, attempts,
and source hashes are recorded in `results/v5_3_recovery_stop.json`. The scheduled
task `V5_3_ToolFilter_Supervisor` was disabled when this amendment was adopted.
