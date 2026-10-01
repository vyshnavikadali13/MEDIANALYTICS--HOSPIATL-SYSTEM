"""Data analytics with Pandas and NumPy.

Pipeline: load_df() collects the records from SQLite -> preprocess() cleans them
and adds derived columns -> summary_stats() computes the statistical measures.
"""
import numpy as np
import pandas as pd

from db import get_db
from patients import build_search_query

# Bins are left-inclusive (right=False): e.g. BMI 18.5 counts as "Normal"
AGE_BINS = [0, 13, 20, 36, 51, 66, 121]
AGE_LABELS = ["0-12", "13-19", "20-35", "36-50", "51-65", "66+"]
BMI_BINS = [0, 18.5, 25, 30, np.inf]  # WHO categories
BMI_LABELS = ["Underweight", "Normal", "Overweight", "Obese"]
SUGAR_BINS = [0, 100, 126, np.inf]  # fasting blood sugar, mg/dL
SUGAR_LABELS = ["Normal", "Prediabetic", "Diabetic"]

NUMERIC_COLUMNS = ["age", "height_cm", "weight_kg", "bmi", "blood_sugar",
                   "bp_systolic", "bp_diastolic"]


def load_df(q="", gender=""):
    """Collect: read patient records from SQLite into a DataFrame."""
    sql, params = build_search_query(q, gender)
    return pd.read_sql_query(sql, get_db(), params=params)


def preprocess(df):
    """Clean the raw records and add the derived columns used in the analysis."""
    df = df.copy()

    # 1. Fix data types
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["admission_date"] = pd.to_datetime(df["admission_date"], errors="coerce")

    # 2. Standardise text so "diabetes" and "Diabetes " are counted together
    df["name"] = df["name"].str.strip()
    df["disease"] = df["disease"].str.strip().str.title()

    # 3. Drop records missing the values every analysis depends on
    df = df.dropna(subset=["age", "gender", "height_cm", "weight_kg", "blood_sugar"])

    # 4. Recalculate BMI from height and weight so it is always consistent
    df["bmi"] = np.round(df["weight_kg"] / (df["height_cm"] / 100) ** 2, 1)

    # 5. Derived categories
    df["age_group"] = pd.cut(df["age"], AGE_BINS, labels=AGE_LABELS, right=False)
    df["bmi_category"] = pd.cut(df["bmi"], BMI_BINS, labels=BMI_LABELS, right=False)
    df["sugar_status"] = pd.cut(df["blood_sugar"], SUGAR_BINS, labels=SUGAR_LABELS, right=False)
    return df


def describe(values):
    """Mean, median, standard deviation, min and max of a NumPy array."""
    return {
        "mean": round(float(np.mean(values)), 1),
        "median": round(float(np.median(values)), 1),
        "std": round(float(np.std(values)), 1),
        "min": round(float(np.min(values)), 1),
        "max": round(float(np.max(values)), 1),
    }


def summary_stats(df):
    """Analyse: the statistical measures shown on the dashboard and in the PDF report."""
    if df.empty:
        return {"total": 0}

    age = df["age"].to_numpy()
    bmi = df["bmi"].to_numpy()
    sugar = df["blood_sugar"].to_numpy()

    correlation = None
    if len(df) > 1 and np.std(bmi) > 0 and np.std(sugar) > 0:
        correlation = round(float(np.corrcoef(bmi, sugar)[0, 1]), 2)

    return {
        "total": len(df),
        "age": describe(age),
        "bmi": describe(bmi),
        "sugar": describe(sugar),
        "diabetic": int((df["sugar_status"] == "Diabetic").sum()),
        "by_disease": df["disease"].value_counts().to_dict(),
        "by_gender": df["gender"].value_counts().to_dict(),
        "by_age_group": df["age_group"].value_counts().reindex(AGE_LABELS, fill_value=0).to_dict(),
        "by_bmi_category": df["bmi_category"].value_counts().reindex(BMI_LABELS, fill_value=0).to_dict(),
        "by_sugar_status": df["sugar_status"].value_counts().reindex(SUGAR_LABELS, fill_value=0).to_dict(),
        "bmi_sugar_correlation": correlation,
    }


def _categorize(value, bins, labels):
    if value is None:
        return ""
    return pd.cut([value], bins, labels=labels, right=False)[0]


def bmi_category(bmi):
    return _categorize(bmi, BMI_BINS, BMI_LABELS)


def sugar_status(sugar):
    return _categorize(sugar, SUGAR_BINS, SUGAR_LABELS)
