"""四种数据分析接口。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from config import CSV_PATH
from utils.db import get_or_load_dataframe


def _load_df() -> pd.DataFrame:
    return get_or_load_dataframe(str(CSV_PATH))


def risk_distribution() -> dict:
    """分析1：风险等级分布。"""
    df = _load_df()
    counts = df["risk_level"].value_counts().reindex(["低风险", "中风险", "高风险"], fill_value=0)
    total = int(counts.sum())
    return {
        "categories": counts.index.tolist(),
        "counts": [int(v) for v in counts.values],
        "percentages": [round(v / total * 100, 2) for v in counts.values],
        "total": total,
    }


def age_bmi_analysis() -> dict:
    """分析2：年龄 vs BMI 散点分析。"""
    df = _load_df()
    sample = df.sample(n=min(2000, len(df)), random_state=42) if len(df) > 2000 else df
    series = []
    for level in ["低风险", "中风险", "高风险"]:
        subset = sample[sample["risk_level"] == level]
        series.append({
            "name": level,
            "data": [
                [float(row["age"]), float(row["bmi"])]
                for _, row in subset.iterrows()
            ],
        })
    return {
        "series": series,
        "age_stats": {
            "mean": round(float(df["age"].mean()), 2),
            "min": int(df["age"].min()),
            "max": int(df["age"].max()),
        },
        "bmi_stats": {
            "mean": round(float(df["bmi"].mean()), 2),
            "min": round(float(df["bmi"].min()), 2),
            "max": round(float(df["bmi"].max()), 2),
        },
    }


def smoking_drinking_cross() -> dict:
    """分析3：吸烟 × 饮酒交叉分析。"""
    df = _load_df()
    cross = pd.crosstab(
        df["smoking"].map({0: "不吸烟", 1: "吸烟"}),
        df["drinking"].map({0: "不饮酒", 1: "饮酒"}),
    )
    smoking_labels = cross.index.tolist()
    drinking_labels = cross.columns.tolist()
    matrix = cross.values.tolist()

    risk_cross = []
    for smoke in [0, 1]:
        for drink in [0, 1]:
            subset = df[(df["smoking"] == smoke) & (df["drinking"] == drink)]
            high_risk_rate = round(
                float((subset["risk_level"] == "高风险").mean() * 100), 2
            ) if len(subset) else 0.0
            risk_cross.append({
                "smoking": "吸烟" if smoke else "不吸烟",
                "drinking": "饮酒" if drink else "不饮酒",
                "count": int(len(subset)),
                "high_risk_rate": high_risk_rate,
            })

    return {
        "smoking_labels": smoking_labels,
        "drinking_labels": drinking_labels,
        "matrix": matrix,
        "risk_cross": risk_cross,
    }


def bp_glucose_correlation() -> dict:
    """分析4：血压与血糖相关性分析。"""
    df = _load_df()
    corr_sys = round(float(df["systolic_bp"].corr(df["glucose"])), 4)
    corr_dia = round(float(df["diastolic_bp"].corr(df["glucose"])), 4)

    sample = df.sample(n=min(1500, len(df)), random_state=42) if len(df) > 1500 else df
    scatter = [
        [float(row["systolic_bp"]), float(row["diastolic_bp"]), float(row["glucose"])]
        for _, row in sample.iterrows()
    ]

    glucose_bins = pd.cut(df["glucose"], bins=5)
    bp_by_glucose = (
        df.groupby(glucose_bins, observed=True)[["systolic_bp", "diastolic_bp"]]
        .mean()
        .reset_index()
    )
    bin_labels = [
        f"{interval.left:.0f}-{interval.right:.0f}"
        for interval in bp_by_glucose["glucose"]
    ]

    return {
        "correlation": {
            "systolic_glucose": corr_sys,
            "diastolic_glucose": corr_dia,
        },
        "scatter": scatter,
        "bp_by_glucose": {
            "labels": bin_labels,
            "systolic": [round(v, 2) for v in bp_by_glucose["systolic_bp"]],
            "diastolic": [round(v, 2) for v in bp_by_glucose["diastolic_bp"]],
        },
    }


def dashboard_summary() -> dict:
    df = _load_df()
    return {
        "total_patients": int(len(df)),
        "high_risk_count": int((df["risk_level"] == "高风险").sum()),
        "medium_risk_count": int((df["risk_level"] == "中风险").sum()),
        "low_risk_count": int((df["risk_level"] == "低风险").sum()),
        "avg_age": round(float(df["age"].mean()), 1),
        "avg_bmi": round(float(df["bmi"].mean()), 2),
        "diabetes_rate": round(float(df["diabetes"].mean() * 100), 2),
        "hypertension_rate": round(float(df["hypertension"].mean() * 100), 2),
    }
