# Senior Prompt Review — `image_prompt` variants v1–v6

**Date:** 2026-07-03
**Scope:** `tests/prompt/image_prompt/prompts/prompt_v1.yaml` … `prompt_v6.yaml`, reviewed against the production generator (`app/features/generation/prompt.py`), the eval framework (`framework/evaluator.py`, `metrics.yaml`, `providers.yaml`), `image_prompt/config.yaml`, and existing results.

**Config at time of review:** only `prompt_v6` enabled, on `gpt5_4_mini` (gpt-5.4-mini, temperature locked at 1.0, max_tokens 1000, Responses API reasoning model), one profile (`profile_v1`: ABC Housing, real estate, Diwali, `model_branding: true`), 9 GEval metrics, image cascade on.

**Report structure:** Section 1 is the final verdict, derived from Section 2 (industry-wide parameters, weight 60%) and Section 3 (project-specific fit, weight 40%). Section 4 gives per-prompt improvement suggestions.

---

## Section 1 — Final Verdict

Weighted combination of the two rankings below (industry parameters 60%, project-specific fit 40%):

| Final Rank | Prompt | Industry Rank (S2) | Project Rank (S3) | Weighted Score¹ | Verdict |
| --- | --- | --- | --- | --- | --- |
| **1** | **v6** | 1 | 1 | 1.0 | Winner. Best structure and format control, best metric alignment. Ship after de-leaking the "belonging" example. |
| **2** | **v4** | 2 | 3 | 2.4 | Cleanest prompt of the six — no contradictions, best model fit under the 1000-token cap. The safe fallback if v6 shows truncation or homogenization. |
| **3** | **v5** | 3 | 2 | 2.6 | Good creativity mechanics and festive framing, but the silent brainstorm adds reasoning burden the current max_tokens may not afford. |
| 4 | v3 | 4 | 4 | 4.0 | Transitional fix; superseded by v4. |
| 5 | v1 | 5 | 5 | 5.0 | Production mirror; cheapest and measured-reliable, but contradicts its own user prompt when `model_branding` is true. |
| 6 | v2 | 6 | 6 | 6.0 | Self-contradictory on text placement, most expensive, measured failure on text_specification (33.3% success). Abandon. |

¹ Weighted score = 0.6 × S2 rank + 0.4 × S3 rank (lower is better).

Note: under this weighting, **v4 edges v5** — the industry-parameter view (clarity, model fit) favors v4, while only the project-specific view (festive_not_promotional metric alignment) favors v5. A pure project-fit ranking would order them v6 > v5 > v4.

**Conditions on the v6 win:** the verdict rests on n=1 test data and zero measured runs for v3–v6. Before treating v6 as final: fix the production contradiction in `prompt.py`, de-leak v6's housing example, add contact_info to the judge context, enable all three profiles, and run v4–v6 head-to-head (details in Section 3).

---

## Section 2 — Review Against Industry-Wide Parameters (weight 60%)

Each prompt was assessed on parameters commonly used across the industry to review prompts (clarity, structure, reasoning mechanics, example hygiene, robustness, model fit, cost, measured performance, safety, maintainability).

| # | Parameter | Short summary of findings | Winner |
| --- | --- | --- | --- |
| 1 | Clarity & internal consistency | v2 states text placement three ways, two contradicting its own "no placement" rule; v1/v3 carry smaller edge-constraint clashes; v4 is the cleanest with zero contradictions; v6 close behind. | **v4** |
| 2 | Structure & format control | All six share the 5-section skeleton. v6's literal contact pattern (website/address joined on the bottom edge, phone/email top right) and its "placement lives only in TEXT, never in CONSTRAINTS" rule give the tightest format control. | **v6** |
| 3 | Reasoning & creativity mechanics | v1–v3 have none. v4 adds a negative-only "reject the first idea" rule; v5 adds brainstorm-three-discard-one (the proven technique); v6 adds concrete angle levers but a fixed menu of four risks becoming the new cliché. | **v5** |
| 4 | Few-shot / example hygiene | v2's good-vs-bad brand-color examples are domain-neutral and instructive — best practice. v6's "'belonging' for a housing firm" example leaks into the only enabled test profile (real estate) — worst practice. | **v2** (worst: v6) |
| 5 | Robustness & graceful degradation | v3–v6's "when provided" conditionals degrade gracefully when contact info is absent; v1/v2 break structurally when it is present. No paraphrase or edge-case sweep was run — structural assessment only. | **v6** |
| 6 | Model fit (gpt-5.4-mini) | Temperature is locked at 1.0 and max_tokens 1000 covers reasoning + output combined. v5/v6's silent-thinking instructions raise truncation risk; v2 is the longest prompt; v4 delivers the concept rule with the least reasoning burden. | **v4** |
| 7 | Cost efficiency | Measured: v1 $0.0049 vs v2 $0.0079 per case (~60% premium). v4–v6 are unmeasured but mid-length; every system-prompt token is paid on every call. | **v1** |
| 8 | Measured performance | Only v1 and v2 have data. v2 won 4/6 metrics on means but collapsed to 33.3% success on text_specification; v1 held 100% success on all metrics. v3–v6 are unmeasured. | **v1** |
| 9 | Safety & inclusive representation | Only v2 carries an explicit inclusive-representation rule. None address culturally sensitive event handling. | **v2** |
| 10 | Maintainability & versioning | All variants are versioned in git with intent descriptions — good practice. v1 is the only one with production parity, but the production prompt it mirrors is itself broken. | **v1** (nominal) |

