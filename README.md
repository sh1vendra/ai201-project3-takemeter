# TakeMeter

Fine-tuning a text classifier on r/soccer posts to distinguish between three types of soccer discourse: **analysis**, **hot\_take**, and **reaction**.

---

## Community Choice

**Subreddit: r/soccer**

r/soccer (~3.5M members) generates a high daily volume of top-level comments that span a wide emotional and analytical range. Soccer discourse is uniquely suited for this classification task because:

- Match events trigger rapid, emotionally charged **reactions** in real time.
- A strong culture of tactical and statistical debate produces clearly structured **analyses**.
- The sport's global fanbase reliably generates confident, unsupported **hot takes**.

---

## Label Taxonomy

### `analysis`
A structured argument backed by specific stats, tactical observations, or historical comparisons. Evidence is specific and verifiable. The author is building a case, not just asserting.

**Example 1**
> "2010: Pep Guardiola coaches in Spain — Spain win the World Cup. 2014: Pep coaches in Germany — Germany win the World Cup. 2018: Pep coaches in England — Doesn't mean anything."

**Example 2**
> "Waiting to concede goals so that you start playing attacking football is not a tactic, it's a pathetic display of desperation. Mourinho got the tactics all wrong. They played terribly and we deserve to go through."

---

### `hot_take`
A bold, confident opinion stated without supporting evidence. The author asserts rather than argues — no stats, no comparisons, no tactical reasoning.

**Example 1**
> "This is the most horrible signing in the history of Barca."

**Example 2**
> "I've got it. I know how we save the 2019/2020 Premier League."

---

### `reaction`
An immediate emotional response to a specific event. Little to no argument — just expressing a feeling or sharing news.

**Example 1**
> "Argentina have won their third World Cup title at the 2022 FIFA World Cup in Qatar!"

**Example 2**
> "FUCKING HELL NEYMAR JUST SHOOT THE FUCKING BALL AND YOU WOULD HAVE SCORED YOU LITTLE SHIT"

---

## Data Collection

