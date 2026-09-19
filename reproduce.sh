#!/bin/sh
set -eu

repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$repo_dir"

if command -v python3 >/dev/null 2>&1; then
  python_bin=python3
elif command -v python >/dev/null 2>&1; then
  python_bin=python
else
  echo "Python 3.10 or newer is required." >&2
  exit 1
fi

"$python_bin" code/analyze_results_v5_1_balanced.py
"$python_bin" code/analyze_results_v5_3.py
"$python_bin" code/validate_release.py

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git diff --exit-code -- results/v5_1_balanced_final_analysis.json \
    results/v5_1_balanced_final_analysis.md \
    results/v5_3_final_analysis.json \
    results/v5_3_final_analysis.md
fi

printf '%s\n' 'Reproduction complete: generated analyses match the committed results.'
