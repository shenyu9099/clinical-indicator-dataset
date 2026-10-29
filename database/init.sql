-- 临床健康风险分析系统 - 数据库初始化脚本
CREATE DATABASE IF NOT EXISTS clinical_risk_db
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE clinical_risk_db;

DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    patient_id      INT NOT NULL UNIQUE,
    age             INT NOT NULL,
    sex             VARCHAR(10) NOT NULL,
    bmi             DECIMAL(5,2) NOT NULL,
    systolic_bp     DECIMAL(6,2) NOT NULL,
    diastolic_bp    DECIMAL(6,2) NOT NULL,
    glucose         DECIMAL(6,2) NOT NULL,
    cholesterol     DECIMAL(6,2) NOT NULL,
    creatinine      DECIMAL(5,2) NOT NULL,
    diabetes        TINYINT NOT NULL DEFAULT 0,
    hypertension    TINYINT NOT NULL DEFAULT 0,
    diagnosis       VARCHAR(50) NOT NULL,
    readmission_30d TINYINT NOT NULL DEFAULT 0,
    mortality       TINYINT NOT NULL DEFAULT 0,
    smoking         TINYINT NOT NULL DEFAULT 0 COMMENT '是否吸烟 0否1是',
    drinking        TINYINT NOT NULL DEFAULT 0 COMMENT '是否饮酒 0否1是',
    exercise_freq   VARCHAR(20) NOT NULL DEFAULT '偶尔' COMMENT '运动频率',
    risk_level      VARCHAR(20) NOT NULL COMMENT '风险等级: 低风险/中风险/高风险',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_risk_level (risk_level),
    INDEX idx_age (age),
    INDEX idx_diagnosis (diagnosis)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
