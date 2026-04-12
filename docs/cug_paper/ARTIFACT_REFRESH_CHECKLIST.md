# CUG Paper Artifact Refresh Checklist

This checklist freezes the paper-facing artifact refresh work after M4
retrieval reruns and three-judge rescoring.

## Scope Freeze

- Table 2 remains an 8-row table.
- The six Chroma/no-tool LangChain rows and the two filesystem rows are all
  first-class comparison rows for the paper.
- Retrieval-backed rows should be sourced from the M4 derived-ticket corpus
  artifact set, not mixed M2/M3 retrieval artifacts.
- No-tool rows remain sourced from `results/cug_m2_canonical`.

## Canonical Artifact Sources

### Main Results Table

- no-tool rows:
  - `results/cug_m2_canonical`
- retrieval-backed rows:
  - `results/cug_m4`

Rows expected in the regenerated table:

- `lang_gptoss_base`
- `lang_sonnet_base`
- `lang_gptoss_filesystem`
- `lang_sonnet_filesystem`
- `lang_gptoss_chroma`
- `lang_sonnet_chroma`
- `lang_gptoss_chroma_opt`
- `lang_sonnet_chroma_opt`

### Variance Figure

- source artifact:
  - `results/cug_m4_var`
- configs:
  - `cug_lang_chroma_gptoss_opt__gptoss__92b1c395`
  - `cug_lang_chroma_sonnet_opt__claude_sonnet__40d3aaa3`

### Harness Comparison Table

- GPT-OSS ATHOS mini harness rows:
  - `results/cug_m4_harness`
- Sonnet ATHOS mini harness rows:
  - `results/cug_m4_harness_lang_sonnet_opt_mini_20260329`
  - `results/cug_m4_harness_smol_sonnet_mini_20260329`
- external coding-agent rows:
  - `results/cug_codex_external_full_20260329`
  - `results/cug_claude_external_full_20260329`

### Judge Sensitivity Tables

- paper-scope main rows:
  - `results/cug_m2_canonical`
  - `results/cug_m4`
- optional auxiliary evidence:
  - `results/cug_m4_harness`
  - `results/cug_m4_harness_lang_sonnet_opt_mini_20260329`
  - `results/cug_m4_harness_smol_sonnet_mini_20260329`
  - `results/cug_codex_external_full_20260329`
  - `results/cug_claude_external_full_20260329`

Judges expected:

- `llama_4_maverick`
- `mistral_large_3`
- `gptoss`

## Regeneration Order

1. Regenerate Table 2 from `config/paper/cug_paper_table_sources.txt`.
2. Regenerate variance plots from `results/cug_m4_var`.
3. Regenerate the harness/external comparison table from the M4 harness and
   full external comparison artifacts.
4. Regenerate judge-sensitivity tables from the finalized three-judge M4
   paper-scope artifacts.
5. Update manuscript prose in `../athos_cug_2026_paper/sections/5_results.tex`
   to match the regenerated assets.
6. Run a final consistency pass so no pre-M4 retrieval-backed values remain in
   the manuscript text, tables, or captions.

## Verification Checklist

- `tables/cug_results_per_config.tex` contains 8 rows, not 6.
- the two filesystem rows come from `results/cug_m4`, not pre-M4 directories.
- no-tool rows still match `results/cug_m2_canonical`.
- variance figure reflects post-M4 behavior for both GPT-OSS and Sonnet.
- harness comparison uses the M4 Sonnet harness refresh and the full M4
  external comparisons rather than the older mini-only external rows.
- judge-sensitivity tables are derived from the same paper-scope artifact set
  cited in the manuscript.
- every numeric claim in `sections/5_results.tex` matches a regenerated table
  or figure.
