# TakeMeter — Fine-Tuning Project Plan

## Community Choice

**Subreddit: r/soccer**

r/soccer is one of the largest sports communities on Reddit (~3.5M members), producing a high daily volume of top-level comments that span a wide emotional and analytical range. Soccer discourse is uniquely suited for this classification task because:

- Match events trigger rapid, emotionally charged **reactions** in real time.
- A strong culture of tactical and statistical debate produces clearly structured **analyses**.
- The sport's global fanbase and high-stakes nature reliably generates confident, unsupported **hot takes**.

This diversity makes r/soccer an ideal source for a three-class dataset with minimal label ambiguity in clear cases, while also surfacing challenging edge cases that stress-test model boundaries.

---

## Label Taxonomy

### `analysis`
A post that makes a structured argument backed by stats, historical comparisons, or tactical observations. Evidence is specific and verifiable. The author is building a case, not just asserting.

**Example 1**
> "People forget how dominant De Bruyne was in 2021–22. He had 8 assists in his first 14 games back from injury, which was the highest rate in the league. Rodri's role expansion only makes sense because KDB shifted to a higher press trigger position — it wasn't random."

*Why it's `analysis`*: References a specific stat (8 assists in 14 games), names a season, and provides tactical context linking two observations causally.

**Example 2**
> "Historically, teams that win the Champions League don't necessarily dominate domestically that year. Madrid won CL in 2022 but finished 12 points behind Barcelona in La Liga. Same pattern with Liverpool in 2019. It suggests squad rotation and fixture congestion consistently produce domestic trade-offs at the elite level."

*Why it's `analysis`*: Uses two verifiable historical data points and draws a reasoned, evidence-backed structural conclusion.

---

### `hot_take`
A bold, confident opinion stated without supporting evidence. The author asserts rather than argues — no stats, no comparisons, no tactical reasoning. Tone is often declarative or provocative.

**Example 1**
> "Mbappe is already better than Messi ever was. End of discussion."

*Why it's `hot_take`*: Confident comparative claim with zero evidence. "End of discussion" signals the author is asserting, not inviting reasoned debate.

**Example 2**
> "The Premier League is genuinely the worst-run top league in Europe. The other four leagues make it look embarrassing."

*Why it's `hot_take`*: Strong, sweeping claim that could be supported with evidence (financial regulation data, referee quality metrics) but isn't. No argument is made.

---

### `reaction`
An immediate emotional response to a specific, recent event. Little to no argument — the post is expressing a feeling provoked by something that just happened.

**Example 1**
> "THAT GOAL. I can't breathe. First time we've scored in the 90th minute in three years and it had to be a volley like that. My heart."

*Why it's `reaction`*: Direct emotional response to a specific match moment. No argument, no evidence, just affect.

**Example 2**
> "I genuinely cannot watch this ref anymore. Three penalties ignored in 20 minutes. I'm done. Turning it off."

*Why it's `reaction`*: Emotional frustration tied to a live event. While it contains an implicit complaint about officiating, there's no argument — it's venting.

---

## Hard Edge Cases and Decision Rules

These are the most common sources of labeling error. Each rule resolves ambiguity by anchoring the decision to one defining feature.

### Case 1: Opinion with One Stat (`hot_take` vs. `analysis`)
> "Rashford has been terrible this season. He has 3 goals in 20 games — just not good enough."

**Decision rule**: A single cherry-picked or uncontextualized stat does not make a post `analysis`. `analysis` requires a structured argument — the stat must be used to build a case, not just to intensify an assertion. If the post would read identically without the number (i.e., removing the stat doesn't change the claim's logic), label it `hot_take`.

---

### Case 2: Emotional + Argumentative Mix (`reaction` vs. `analysis`)
> "I'm so angry right now. But seriously — Slot's substitutions were tactically illiterate. Pulling off Salah in the 70th when we were chasing the game? Insane."

**Decision rule**: When a post contains both emotional language and a tactical/analytical point, ask: *what is the dominant purpose?* If the argument could stand alone and is the main thrust, lean `analysis`. If the argument is subordinate to expressing a feeling and is brief or undeveloped, label `reaction`. In this example, the tactical observation is a sentence embedded in venting — label `reaction`.

---

### Case 3: Confident Analysis (`analysis` vs. `hot_take`)
> "Guardiola is clearly the greatest manager in history. His trophy-per-season rate, his adaptations across three leagues, his tactical evolution from positional play to gegenpressing hybrids — there's no comparison."

