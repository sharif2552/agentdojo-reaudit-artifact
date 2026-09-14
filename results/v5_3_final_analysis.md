# Final OpenRouter Tool Filter Analysis

Status: **FINAL_STOPPED_WITH_EXPLICIT_MISSINGNESS**

Coverage: 1431/1540 usable cells (92.9%); 109 unresolved infrastructure outcomes.

All estimates use completed defense-paired cells only. Repetitions were not performed, and model aliases did not expose immutable backend revisions.

## Paired contrasts

Deltas are Tool Filter minus no defense. Holm correction is applied within outcome across the ten configurations.

| Model configuration | Family | BU pairs | BU delta | UA pairs | UA delta | ASR pairs | ASR delta |
|---|---|---:|---:|---:|---:|---:|---:|
| cohere/north-mini-code:free | Cohere | 5/17 | -100.0% | 17/60 | -47.1% | 17/60 | -17.6% |
| dots-studio/dots-3-note-preview:free | dots | 17/17 | -64.7% | 60/60 | -3.3% | 60/60 | -46.7% |
| minimax/minimax-m2.7:free | MiniMax | 16/17 | -43.8% | 46/60 | -37.0% | 46/60 | -10.9% |
| minimax/minimax-m3:free | MiniMax | 17/17 | -52.9% | 54/60 | -70.4% | 54/60 | 0.0% |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | NVIDIA Nemotron | 17/17 | -70.6% | 56/60 | -80.4% | 56/60 | -3.6% |
| nvidia/nemotron-3-super-120b-a12b:free | NVIDIA Nemotron | 16/17 | -100.0% | 58/60 | -27.6% | 58/60 | -32.8% |
| nvidia/nemotron-3-ultra-550b-a55b:free | NVIDIA Nemotron | 16/17 | -68.8% | 58/60 | -65.5% | 58/60 | 0.0% |
| nvidia/nemotron-3.5-lightning:free | NVIDIA Nemotron | 17/17 | -94.1% | 57/60 | -54.4% | 57/60 | -24.6% |
| poolside/laguna-s-2.1:free | Poolside | 16/17 | -56.2% | 58/60 | -69.0% | 58/60 | -13.8% |
| poolside/laguna-xs-2.1:free | Poolside | 15/17 | -80.0% | 54/60 | -59.3% | 54/60 | -11.1% |

## Interpretation boundary

The 109 unresolved cells remain infrastructure missingness, not task failures. Complete-case contrasts are accompanied by planned-denominator bounds in the JSON artifact; results are reported by configuration and are not pooled as independent model samples.