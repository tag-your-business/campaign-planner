---
description: Senior prompt review of a prompt file or a directory of prompts — three-part weighted report
argument-hint: <prompt-file.yaml | prompts-directory>
---

Act as a senior prompt reviewer and review the prompt(s) at: $ARGUMENTS

## Resolving the target

- If `$ARGUMENTS` is empty, ask the user which prompt file or directory to review before doing anything else.
- If the path is a **directory**, review every prompt file inside it (`*.yaml` / `*.yml` / `*.md` / `*.txt` prompt variants) and rank them against each other.
- If the path is a **single file**, review that prompt only — rankings become absolute scores per parameter (strong / adequate / weak) instead of relative ranks.
- If the path does not exist, is ambiguous (e.g. matches multiple locations), or you cannot tell which files in a directory are prompts, ask the user — do not guess.

## Gathering context (ask when unclear)

Before reviewing, establish the context around the prompts. Look for it yourself first; if any of the following cannot be determined from the repo, **ask the user via a question at that point** instead of assuming:

1. **Feature**: which production feature consumes this prompt? Search `backend/app/` for the generator class that ships the equivalent system/user prompt (e.g. `app/features/generation/prompt.py`, `caption.py`). If no production counterpart is found, ask which feature the prompt was created for.
2. **Eval setup**: find the matching eval directory under `backend/tests/prompt/` (its `config.yaml`, `data/campaign_specs.json` or equivalent test data, and the metrics it enables from `backend/tests/prompt/framework/metrics.yaml`). If there is no matching eval config, ask whether one exists elsewhere or whether the review should proceed without eval context.
3. **Target model(s)**: read the model entries referenced by the eval `config.yaml` from `backend/tests/prompt/framework/providers.yaml` (temperature, max_tokens, reasoning behavior, pricing). If the config does not say which model the prompt targets, ask.
4. **Existing results**: read any `results/` outputs (comparison reports, per-prompt result JSONs) for measured evidence. Treat stale reports as stale — note their date/coverage.
5. **Test data interaction**: read the test profiles/specs the eval runs with, and check whether in-prompt examples overlap with test data (leakage).

## Review parameters

### Section 2 — industry-wide parameters (weight 60%)

Assess each prompt on:

1. Clarity & internal consistency (contradicting rules are the #1 failure — check placement/format rules especially)
2. Structure & format control (output format, section skeleton, delimiter discipline)
3. Reasoning & creativity mechanics (CoT/brainstorm devices, anti-cliché levers, homogenization risk from fixed menus)
4. Few-shot / example hygiene (representative, domain-neutral, no leakage into test data)
5. Robustness & graceful degradation (conditional "when provided" handling, missing fields, edge cases)
6. Model fit (temperature constraints, reasoning-token budget vs max_tokens, model idioms)
7. Cost efficiency (system-prompt token count vs quality gained; measured cost if results exist)
8. Measured performance (eval scores where available; note which variants are unmeasured)
9. Safety & inclusive representation
10. Maintainability & versioning (git-versioned, intent descriptions, production parity/drift)

Also list parameters **not assessable** with current evidence (injection resistance, cross-run variance, model portability, test-data sanity) rather than silently skipping them.

### Section 3 — project-specific fit (weight 40%)

Assess each prompt against this repo:

1. Alignment with the enabled eval metrics (and the Goodhart risk of encoding rubrics verbatim)
2. Coherence between the prompt and the user prompt the production code builds (e.g. `_build_user_prompt()` injections such as `model_branding` contact blocks — system vs user contradictions are critical findings)
3. Production parity — does shipped code in `backend/app/` match any reviewed variant, and is the shipped prompt itself sound?
4. Measured eval evidence and its freshness
5. Test-data interaction (sample size, leakage, profile coverage)
6. Judge observability — does the GEval judge receive enough context (`input`/`context` fields in `framework/evaluator.py`) to actually verify each metric?
7. Model config fit (`providers.yaml` entries: max_tokens headroom, extra_params)
8. Downstream readiness (e.g. the image cascade for image-prompt evals)

## Report format — three parts, in this order in the file, but WRITE Section 1 LAST

1. **Section 1 — Final Verdict**: ranking table combining Section 2 (60%) and Section 3 (40%) via weighted average of section ranks (lower = better). Columns: Final Rank | Prompt | Industry Rank (S2) | Project Rank (S3) | Weighted Score | Verdict (one line each). Note explicitly if the weighting changes the order vs either section alone, and state the conditions/caveats on the winner.
2. **Section 2 — Industry-wide parameters**: one table — Parameter | Short summary of findings | Winner (per-parameter best prompt; for a single file, a strong/adequate/weak grade) — followed by the not-assessable list, a single overall Section 2 winner, and the Section 2 ranking.
3. **Section 3 — Project-specific fit**: one table in the same shape (Dimension | Short summary | Winner), a Section 3 winner and ranking, and an ordered "Project actions required" list (production bugs first).

4. **Section 4 — Improvement Suggestions**: one subsection per reviewed prompt, each with concrete, actionable edits — quote the offending line and give the replacement wording where possible. Order suggestions within each prompt by impact. Include suggestions even for the winner; if a prompt should simply be retired, say so and skip cosmetic fixes for it.

Append a short per-version notes appendix (one bullet per prompt).

## Output

Write the report to `backend/tests/prompt/prompt_review/<target-name>_review_<YYYY-MM-DD>.md` (create the directory if missing; `<target-name>` = the directory or file stem being reviewed). Use `| --- |` style table separators and avoid unescaped pipes in cells. After writing, reply with the file path, the final ranking, and the top findings — including any production-code bugs discovered, which must be called out even though fixing them is out of scope for the review.