**Decision rule**: Confidence of tone alone does not make something a `hot_take`. If verifiable evidence is cited and a logical case is being assembled, label it `analysis` even if the conclusion is strong. The test is evidence presence and use, not tone certainty.

---

### Case 4: Sarcasm (`hot_take` vs. `reaction`)
> "Oh, brilliant. Another 0-0 at the Arsenal. Absolutely world-class football on display."

**Decision rule**: Sarcastic posts that are primarily venting about an event belong in `reaction`. Only label `hot_take` if the sarcasm is wrapping a genuine bold opinion claim, not just frustration. When in doubt with sarcastic posts, prefer `reaction`.

---

## Data Collection Plan

**Target**: 200 labeled posts (~67 per label)
**Source**: Top-level comments on r/soccer posts — match threads, discussion threads, and hot posts.

### Collection Strategy

| Label | Primary Thread Type | Reasoning |
|---|---|---|
| `reaction` | Live match threads, post-match threads | High emotional density, event-specific responses |
| `hot_take` | Weekly discussion threads, "unpopular opinion" threads | Encourage confident, evidence-free asserting |
| `analysis` | Tactical discussion posts, historical comparison threads | Draw users inclined toward structured reasoning |

### Collection Steps
1. Use the Reddit API (PRAW) or manual scraping to pull top-level comments from 15–20 targeted threads across the three thread types above.
2. Filter out: deleted/removed comments, comments under 15 words, non-English comments, and pure meme responses.
3. Annotate each comment with a label. Use a second pass for any flagged ambiguous cases.
4. Balance across labels: target 67 per class, with a tolerance of ±5.
5. Store raw data in `data/raw/` as `.jsonl` with fields: `id`, `text`, `label`, `source_thread`, `annotator_notes`.

### Train/Validation/Test Split
- **Train**: 140 posts (70%)
- **Validation**: 30 posts (15%)
- **Test**: 30 posts (15%)

Stratified by label to preserve class balance across all splits.

---

## Evaluation Metrics

### Metrics Used
- **Overall Accuracy**: proportion of correctly classified posts across all classes.
- **Per-class F1 Score**: harmonic mean of precision and recall for each individual label.

### Why These Metrics

**Accuracy** gives a high-level view of model performance and is intuitive to communicate. However, in a multi-class setting with potentially imbalanced real-world distributions, accuracy can be misleading — a model could ignore a minority class and still score well. It is reported as a supporting number, not the primary success criterion.

**Per-class F1** is the primary metric because it directly captures performance on each label independently. It penalizes both false positives (precision) and false negatives (recall), which matters here because all three labels are equally important to the task. A model that classifies `analysis` well but consistently misses `hot_take` or `reaction` is not useful — F1 exposes that failure where accuracy might not.

Macro-averaged F1 across all three classes will also be reported as a single summary number.

---

## Definition of Success

The model is considered successful if it achieves:

> **Per-class F1 ≥ 0.70 for all three labels on the held-out test set.**

This threshold was chosen because:
- 0.70 represents meaningful signal above chance (0.33 for a random 3-class model).
- It is achievable with 200 samples through fine-tuning a strong pre-trained model.
- It is high enough to be practically useful for annotation assistance and content analysis.

A model passing this bar on all three classes will be considered ready for use. A model that meets the bar on only one or two classes will be retrained with additional data or label cleaning for the failing class.

---

## AI Tool Plan

AI assistance is used at three stages of the project — not for bulk labeling, but for targeted augmentation and diagnostics.

### 1. Label Stress-Testing (Pre-Collection)
Before collecting data, use an LLM to generate synthetic edge cases for each class boundary (e.g., `hot_take`/`analysis` border, `reaction`/`hot_take` border). These synthetic posts are used to pressure-test the decision rules in the taxonomy above — not added to training data. The goal is to expose decision rule gaps before annotation begins.

### 2. Annotation Assistance (During Collection)
For comments flagged as ambiguous during human annotation, use an LLM to provide a suggested label with reasoning. The human annotator makes the final call, but the LLM suggestion surfaces alternative interpretations and reduces annotation fatigue on hard cases. All AI-assisted labels are marked in `annotator_notes` as `ai_suggested` for traceability.

### 3. Failure Analysis (Post-Training)
After evaluating the fine-tuned model on the test set, feed misclassified examples to an LLM with the prompt: *"Given this label taxonomy, why might a model confuse this post's class?"* The output is used to identify systematic failure patterns (e.g., sarcasm consistently mislabeled, stats used as assertions consistently promoted to `analysis`) and inform a second round of decision rule refinement or targeted data augmentation.
