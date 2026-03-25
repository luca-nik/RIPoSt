# RIPoSt Analysis — Emotional Dysregulation in ADHD

This repository contains the full statistical analysis pipeline for a thesis investigating
**emotional dysregulation (ED) in adult ADHD patients**, using the RIPoSt screening instrument.

---

## Table of Contents

1. [Background](#1-background)
2. [How to run](#2-how-to-run)
3. [Dataset structure](#3-dataset-structure)
4. [Analysis pipeline](#4-analysis-pipeline)
   - [Step 1 — Spearman correlation](#step-1--spearman-correlation-with-ripost-ned)
   - [Step 2 — LASSO linear regression](#step-2--lasso-linear-regression--ripost-ned)
   - [Step 3 — Association analysis](#step-3--association-analysis-csed-vs-csed)
   - [Step 4 — LASSO logistic regression](#step-4--lasso-logistic-regression--ripost-sv)
   - [Step 5 — Clustering](#step-5--clustering--comparison-vs-ripost-sv)
5. [Output files](#5-output-files)
6. [Interpreting the plots](#6-interpreting-the-plots)
7. [Important caveats](#7-important-caveats)

---

## 1. Background

### What is emotional dysregulation?

Emotional dysregulation (ED) refers to the inability to manage emotional experiences in a way
that allows goal-directed behavior. In clinical terms, it manifests as some combination of:
- **Hot temper / explosive short-lived outbursts**
- **Affective lability** — rapid mood shifts from normal to depressed or excited, usually lasting hours
- **Emotional over-reactivity** — being unable to handle ordinary stress

ED is highly prevalent in ADHD and is considered a transdiagnostic feature across many psychiatric
conditions.

### What is RIPoSt?

The **Reactivity, Intensity, Polarity and Stability questionnaire (RIPoSt)** is a self-report
instrument measuring different facets of emotional dysregulation. The version used here is
**RIPoSt-40**, a 40-item questionnaire with four subscales:

| Subscale | What it measures |
|---|---|
| Affective instability (AI) | How much mood oscillates over time |
| Negative emotionality (N) | Tendency toward intense, frequent negative emotions |
| Positive emotionality (P) | Tendency toward intense, frequent positive emotions |
| Emotional impulsivity (EI) | Inability to control impulsive reactions to emotions |

From these, a **Negative Emotion Dysregulation (NED)** total score is derived (30 items,
excluding positive emotionality), ranging from 39 to 178. Higher scores = more severe ED.

### What is RIPoSt-SV?

The **RIPoSt-SV** (Screening Version) is a short decision tree developed in Brancati et al. (2024,
Journal of Affective Disorders) that classifies a patient as either:

- **CSED+ (True):** Clinically Significant Emotional Dysregulation is present
- **CSED− (False):** Clinically Significant Emotional Dysregulation is absent

CSED is defined as: at least 2 of the 3 qualitative criteria above AND a severity rating of
at least 4/7 on the Clinical Global Impression scale. The tool was validated with ~83% accuracy.

### What does this analysis do?

We have a dataset of **200 adult ADHD patients** assessed with a wide battery of clinical and
psychometric instruments. The goal is to understand:

1. Which clinical and psychometric variables are associated with ED severity and CSED status?
2. Which variables independently predict ED, after controlling for all others?
3. Do patients naturally cluster into types that align with CSED status?

---

## 2. How to run

### Requirements

- Python ≥ 3.11
- [uv](https://docs.astral.sh/uv/) for package management

### Setup

```bash
# Install dependencies (only needed once)
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### Running the analysis

```bash
# Run everything — all 5 steps, all 3 samples (full, INAT, COMB)
uv run python main.py

# Run specific steps only
uv run python main.py --steps 1 2

# Run on a specific sample only
uv run python main.py --samples inat

# Combine: step 3 on full sample and COMB subtype
uv run python main.py --steps 3 --samples full comb
```

### Available steps and samples

| `--steps` | Analysis |
|---|---|
| `1` | Spearman correlation → RIPoSt-NED |
| `2` | LASSO linear regression → RIPoSt-NED |
| `3` | Association analysis → RIPoSt-SV |
| `4` | LASSO logistic regression → RIPoSt-SV |
| `5` | Clustering + comparison vs RIPoSt-SV |

| `--samples` | Patients included |
|---|---|
| `full` | All 200 patients |
| `inat` | Inattentive subtype only (n=98) |
| `comb` | Combined subtype only (n=97) |

---

## 3. Dataset structure

**File:** `dati_ripost.xlsx` — sheet `data_ripost_sv`
**Size:** 200 patients × 109 columns

### Patient groups

| Subtype | Code | N | Notes |
|---|---|---|---|
| Inattentive | INAT | 98 | Included in all analyses |
| Combined | COMB | 97 | Included in all analyses |
| Hyperactive | IPER | 4 | Descriptive only — too few for statistical tests |

### Variable types

#### Demographics
| Column | Description |
|---|---|
| `Genere` | Gender (encoded: M=1, F=0) |
| `Age` | Age in years |
| `school_years` | Years of education |
| `repeated_grades` | Number of repeated school years |
| `marital_status` | Civil status (one-hot encoded) |

#### Clinical variables
| Column | Description |
|---|---|
| `mood` | Mood diagnosis (BD1, BD2, CYC, MDD, NO) |
| `mood_any` | Has any mood disorder (True/False) |
| `mood_onset` | Age at first mood episode |
| `FH_bipolar`, `FH_mood`, ... | Family history flags (True/False) |
| `alcool`, `cannabis`, `opioids`, ... | Substance use (True/False) |
| `panic`, `GAD`, `social_anx`, ... | Anxiety disorders (True/False) |
| `anorexia`, `bulimia`, `BED` | Eating disorders (True/False) |
| `Trattato` | Currently under pharmacological treatment (True/False) |
| `first_referral` | Age at first psychiatric contact |
| `sud_any`, `anx_any`, `eat_any`, ... | Any disorder in that category (True/False) |

#### Psychometric scales

All scale scores are continuous (higher = more severe / more symptoms).

| Scale | What it measures | Columns |
|---|---|---|
| **CAARS** | ADHD symptoms (Conners self-report) | `CAARS_A/B/C/D` |
| **BRIEF** | Executive function difficulties | `BRIEF_GEC` (total), `BRIEF_BRI`, `BRIEF_MI` + 8 subscales |
| **FAST** | Functional impairment | `FAST_TOT` + 6 subscales |
| **ASRS** | ADHD severity (self-report) | `ASRS` |
| **LPFS** | Level of personality functioning | `LPFS_S` (self), `LPFS_I` (interpersonal) |
| **HCL** | Hypomania symptoms | `HCL_TOT`, `HCL_F1`, `HCL_F2` |
| **TEMPS** | Affective temperament | `TEMPS_D` (depressive), `TEMPS_C` (cyclothymic), `TEMPS_H` (hyperthymic), `TEMPS_I` (irritable), `TEMPS_A` (anxious) |
| **PID** | Personality traits (DSM-5) | `PID_NEG`, `PID_DET`, `PID_ANT`, `PID_DIS`, `PID_ANA`, `PID_PSY` |
| **BIS** | Impulsivity (Barratt) | `BIS_TOT` + `BIS_A/M/P` |
| **BRIAN** | Biological rhythms | `BRIAN_TOT` + 5 subscales |

#### Outcome variables (not used as predictors)

| Column | Type | Description |
|---|---|---|
| `RIPoSt_NED` | Continuous (39–178) | Total negative emotion dysregulation score |
| `RIPoSt_SV` | Binary (True/False) | CSED screening result |
| `RIPoSt_AI`, `RIPoSt_N`, `RIPoSt_EI`, `RIPoSt_P` | Continuous | RIPoSt subscales |
| `RIPoSt_40`, `RIPoSt_36`, `RIPoSt_3`, `RIPoSt_4`, `RIPoSt_32`, `RIPoSt_27` | Binary | Individual RIPoSt items used in the decision tree |

All `RIPoSt_*` columns are part of the instrument being studied and are **excluded from predictors**
in all analyses.

### Missing data

Missing data is handled with **available-case analysis** (pairwise deletion): each statistical
test uses all patients who have valid data for that specific variable, regardless of whether
they have missing data on other variables. The sample size N is reported for every result.
No imputation was performed.

Columns with notable missing data:
- CAARS subscales: ~39 missing (~20%)
- BRIEF subscales: ~40 missing (~20%)
- FAST_TOT: ~79 missing (~40%)

---

## 4. Analysis pipeline

Each step is run separately for three samples: **full sample**, **INAT subtype**, **COMB subtype**.
This allows comparison of findings across subtypes.

---

### Step 1 — Spearman correlation with RIPoSt-NED

**Question:** *Which variables track with the severity of emotional dysregulation?*

**How it works:**

For each predictor variable, we compute a **Spearman rank correlation (ρ)** with the NED score.
Spearman correlation measures how consistently two variables move together — if patients with
higher TEMPS_C also tend to have higher NED, the correlation is positive. If patients with
earlier mood onset tend to have higher NED, the correlation is negative (because earlier age
= lower number).

Spearman is used instead of Pearson because it does not assume that the relationship is
perfectly linear or that the data is normally distributed — it works on ranks, making it
more robust for psychiatric data.

**Example:** TEMPS_C (cyclothymic temperament) has ρ = +0.81 — one of the strongest
correlations in the dataset. This means patients who score higher on cyclothymic temperament
almost always score higher on NED severity. The relationship is very consistent.

**What ρ values mean:**

| ρ value | Interpretation |
|---|---|
| 0.8 – 1.0 | Very strong |
| 0.6 – 0.8 | Strong |
| 0.4 – 0.6 | Moderate |
| 0.2 – 0.4 | Weak |
| 0.0 – 0.2 | Negligible |

Negative ρ means the variable moves in the opposite direction to NED (higher value = lower
ED severity). For example, `Genere` (M=1, F=0) has a negative ρ because males tend to score
lower on NED than females.

**Important limitation:** This analysis looks at each variable **one at a time**. It cannot
tell you whether a variable has an independent effect or whether it is just correlated with
another variable that is the real driver. That is what Step 2 does.

---

### Step 2 — LASSO linear regression → RIPoSt-NED

**Question:** *Which variables independently predict ED severity, after accounting for all others?*

**The problem this solves:**

In Step 1, many variables correlate with NED. But many of those variables also correlate
with each other. For example, TEMPS_C and ASRS are both strongly correlated with NED — but
are they each contributing something unique, or is one just a proxy for the other?

Standard multiple regression would answer this, but with ~98 predictors and only 200 patients,
it is unreliable — the model would find spurious patterns in the noise.

**What LASSO does:**

LASSO (Least Absolute Shrinkage and Selection Operator) is a penalized regression. It works
like standard regression but adds a cost for every variable included. A variable is only kept
if it contributes enough predictive power to justify the cost. This forces most coefficients
to exactly zero, leaving only the variables with genuine independent signal.

The penalty strength is chosen automatically via **5-fold cross-validation**: the dataset is
split into 5 parts, the model is trained on 4 and tested on 1, repeated 5 times. The penalty
that gives the best average test performance is selected.

**Example:** In the full sample, 15 variables survived out of 98. TEMPS_C had β = +9.78 and
ASRS had β = +6.13, meaning both contribute independently to NED severity — knowing one does
not make the other redundant. Conversely, many variables that correlated with NED in Step 1
disappeared here, meaning their apparent relationship was driven by overlap with TEMPS_C or
ASRS.

**What the coefficients mean:**

- **Positive β:** higher score on this variable → higher NED severity
- **Negative β:** higher score → lower NED severity
- **Larger |β|:** stronger independent contribution
- **β = 0:** variable was eliminated by LASSO (not independently informative)

**Model performance:**

- **CV R² ≈ 0.77** in the full sample: the model explains ~77% of the variance in NED severity.
  This is high for psychiatric data, suggesting the psychometric variables capture ED severity well.
- **CV RMSE ≈ 14.5**: on average, the model's NED prediction is off by about 14.5 points
  (on a scale of 39–178).

---

### Step 3 — Association analysis: CSED+ vs CSED−

**Question:** *For each variable, do patients who screen positive for ED look different from those who screen negative?*

**How it works:**

The 200 patients are split into two groups based on RIPoSt-SV: CSED+ (n=132) and CSED− (n=68).
For every predictor variable, we test whether the two groups differ — using the appropriate
test depending on the variable type:

**For continuous variables** (scale scores):
- Test: **Mann-Whitney U** — compares whether values in one group tend to be higher than in
  the other, without assuming a normal distribution
- Effect size: **rank-biserial correlation r**
  - Positive r → CSED+ patients score **higher** on this variable
  - Negative r → CSED+ patients score **lower** on this variable
  - |r| ≥ 0.5 is considered a large effect

**For binary/categorical variables** (yes/no comorbidities, family history):
- Test: **Chi-square** or **Fisher's exact** (when expected counts are small)
- Effect size: **Cramér's V**
  - Always positive (0 to 1) — measures strength of association but not direction
  - To know direction (more common in CSED+ or CSED−?), look at the raw percentages in the CSV

**Examples:**

- `TEMPS_C`: large positive r → CSED+ patients score much higher on cyclothymic temperament
- `mood_onset`: significant negative r → CSED+ patients had their first mood episode at a
  younger age (earlier onset = lower number = negative correlation with CSED+)
- `mood_any`: significant Cramér's V → having a mood disorder is distributed differently
  between CSED+ and CSED− groups (check CSV for direction)

**Important limitation:** Like Step 1, each variable is tested individually. A variable may
appear significant simply because it correlates with another significant variable. Step 4
addresses this.

---

### Step 4 — LASSO logistic regression → RIPoSt-SV

**Question:** *Which variables are genuine independent predictors of screening CSED+?*

**How it works:**

Same LASSO logic as Step 2, but the outcome is now binary (CSED+ yes/no) instead of
continuous. This requires **logistic regression**, which models the probability of being CSED+
as a function of the predictor variables.

The LASSO penalty again eliminates weak or redundant variables, keeping only those with
genuine independent predictive value.

**What the coefficients mean:**

Instead of β directly, the most interpretable quantity is the **odds ratio (OR = exp(β))**:

- **OR > 1:** this variable increases the odds of being CSED+
- **OR < 1:** this variable decreases the odds of being CSED+
- **OR = 1:** no effect

**Example:** In the full sample, TEMPS_C had OR ≈ 1.76. This means: for each one-unit
increase in the cyclothymic temperament score, the odds of screening CSED+ are 1.76 times
higher — independently of ASRS, BRIAN_ACT, and all other variables in the model.

**Model performance:**

- **CV AUC ≈ 0.80:** the model can distinguish CSED+ from CSED− patients with 80%
  discriminative ability. AUC of 0.5 = chance, 1.0 = perfect.
- **CV Accuracy ≈ 76%:** compared to the RIPoSt-SV paper reference of 83%, meaning the
  screening tool is still better at identifying CSED than the full clinical/psychometric
  profile alone.

**Key insight:** A variable that was strongly significant in Step 3 may disappear in Step 4.
This means it is associated with CSED, but only because it travels together with another
variable that is the real driver. Variables that **survive Step 4** are the ones that matter
independently.

---

### Step 5 — Clustering + comparison vs RIPoSt-SV

**Question:** *Do ADHD patients naturally group into distinct types — and do those types align with CSED status?*

**How it works:**

Steps 1–4 all used RIPoSt-SV or NED as an explicit outcome to guide the analysis. Clustering
is entirely different: it is **unsupervised** — it is blind to who is CSED+ or CSED−.

K-means clustering groups patients based purely on their similarity across the psychometric
scale scores. Patients within the same cluster score similarly across all scales; patients
in different clusters score differently.

The number of clusters (k) is chosen automatically by testing k=2 to 6 and selecting the
value that produces the most distinct, well-separated groups, measured by the **silhouette score**
(higher = better separated). In all samples, k=2 was optimal.

**Then, as a second step**, we ask: within each cluster, what fraction of patients is CSED+?
If one cluster is almost entirely CSED+ and the other mostly CSED−, the natural patient
grouping aligns with the clinical screening. We then use this to classify patients and compare
accuracy against RIPoSt-SV's 83% reference.

**Example interpretation of cluster profiles:**

If the cluster profile heatmap shows Cluster 0 with high TEMPS scores and high ASRS, and
Cluster 1 with lower scores across all scales — Cluster 0 likely represents a more severe,
emotionally dysregulated ADHD profile, while Cluster 1 represents a milder presentation.

**Results and what they mean:**

Clustering accuracy was **66–69%** across all samples, compared to RIPoSt-SV's **83%**.

This is a meaningful finding: the natural grouping of ADHD patients by their clinical
and psychometric profile does not recover the CSED distinction as reliably as the dedicated
screening tool. Being CSED+ is not simply equivalent to being a "more severe" ADHD patient
on all dimensions — it is a specific clinical feature that requires a targeted instrument.
This **validates RIPoSt-SV** as capturing something that broad clinical profiling alone misses.

---

## 5. Output files

All outputs are saved in the `output/` directory, organized as:

```
output/
├── full/                         ← all 200 patients
│   ├── step1_spearman/
│   ├── step2_lasso_ned/
│   ├── step3_association/
│   ├── step4_logistic/
│   └── step5_clustering/
├── inat/                         ← INAT subtype (n=98)
│   └── ...
└── comb/                         ← COMB subtype (n=97)
    └── ...
```

### Step 1 outputs

| File | Description |
|---|---|
| `spearman_results.csv` | Full table: variable, ρ, p-value, N for every predictor |
| `demographics.png` | Bar chart: ρ for demographic variables |
| `clinical.png` | Bar chart: ρ for clinical variables (comorbidities, family history, etc.) |
| `scale_totals.png` | Bar chart: ρ for psychometric scale totals |
| `scale_subscales.png` | Bar chart: ρ for psychometric subscales |

### Step 2 outputs

| File | Description |
|---|---|
| `lasso_coefficients.csv` | Surviving variables with their β coefficients |
| `lasso_metrics.csv` | CV R², CV RMSE, best regularization parameter α, N |
| `lasso_coefficients.png` | Bar chart of surviving β coefficients |

### Step 3 outputs

| File | Description |
|---|---|
| `association_results.csv` | Full table: variable, effect size, p-value, N, test used |
| `demographics.png` | Bar chart: effect sizes for demographic variables |
| `clinical.png` | Bar chart: effect sizes for clinical variables |
| `scale_totals.png` | Bar chart: effect sizes for scale totals |
| `scale_subscales.png` | Bar chart: effect sizes for scale subscales |

### Step 4 outputs

| File | Description |
|---|---|
| `logistic_coefficients.csv` | Surviving variables with β and odds ratio |
| `logistic_metrics.csv` | CV AUC, CV accuracy, best C, N, CSED+/CSED− counts |
| `logistic_coefficients.png` | Bar chart of surviving β with OR labeled |

### Step 5 outputs

| File | Description |
|---|---|
| `silhouette_scores.png` | Silhouette score for each k — shows why k=2 was chosen |
| `cluster_profiles.png` | Heatmap: mean standardized scale scores per cluster |
| `csed_rate_per_cluster.png` | Bar chart: % CSED+ patients in each cluster |
| `cluster_assignments.csv` | Each patient's cluster label and predicted CSED |
| `clustering_metrics.csv` | Best k, silhouette, accuracy, comparison to 83% reference |
| `confusion_matrix.csv` | True vs predicted CSED labels per cluster |

---

## 6. Interpreting the plots

### Bar chart colors (Steps 1, 2, 3, 4)

| Color | Meaning |
|---|---|
| Dark blue | Positive and statistically significant (p < 0.05) |
| Dark red | Negative and statistically significant (p < 0.05) |
| Light blue | Positive but not significant |
| Light red/orange | Negative but not significant |

### Reading bar charts (Steps 1 and 3)

- Bars are sorted by absolute effect size (largest effect at the top)
- The N for each variable is annotated on the bar (available-case N)
- A dashed vertical line marks zero

### Reading the cluster profile heatmap (Step 5)

- Each row is a cluster, each column is a scale
- Blue = that cluster scores below average on that scale
- Red = that cluster scores above average
- The pattern of colors describes what kind of patient ends up in each cluster

### Readability warnings

When a plot would contain more than 30 variables, a warning is printed:
```
[READABILITY WARNING] 'Clinical — Full sample' would display 40 variables...
```
The plot is still saved, but interpret it carefully — it may be dense.

---

## 7. Important caveats

**Steps 1 and 3 are univariate** — they test each variable in isolation. A significant
result does not mean the variable has an independent effect; it may simply be correlated
with another variable that is the true driver.

**Steps 2 and 4 are multivariate** — they control for all other variables simultaneously.
These results are more conservative but more reliable for causal inference.

**LASSO performs variable selection** — variables eliminated by LASSO are not necessarily
unimportant in a clinical sense. They may be collinear with a surviving variable (i.e.,
they carry the same information). The surviving variables are those that add unique information.

**Sample sizes per subtype are moderate** (n≈97–98) — results in subtype analyses should
be interpreted with more caution than full-sample results, especially for rare comorbidities
with few cases.

**Clustering accuracy vs RIPoSt-SV accuracy are not directly comparable** — RIPoSt-SV was
specifically trained to predict CSED; clustering is unsupervised. The comparison is meaningful
but conceptually asymmetric.

**Gender encoding:** Genere is encoded as M=1, F=0. A negative correlation or negative β
for Genere means males have lower scores — i.e., females have higher ED severity.

---

## Reference

Brancati GE, De Rosa U, Acierno D, et al. (2024). Development of a self-report screening
instrument for emotional dysregulation: the Reactivity, Intensity, Polarity and Stability
questionnaire, screening version (RIPoSt-SV). *Journal of Affective Disorders*, 355, 406–414.
https://doi.org/10.1016/j.jad.2024.03.167