- **Source**: r/soccer via [Pullpush](https://pullpush.io) (public Pushshift mirror, no API key required)
- **Method**: Fetched post titles, selftexts, and top-level comments sorted by score
- **Raw collected**: ~532 rows
- **After cleaning**:
  - Removed rows starting with `Prediction:` (low-quality match prediction posts)
  - Removed rows under 50 characters
  - Deduplicated by first 50 characters
  - Removed `[deleted]` / `[removed]` content and Reddit poll links
- **Final dataset**: 333 rows

---

## Labeling Process

Labels were assigned in two stages:

1. **AI pre-labeling**: `prelabel.py` called the Groq API (`llama-3.3-70b-versatile`) to suggest a label for each unlabeled row. Labels were written to `raw_data.csv` and saved every 10 rows.
2. **Manual review**: All AI-suggested labels were reviewed. Rows labeled `AI-prelabeled-error` were corrected. Additional `analysis` examples were manually identified and labeled to reach the minimum target of 15.

**Final labeled dataset: 232 rows**

| Label | Count |
|---|---|
| `analysis` | 15 |
| `hot_take` | 31 |
| `reaction` | 186 |
| **Total** | **232** |

> **Note**: The dataset is heavily imbalanced toward `reaction`. This reflects the natural distribution of r/soccer content, which skews heavily toward news sharing and match updates rather than tactical debate.

---

## Fine-Tuning Approach

- **Model**: `distilbert-base-uncased`
- **Epochs**: 3
- **Learning rate**: 2e-5
- **Batch size**: 16
- **Split**: 70% train / 15% val / 15% test (stratified by label)
- **Test set size**: 35 rows

The dataset was formatted as labeled text pairs and fine-tuned using HuggingFace Transformers with a classification head over DistilBERT's `[CLS]` token.

---

## Baseline Description

**Model**: `llama-3.3-70b-versatile` via Groq API

The baseline uses the same prompt used during pre-labeling — a zero-shot classifier with the full label taxonomy in the system prompt. No training, no examples.

**Prompt format**:
```
System: You are a soccer discourse classifier. Classify posts into exactly one label.
Labels: analysis, hot_take, reaction
[rules]

Post: {text}
```

---

## Evaluation Report

### Accuracy

| Model | Accuracy |
|---|---|
| Baseline (Groq llama-3.3-70b-versatile) | **0.829** |
| Fine-tuned DistilBERT | **0.800** |
| Difference | -0.029 |

### Baseline Per-Class Metrics

| Label | Precision | Recall | F1 |
|---|---|---|---|
| `analysis` | 0.00 | 0.00 | 0.00 |
| `hot_take` | 0.60 | 0.75 | 0.67 |
| `reaction` | 0.90 | 0.93 | 0.91 |

### Fine-Tuned DistilBERT Per-Class Metrics

| Label | Precision | Recall | F1 |
|---|---|---|---|
| `analysis` | 0.00 | 0.00 | 0.00 |
| `hot_take` | 0.00 | 0.00 | 0.00 |
| `reaction` | 0.80 | 1.00 | 0.89 |

### Confusion Matrix (Fine-Tuned, Test Set)

|  | Predicted: analysis | Predicted: hot_take | Predicted: reaction |
|---|---|---|---|
| **True: analysis** | 0 | 0 | 3 |
| **True: hot_take** | 0 | 0 | 4 |
| **True: reaction** | 0 | 0 | 28 |

The fine-tuned model collapsed to predicting `reaction` for every input. This is a textbook class collapse caused by severe label imbalance — `reaction` makes up 80% of the labeled dataset, and the model learned that always predicting the majority class is the loss-minimizing strategy.

---

## Sample Classifications

| Text (truncated) | True Label | Baseline | Fine-Tuned |
|---|---|---|---|
| *TBD — fill in from test set* | — | — | — |
| *TBD* | — | — | — |
| *TBD* | — | — | — |
| *TBD* | — | — | — |
| *TBD* | — | — | — |

---

## Wrong Predictions Analysis

Three representative errors from the fine-tuned model:

**1. Misclassified as `reaction`**
> "Not much of a protest if you need permission from those you are protesting against."
- **True label**: `hot_take`
- **Predicted**: `reaction`
- **Why it failed**: The model never learned `hot_take` — it collapsed entirely. Any opinion-forward post gets swept into `reaction`.

**2. Misclassified as `reaction`**
> "Waiting to concede goals so that you start playing attacking football is not a tactic, it's a pathetic display of desperation. Mourinho got the tactics all wrong."
- **True label**: `analysis`
- **Predicted**: `reaction`
- **Why it failed**: Only 15 `analysis` examples in training. DistilBERT had no meaningful signal to distinguish structured tactical critique from a generic response.

**3. Misclassified as `reaction`**
> "I hope most Man United fans will remember Wayne Rooney as a great legend for them. Some few bad years shouldn't disregard how brilliant he was for around 10 years."
- **True label**: `analysis`
- **Predicted**: `reaction`
- **Why it failed**: Career retrospective framing with a comparative argument — but with only 15 total `analysis` examples, the model never learned this pattern.

---

## What the Model Learned vs. What Was Intended

**Intended**: A three-class classifier that distinguishes structured arguments (analysis), unsupported bold opinions (hot\_take), and emotional event responses (reaction).

**What actually happened**: The fine-tuned model learned a one-class classifier — it always outputs `reaction`. The 80/13/7 class split (reaction/hot\_take/analysis) meant the training loss was dominated by the majority class. DistilBERT converged on the trivial solution.

The baseline (Groq LLM) performed better on minority classes because it uses in-context understanding of the label definitions, not a learned distribution — it doesn't need balanced examples to attempt all three classes. Even so, the baseline also failed on `analysis` (F1=0.00), suggesting the label is genuinely hard to classify from the text alone without richer examples.

**Key lesson**: Class imbalance this severe (12:1 reaction:analysis ratio) requires weighted loss, oversampling, or significantly more minority-class examples before fine-tuning on a small encoder model.

---

## Spec Reflection

The project plan specified F1 ≥ 0.70 per class as the definition of success. Neither model met this bar for `analysis`. The baseline met it for `reaction` (F1=0.91) and approached it for `hot_take` (F1=0.67). The fine-tuned model met it only for `reaction` (F1=0.89) and failed entirely on the other two classes.

The primary bottleneck was data quantity and balance — 15 `analysis` examples and 31 `hot_take` examples are not enough for a supervised fine-tuning approach on a small model. A realistic fix would require:
- 60–80 examples per class (balanced)
- Weighted cross-entropy loss during training
- Or using a larger model (e.g., RoBERTa, DeBERTa) with more capacity to learn from few examples

---

## AI Usage Disclosure

This project used AI assistance in the following ways:

1. **Pre-labeling (`prelabel.py`)**: The Groq API (`llama-3.3-70b-versatile`) was used to generate suggested labels for all 232 labeled rows. All labels were manually reviewed after generation. Rows that errored were manually corrected. Additional `analysis` labels were manually assigned by the author to reach the minimum target.

2. **Baseline evaluation**: The same Groq model was used as the zero-shot baseline for comparison against the fine-tuned model.

AI was not used to write any of the code, generate the dataset text, or write this README without human review and editing.
