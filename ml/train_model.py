"""疾病风险分类模型训练（GridSearchCV）。"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder

from config import CSV_PATH, LABEL_ENCODER_PATH, MODEL_DIR, MODEL_PATH
from utils.data_processor import encode_features, get_feature_columns
from utils.db import get_or_load_dataframe


def prepare_training_data(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    feature_cols = get_feature_columns()
    encoded = encode_features(df)
    x = encoded[feature_cols]
    y = df["risk_level"].values
    return x, y


def train_model(df: pd.DataFrame | None = None) -> dict:
    df = df if df is not None else get_or_load_dataframe(str(CSV_PATH))
    x, y = prepare_training_data(df)

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    param_grid = {
        "n_estimators": [100, 200],
        "max_depth": [8, 12, None],
        "min_samples_split": [2, 5],
        "min_samples_leaf": [1, 2],
    }

    base_model = RandomForestClassifier(random_state=42, class_weight="balanced")
    grid_search = GridSearchCV(
        base_model,
        param_grid,
        cv=5,
        scoring="f1_weighted",
        n_jobs=-1,
        verbose=1,
    )
    grid_search.fit(x_train, y_train)

    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(x_test)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1_weighted": round(float(f1_score(y_test, y_pred, average="weighted")), 4),
        "best_params": grid_search.best_params_,
        "classification_report": classification_report(
            y_test, y_pred, target_names=label_encoder.classes_, output_dict=True
        ),
        "feature_importance": dict(
            zip(get_feature_columns(), best_model.feature_importances_.round(4).tolist())
        ),
        "train_size": len(x_train),
        "test_size": len(x_test),
        "classes": label_encoder.classes_.tolist(),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(label_encoder, LABEL_ENCODER_PATH)

    metrics_path = MODEL_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    return metrics


def load_trained_model():
    if not MODEL_PATH.exists() or not LABEL_ENCODER_PATH.exists():
        train_model()
    model = joblib.load(MODEL_PATH)
    label_encoder = joblib.load(LABEL_ENCODER_PATH)
    return model, label_encoder


def predict_risk(patient_data: dict) -> dict:
    model, label_encoder = load_trained_model()
    feature_cols = get_feature_columns()
    df = pd.DataFrame([patient_data])
    encoded = encode_features(df)
    x = encoded[feature_cols]

    proba = model.predict_proba(x)[0]
    pred_idx = int(np.argmax(proba))
    risk_level = label_encoder.inverse_transform([pred_idx])[0]

    return {
        "risk_level": risk_level,
        "probabilities": {
            cls: round(float(p), 4)
            for cls, p in zip(label_encoder.classes_, proba)
        },
    }


if __name__ == "__main__":
    result = train_model()
    print("训练完成")
    print(f"准确率: {result['accuracy']}")
    print(f"F1(加权): {result['f1_weighted']}")
    print(f"最优参数: {result['best_params']}")
