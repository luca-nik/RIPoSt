"""
Central configuration: column definitions, paths, constants.
"""
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DATA_FILE = ROOT / "dati_ripost.xlsx"
SHEET_NAME = "data_ripost_sv"
OUTPUT_DIR = ROOT / "output"

# ── Outcomes ───────────────────────────────────────────────────────────────────
OUTCOME_NED = "RIPoSt_NED"      # continuous ED severity
OUTCOME_SV  = "RIPoSt_SV"       # binary CSED screening (True/False)

# ── Subtype column & labels ────────────────────────────────────────────────────
SUBTYPE_COL = "Specificatore"
SUBTYPES = {
    "full": None,           # no filter
    "inat": "INAT",
    "comb": "COMB",
    "iper": "IPER",         # n=4, descriptive only
}

# ── Columns to EXCLUDE from predictors ────────────────────────────────────────
# All RIPoSt-derived columns (instrument itself) + admin columns
EXCLUDE_COLS = {
    "Column1",          # row index
    "ID_anonimo",       # identifier
    # RIPoSt instrument columns
    "RIPoSt_AI",
    "RIPoSt_P",
    "RIPoSt_N",
    "RIPoSt_EI",
    "RIPoSt_NED",
    "RIPoSt_40",
    "RIPoSt_36",
    "RIPoSt_3",
    "RIPoSt_4",
    "RIPoSt_32",
    "RIPoSt_27",
    "RIPoSt_SV",
    # Subtype (used for stratification, not a predictor)
    "Specificatore",
}

# ── Predictor groups (for readable plots) ─────────────────────────────────────
DEMO_COLS = [
    "Genere", "Age", "school_years", "repeated_grades", "marital_status",
]

CLINICAL_COLS = [
    "mood",
    "FH_bipolar", "FH_mood", "FH_neurodev", "FH_anxiety",
    "FH_psychosis", "FH_suicide", "FH_SUD",
    "alcool", "opioids", "cannabis", "bdz", "cocaine", "stimulants",
    "separation_anx", "panic", "agoraphobia", "social_anx", "GAD", "OCD",
    "anorexia", "bulimia", "BED", "dismorfofobia",
    "conversion", "somatic", "Tourette", "tic",
    "oppositional", "conduct",
    "first_referral", "mood_onset",
    "mood_any", "sud_any", "anx_any", "eat_any", "ocd_any", "imp_any",
    "Trattato",
]

# Scale totals only (for compact plots)
SCALE_TOTALS = [
    "CAARS_A", "CAARS_B", "CAARS_C", "CAARS_D",
    "BRIEF_GEC", "BRIEF_BRI", "BRIEF_MI",
    "FAST_TOT",
    "ASRS",
    "LPFS_S", "LPFS_I",
    "HCL_TOT",
    "TEMPS_D", "TEMPS_C", "TEMPS_H", "TEMPS_I", "TEMPS_A",
    "PID_NEG", "PID_DET", "PID_ANT", "PID_DIS", "PID_ANA", "PID_PSY",
    "BIS_TOT",
    "BRIAN_TOT",
]

# Scale subscales (excluding totals already listed above)
SCALE_SUBSCALES = [
    "Inhibit", "Shift", "Emotional control", "Self-monitor",
    "Initiate", "Working memory", "Plan/Organize", "Task monitor",
    "Organization of materials",
    "FAST_A", "FAST_O", "FAST_C", "FAST_F", "FAST_I", "FAST_L",
    "HCL_F1", "HCL_F2",
    "BIS_A", "BIS_M", "BIS_P",
    "BRIAN_SLE", "BRIAN_ACT", "BRIAN_SOC", "BRIAN_EAT", "BRIAN_TYP",
]

# Ordered groups for plots
PREDICTOR_GROUPS = {
    "Demographics": DEMO_COLS,
    "Clinical": CLINICAL_COLS,
    "Scale totals": SCALE_TOTALS,
    "Scale subscales": SCALE_SUBSCALES,
}

# ── Plot readability threshold ─────────────────────────────────────────────────
# Warn when a plot would show more than this many variables
MAX_VARS_READABLE = 30

# ── Significance thresholds ────────────────────────────────────────────────────
ALPHA = 0.05
