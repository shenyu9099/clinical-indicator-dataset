"""数据预处理与特征工程模块。"""

from __future__ import annotations

import numpy as np
import pandas as pd


EXERCISE_LEVELS = ["很少", "偶尔", "经常", "每天"]
RISK_LEVELS = ["低风险", "中风险", "高风险"]
DIAGNOSIS_RISK_MAP = {
    "Normal": "低风险",
    "Pneumonia": "中风险",
    "Heart Failure": "中风险",
    "Sepsis": "高风险",
}


def derive_risk_level(row: pd.Series) -> str:
    """根据诊断、死亡与再入院情况综合判定风险等级。"""
    if row["mortality"] == 1 or row["diagnosis"] == "Sepsis":
        return "高风险"
    if row["readmission_30d"] == 1 or row["diagnosis"] in ("Heart Failure", "Pneumonia"):
        return "中风险"
    if row["diabetes"] == 1 and row["hypertension"] == 1:
        return "中风险"
    return DIAGNOSIS_RISK_MAP.get(row["diagnosis"], "低风险")


def _seeded_rng(patient_id: int) -> np.random.Generator:
    return np.random.default_rng(int(patient_id))


def derive_lifestyle_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    原始 Kaggle 数据集不含生活方式字段，基于临床指标与患者 ID 确定性派生，
    保证可复现且与风险因素存在合理关联。
    """
    result = df.copy()
    smoking_list = []
    drinking_list = []
    exercise_list = []

    for _, row in result.iterrows():
        rng = _seeded_rng(row["patient_id"])
        age = row["age"]
        bmi = row["bmi"]
        hypertension = row["hypertension"]

        smoke_prob = 0.15 + (age - 40) * 0.004 + (bmi - 25) * 0.01 + hypertension * 0.08
        drink_prob = 0.12 + (age - 35) * 0.003 + (bmi - 22) * 0.008
        smoke_prob = float(np.clip(smoke_prob, 0.05, 0.65))
        drink_prob = float(np.clip(drink_prob, 0.05, 0.55))

        smoking = int(rng.random() < smoke_prob)
        drinking = int(rng.random() < drink_prob)

        exercise_score = (
            2
            + (30 - abs(age - 45)) * 0.02
            - smoking * 0.8
            - drinking * 0.5
            - (bmi - 22) * 0.05
            + rng.normal(0, 0.3)
        )
        exercise_idx = int(np.clip(round(exercise_score), 0, len(EXERCISE_LEVELS) - 1))

        smoking_list.append(smoking)
        drinking_list.append(drinking)
        exercise_list.append(EXERCISE_LEVELS[exercise_idx])

    result["smoking"] = smoking_list
    result["drinking"] = drinking_list
    result["exercise_freq"] = exercise_list
    result["risk_level"] = result.apply(derive_risk_level, axis=1)
    return result


def load_and_enrich(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    return derive_lifestyle_features(df)


def get_feature_columns() -> list[str]:
    return [
        "age",
        "sex",
        "bmi",
        "systolic_bp",
        "diastolic_bp",
        "glucose",
        "cholesterol",
        "smoking",
        "drinking",
        "exercise_freq",
    ]


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    encoded = df.copy()
    encoded["sex"] = encoded["sex"].map({"Male": 1, "Female": 0}).fillna(0).astype(int)
    encoded["exercise_freq"] = encoded["exercise_freq"].map(
        {level: idx for idx, level in enumerate(EXERCISE_LEVELS)}
    ).fillna(1).astype(int)
    return encoded
