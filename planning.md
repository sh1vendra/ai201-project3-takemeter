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

**Target**: 200 labeled rows (minimum), ~67 per label
**Source**: r/soccer posts and top-level comments via [Pullpush](https://pullpush.io) (public Pushshift mirror — used in place of PRAW after Reddit blocked unauthenticated API access in 2023)

### Collection Strategy

| Label | Primary Source | Reasoning |
|---|---|---|
| `reaction` | High-score post titles, match update threads | High emotional density, event-specific responses |
| `hot_take` | Discussion threads, opinion posts | Encourage confident, evidence-free asserting |
| `analysis` | Manually identified from unlabeled pool | Tactical/historical content is rare in top posts |

### Actual Collection Steps
1. `scrape_reddit.py` pulled 500 post titles/selftexts and 500 comments from r/soccer sorted by score via Pullpush JSON API.
2. Cleaned: removed rows starting with `Prediction:`, under 50 characters, `[deleted]`/`[removed]` content, Reddit poll links, and near-duplicates (first 50 chars).
3. Final pool: **333 rows**.
4. AI pre-labeling via `prelabel.py` (Groq `llama-3.3-70b-versatile`) labeled 220 rows; all labels manually reviewed.
5. `analysis` examples were manually identified from unlabeled pool to reach minimum of 15.
6. Stored as `raw_data.csv` with fields: `text`, `label`, `notes`.

### Actual Label Distribution (Final)

| Label | Count | % of Labeled |
|---|---|---|
| `analysis` | 15 | 6% |
| `hot_take` | 31 | 13% |
| `reaction` | 186 | 80% |
| **Total labeled** | **232** | — |

> **Note**: The dataset is heavily skewed toward `reaction` — this reflects the natural distribution of r/soccer content, which is dominated by news sharing and match updates rather than tactical debate. The target of ~67 per class was not achievable without significant manual curation.

### Train/Validation/Test Split
- **Train**: 162 rows (70%)
- **Validation**: 35 rows (15%)
- **Test**: 35 rows (15%)

Stratified by label to preserve class distribution across all splits.

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

AI assistance was planned for three stages. Below is what was planned vs. what was actually executed.

### 1. Label Stress-Testing (Pre-Collection) — *Planned*
Before collecting data, use an LLM to generate synthetic edge cases for each class boundary. These would be used to pressure-test the decision rules — not added to training data.

**Outcome**: The edge case decision rules (Cases 1–4 above) were developed through manual inspection of the data rather than LLM-generated synthetic examples. This stage was effectively merged into manual annotation.

### 2. Annotation Assistance (During Collection) — *Executed*
For unlabeled rows, `prelabel.py` called the Groq API (`llama-3.3-70b-versatile`) to suggest a label for each row. The human annotator made the final call on all labels. AI-suggested labels are marked `AI-prelabeled` in the `notes` column; manually corrected rows are marked `manual-labeled`.

**Outcome**: 220 rows were AI-prelabeled. All were reviewed. 15 `analysis` rows and several corrections were manually assigned. The tool worked as intended for `reaction` classification but under-performed on `analysis` even during prelabeling.

### 3. Failure Analysis (Post-Training) — *Executed*
Misclassified examples from the test set were reviewed against the label taxonomy to identify systematic patterns.

**Outcome**: The dominant failure mode was class collapse — the fine-tuned model predicted `reaction` for all inputs due to severe class imbalance. This was apparent from the confusion matrix and confirmed the need for weighted loss or balanced resampling in any follow-up training run.