**Parameters not assessable with current evidence** (industry-standard checks the project setup cannot yet answer):

- **Prompt-injection resistance** — company-supplied fields (name, address) are interpolated into the user prompt untested against adversarial content. No variant addresses it.
- **Cross-run consistency / variance** — n=1 at temperature 1.0 gives zero stability information; a 0.9 score once could be 0.6 on the next run.
- **Model portability** — assessed for gpt-5.4-mini only; behavior under the Anthropic/NVIDIA providers that `ProviderFactory` supports is unknown.
- **Data sanity** — the test spec dates Diwali to 2026-06-30 (Diwali falls in autumn); judge metrics anchored on event correctness could be skewed.

**Section 2 verdict (one among all parameters):** **v6** — it wins or places near the top on the heavyweight parameters (structure, robustness, clarity) and its two losses (example hygiene, model fit) are fixable with a one-line example swap and a config token bump.

**Section 2 ranking: v6 > v4 > v5 > v3 > v1 > v2.**

---

## Section 3 — Review Against Project-Specific Fit (weight 40%)

Assessment against this project's eval framework, test data, model config, and backend production code.

| # | Dimension | Short summary of findings | Winner |
| --- | --- | --- | --- |
| 1 | Eval metric alignment (9 GEval metrics) | v6 encodes the rubrics of `concept_originality`, `festive_not_promotional`, and `contact_text_placement` nearly verbatim; v5 covers two of the three; v1/v2 fail `contact_text_placement` by design. Caveat: rubric-encoding means those metrics now measure instruction-following, not quality (Goodhart risk) — the `image/` cascade eval becomes the real signal. | **v6** |
| 2 | Coherence with `_build_user_prompt()` | profile_v1 sets `model_branding: true`, so the user prompt injects contact placement. v1/v2's "no company information" CONSTRAINTS directly contradict it; v3 resolves it ambiguously; v4–v6 resolve it cleanly. | **v6** |
| 3 | Production parity (`app/features/generation/prompt.py`) | v1 mirrors shipped code exactly — but that code carries the same system-vs-user contradiction live in production (`prompt.py:39` vs `prompt.py:196-209`). Parity with a broken prompt is a flag, not a win. | **v1** (nominal) |
| 4 | Measured eval evidence | Only a stale v1-vs-v2 run exists (`comparison_report.md` still names v2 the winner despite its 33.3% text_specification success). Running v6 alone produces a trivial self-comparison — no head-to-head evidence for the current selection. | **v1** (only reliable data) |
| 5 | Test-data interaction | v6's "belonging/housing" example leaks into the sole enabled profile, inflating its scores; v4/v5 are neutral. All verdicts rest on n=1 (one profile, one event, one industry) — `concept_originality` on a single case is noise. | **v5** |
| 6 | Judge observability | GEval receives only `input_description` + `context` (`evaluator.py:102-105`) — neither includes `contact_info` or `model_branding`, so `contact_text_placement` cannot detect silently dropped contact elements (false pass). Affects all variants equally; v6's mandatory literal pattern is most audit-friendly. | **v6** |
| 7 | Model config fit (`providers.yaml`) | `gpt5_4_mini` gets max_tokens 1000 while its reasoning siblings get 2000. v5/v6's silent-reasoning instructions are the most exposed to truncation; v4 and below are safe. | **v4** |
| 8 | Image cascade readiness | All variants produce cascadable `prompt_auto_*` files; v6's pinned contact pattern feeds the downstream `text_placement` image metric most predictably. | **v6** |

**Section 3 verdict:** **v6** — metric alignment and user-prompt coherence dominate project fit, and v6 leads both. v5 beats v4 here because only v5/v6 align with `festive_not_promotional`.

**Section 3 ranking: v6 > v5 > v4 > v3 > v1 > v2.**

### Project actions required (in order)

1. **Fix the production contradiction** in `app/features/generation/prompt.py` — the shipped SYSTEM_PROMPT forbids company information while its own user prompt injects it when `model_branding` is true. Whatever wins the eval, this must land.
2. **De-leak v6's example** — replace "'belonging' for a housing firm" with a domain absent from test data (e.g. "'harvest' for a farm-equipment maker").
3. **Make the judge observant** — add contact_info to the spec `context` lines in the conftest generation step.
4. **Widen the sample** — enable `profile_v2`/`profile_v3` and run v4–v6 head-to-head; regenerate the stale comparison report.
5. **Bump `gpt5_4_mini` max_tokens** to 1500–2000 (or add `extra_params: {reasoning: {effort: "low"}}`) and check `prompt_v6_*_results.json` for truncated CONSTRAINTS sections.
6. **Close the industry-standard gaps** when feasible: paraphrase/edge-case robustness cases (missing colors, `model_branding: false`, non-English), an injection probe in one spec, and a repeat-run variance check.

