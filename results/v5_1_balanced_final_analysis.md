# Final Groq Balanced-Panel Analysis

Status: **FINAL_STOPPED_WITH_EXPLICIT_MISSINGNESS**

Coverage: 879/1096 usable cells (80.2%); 2 ambiguous cells excluded; 215 unresolved.

## Native outcomes

| Model | Defense | BU | UA | ASR | Coverage |
|---|---|---:|---:|---:|---:|
| openai/gpt-oss-120b | no_defense | 12/13 (92.3%) | 59/86 (68.6%) | 16/86 (18.6%) | 99/137 |
| openai/gpt-oss-120b | repeat_user_prompt | 13/15 (86.7%) | 73/90 (81.1%) | 5/90 (5.6%) | 105/137 |
| openai/gpt-oss-120b | spotlighting_with_delimiting | 12/13 (92.3%) | 62/89 (69.7%) | 13/89 (14.6%) | 102/137 |
| openai/gpt-oss-120b | tool_filter | 1/17 (5.9%) | 7/117 (6.0%) | 0/117 (0.0%) | 134/137 |
| openai/gpt-oss-20b | no_defense | 10/14 (71.4%) | 61/89 (68.5%) | 10/89 (11.2%) | 103/137 |
| openai/gpt-oss-20b | repeat_user_prompt | 11/14 (78.6%) | 66/95 (69.5%) | 7/95 (7.4%) | 109/137 |
| openai/gpt-oss-20b | spotlighting_with_delimiting | 11/14 (78.6%) | 56/94 (59.6%) | 15/94 (16.0%) | 108/137 |
| openai/gpt-oss-20b | tool_filter | 2/17 (11.8%) | 5/102 (4.9%) | 0/102 (0.0%) | 119/137 |

## Paired contrasts

All deltas are comparison defense minus no defense on complete matched pairs.

### openai/gpt-oss-120b

| Phase | Defense | Complete pairs | Utility delta | Utility Holm p | ASR delta | ASR Holm p |
|---|---|---:|---:|---:|---:|---:|
| benign | repeat_user_prompt | 13/17 | -7.7% | 1 | N/A | N/A |
| benign | spotlighting_with_delimiting | 12/17 | 0.0% | 1 | N/A | N/A |
| benign | tool_filter | 13/17 | -84.6% | 0.00293 | N/A | N/A |
| injection | repeat_user_prompt | 79/120 | 10.1% | 0.2306 | -11.4% | 0.007812 |
| injection | spotlighting_with_delimiting | 81/120 | 0.0% | 1 | -2.5% | 0.5 |
| injection | tool_filter | 86/120 | -60.5% | 1.832e-14 | -18.6% | 9.155e-05 |

### openai/gpt-oss-20b

| Phase | Defense | Complete pairs | Utility delta | Utility Holm p | ASR delta | ASR Holm p |
|---|---|---:|---:|---:|---:|---:|
| benign | repeat_user_prompt | 13/17 | 0.0% | 1 | N/A | N/A |
| benign | spotlighting_with_delimiting | 13/17 | 7.7% | 1 | N/A | N/A |
| benign | tool_filter | 14/17 | -57.1% | 0.06445 | N/A | N/A |
| injection | repeat_user_prompt | 80/120 | 1.2% | 1 | -5.0% | 0.5781 |
| injection | spotlighting_with_delimiting | 79/120 | -7.6% | 0.5264 | 5.1% | 0.5781 |
| injection | tool_filter | 78/120 | -62.8% | 1.386e-13 | -10.3% | 0.02344 |

## Interpretation boundary

Operational and provider failures are missing outcomes, not model task failures. Complete-case estimates must be read with the planned-denominator bounds in the JSON artifact.
