import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# MySQL 连接配置（可通过环境变量覆盖）
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "clinical_risk_db")

SQLALCHEMY_DATABASE_URI = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)

CSV_PATH = BASE_DIR / "synthetic_clinical_dataset.csv"
MODEL_DIR = BASE_DIR / "saved_models"
MODEL_PATH = MODEL_DIR / "risk_classifier.joblib"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.joblib"

SECRET_KEY = os.getenv("SECRET_KEY", "clinical-risk-analysis-secret-key")