---

## Section 4 — Improvement Suggestions (per prompt)

### v1 (production mirror)

1. **Resolve the contact contradiction at the source.** The fix belongs in `app/features/generation/prompt.py`, not the eval copy: replace the CONSTRAINTS item "no logos, no watermarks, no company information" with "no logos, no watermarks" and adopt v4's TEXT wording ("Header and body text. If provided: website and address along the bottom edge; phone and email in the top right corner"). Until then, v1 breaks on every `model_branding: true` spec.
2. **Exempt rendered text from the edge constraint** — append "(rendered text is exempt)" to "no focal elements near the edges", as v4–v6 do.

### v2

**Retire it** — but salvage two pieces into the winner before doing so:

1. The **tone-to-visual mapping table** (Rule 6: "professional → clean lines…", "playful → bright saturated colors…") is the best brand-tone device in any variant and is absent from v6.
2. The **good/bad brand-color example pair** ("Good: warm lighting with golden undertones echoing #FFD700 / Bad: yellow walls painted #FFD700") teaches the tonal-influence rule better than v6's abstract phrasing.

If it is ever revived instead: delete Rule 4 (lower-30% text pinning) and the CONSTRAINTS bullet "Reserve lower 30% for text overlay space" — both contradict its own "do not specify… exact placement" — and drop the "no company text" constraint.

### v3

**Retire** — fully superseded by v4. If kept for comparison runs only: scope "wrap every literal string in double quotes. Do NOT specify font, color, or placement" to the header and body explicitly, and add the "(rendered text is exempt)" edge exemption.

### v4 (fallback candidate)

1. If it remains the fallback, add v5's one-line festive framing to the opening sentence ("The deliverable is a festive social media post — a celebratory greeting, not an advertisement") — it currently has no defense against product-showcase concepts, which `festive_not_promotional` will punish.
2. Optionally borrow v6's literal contact pattern for the TEXT rule; v4's prose placement ("as a line along the bottom edge") leaves the separator and sizing to chance.

### v5

1. **Protect the brainstorm from truncation**: either raise `gpt5_4_mini` max_tokens to 1500–2000 in `providers.yaml`, or soften "Think of three distinct visual concepts… silently" to a single-sentence device ("Discard the most literal concept before writing") to cut hidden reasoning spend.
2. Adopt v6's literal contact pattern in the TEXT rule for the same reason as v4.

### v6 (winner)

1. **De-leak the example** (highest impact): replace "e.g. 'belonging' for a housing firm" with a domain absent from all test profiles, e.g. "e.g. 'harvest' for a farm-equipment maker".
2. **Make the angle levers non-exhaustive**: change "Find a fresh angle instead: an overhead or macro viewpoint, a symbolic object as the hero of the frame, a small human gesture (hands, not posed groups), or the quiet moment just before or after the celebration" to end with "…or another unexpected angle of your own" — otherwise the four-item menu becomes the new cliché at scale.
3. **Guard the placeholder pattern**: in the contact rule, add "substituting the actual values" after "following this pattern exactly" so a smaller model never renders the literal angle brackets.
4. **Consider importing v2's tone-to-visual mapping table** — v6 tells the model to honor brand tone but gives it no translation device; this is the one capability gap left versus v2.

---

## Appendix — Per-version notes

- **v1** (production mirror): faithful copy of `PromptGenerator.SYSTEM_PROMPT`; CONSTRAINTS "no company information" clashes with the `model_branding` contact block the user prompt injects — live in production.
- **v2**: strong technique (tone-to-visual mapping, good/bad color examples) undermined by triple-stated, self-contradictory text placement; measured text_specification success 33.3%; ~60% cost premium.
- **v3**: drops "no company information", pins contact placement in the TEXT format line — but the blanket "do NOT specify placement" rule still reads as covering contact strings, and bottom-edge text clashes with the un-exempted edge constraint.
- **v4**: the cleanup — header/body free, contact pinned, "(rendered text is exempt)", placement confined to TEXT, anti-cliché CONCEPT rule. No internal contradictions.
- **v5**: v4 + festive-not-promotional framing + silent brainstorm-and-discard. Creativity win; reasoning-token risk under max_tokens 1000.
- **v6** (selected): structural ban on posed-product subjects, four concrete angle levers, literal contact pattern, "nothing the company sells as focal element" constraint. Caveats: test-set leakage ("belonging"), rubric-encoding drains metric discriminative power, fixed angle menu risks homogenization.