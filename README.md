# AgentDojo prompt-injection defense re-audit

This repository is the minimal reproducibility artifact for our AgentDojo Workspace re-audit. It contains the sanitized inputs and deterministic analysis code required to reproduce the reported Groq and OpenRouter results without provider access.

## Reproduce

Requirements: Git and Python 3.10 or newer. The analysis uses only Python's standard library.

```sh
git clone https://github.com/sharif2552/agentdojo-reaudit-artifact.git
cd agentdojo-reaudit-artifact
./reproduce.sh
```

The command regenerates both final analyses, validates the public release boundary, and checks that regenerated outputs match the committed results.

## Expected results

| Cohort | Planned cells | Usable outcomes | Unresolved | Excluded ambiguous completions |
|---|---:|---:|---:|---:|
| Groq balanced panel | 1,096 | 879 | 215 | 2 |
| OpenRouter v5.3 | 1,540 | 1,431 | 109 | 0 |

Operational failures remain missing outcomes rather than being converted into model successes or failures. API retries are not treated as scientific replicates.

## Contents

```text
code/       deterministic analysis and release validation
protocols/  frozen analysis plans and documented amendments
results/    sanitized ledgers, planned cells, and final outputs
```

The two `release_attempts_*.jsonl` files are compact research ledgers. They retain experimental conditions, statuses, native scores, pairing identifiers, timestamps, and provenance hashes. They exclude prompts, messages, tool outputs, full environment states, raw provider payloads, credentials, and account identifiers.

## Scope

Only the materials required for provider-stratum reproduction are included. Compact ledgers replace full execution transcripts and raw provider responses. Credentials, `.env` files, account data, logs, caches, and exploratory runs are outside the release boundary.

The source-audit result is provided as `results/workspace_injection_vector_audit.json`. Experiment methods and stopping decisions are recorded in `protocols/`.

## Citation

Use the repository's `CITATION.cff` metadata and cite the accompanying paper when available.

## License

Code and documentation are available under the MIT License (`LICENSE`). Sanitized research data and derived results are available under CC BY 4.0 (`LICENSE-DATA`).
