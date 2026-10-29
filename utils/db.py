"""数据库连接与数据访问。"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import SQLALCHEMY_DATABASE_URI
from utils.data_processor import derive_lifestyle_features, load_and_enrich


def get_engine() -> Engine:
    return create_engine(SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)


def fetch_patients_df(engine: Engine | None = None) -> pd.DataFrame:
    engine = engine or get_engine()
    query = """
        SELECT patient_id, age, sex, bmi, systolic_bp, diastolic_bp,
               glucose, cholesterol, creatinine, diabetes, hypertension,
               diagnosis, readmission_30d, mortality,
               smoking, drinking, exercise_freq, risk_level
        FROM patients
    """
    return pd.read_sql(query, engine)


def import_csv_to_mysql(csv_path: str, engine: Engine | None = None) -> int:
    engine = engine or get_engine()
    df = load_and_enrich(csv_path)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM patients"))
        df.to_sql("patients", conn, if_exists="append", index=False)

    return len(df)


def get_or_load_dataframe(csv_path: str) -> pd.DataFrame:
    """优先从 MySQL 读取，连接失败时回退到 CSV 内存处理。"""
    try:
        return fetch_patients_df()
    except Exception:
        return derive_lifestyle_features(pd.read_csv(csv_path))
