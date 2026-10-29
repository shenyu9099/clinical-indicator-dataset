# -*- coding: utf-8 -*-
"""基于临床指标数据的患者健康风险分析：提纲 Word + 图表（输出至本项目目录）"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    RocCurveDisplay,
    accuracy_score,
    classification_report,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import LabelEncoder

PROJ = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJ))

from utils.data_processor import encode_features, get_feature_columns, load_and_enrich  # noqa: E402

DATA = PROJ / "synthetic_clinical_dataset.csv"
CHART_DIR = PROJ / "论文选题图表"
OUT_DOCX = PROJ / "23论文选题-学生在线回答提纲_患者健康风险分析_含图表.docx"

TOPIC = "基于临床指标数据的患者健康风险分析数据分析系统的设计与实现"
URL = "https://www.kaggle.com/datasets/uom190346a/synthetic-clinical-tabular-dataset"
TECH = "Python、Flask、Pandas、scikit-learn、MySQL、ECharts"

FONT_PROP = None
RISK_ORDER = ["低风险", "中风险", "高风险"]
RISK_COLORS = {"低风险": "#059669", "中风险": "#ea580c", "高风险": "#dc2626"}


def setup_font():
    global FONT_PROP
    for path in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
        if Path(path).exists():
            FONT_PROP = fm.FontProperties(fname=path)
            plt.rcParams["font.family"] = FONT_PROP.get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False
    sns.set_theme(style="whitegrid")


def cn(ax, title=None, xlabel=None, ylabel=None):
    if title:
        ax.set_title(title, fontproperties=FONT_PROP, fontsize=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontproperties=FONT_PROP)
    if ylabel:
        ax.set_ylabel(ylabel, fontproperties=FONT_PROP)
    for lab in list(ax.get_xticklabels()) + list(ax.get_yticklabels()):
        lab.set_fontproperties(FONT_PROP)
    leg = ax.get_legend()
    if leg:
        for t in leg.get_texts():
            t.set_fontproperties(FONT_PROP)


def save_fig(fig, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def add_run(p, text, bold=False, size=11):
    r = p.add_run(text)
    r.bold = bold
    r.font.size = Pt(size)
    r.font.name = "宋体"


def add_title(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_run(p, text, bold=True, size=18)


def add_h(doc, text, level=2):
    doc.add_heading(text, level=level)


def add_p(doc, text):
    p = doc.add_paragraph()
    add_run(p, text)


def add_bullets(doc, items):
    for it in items:
        p = doc.add_paragraph()
        add_run(p, f"• {it}")


def load_data() -> tuple[pd.DataFrame, dict]:
    df = load_and_enrich(str(DATA))
    risk_counts = df["risk_level"].value_counts().reindex(RISK_ORDER, fill_value=0)
    stats = {
        "rows": len(df),
        "age_mean": round(df["age"].mean(), 1),
        "bmi_mean": round(df["bmi"].mean(), 1),
        "glucose_mean": round(df["glucose"].mean(), 1),
        "diabetes_rate": round(df["diabetes"].mean() * 100, 2),
        "hypertension_rate": round(df["hypertension"].mean() * 100, 2),
        "risk_counts": {k: int(v) for k, v in risk_counts.items()},
        "corr_sys_glu": round(df["systolic_bp"].corr(df["glucose"]), 4),
        "corr_dia_glu": round(df["diastolic_bp"].corr(df["glucose"]), 4),
    }
    return df, stats


def train_model(df: pd.DataFrame):
    feature_cols = get_feature_columns()
    encoded = encode_features(df)
    x = encoded[feature_cols]
    y = df["risk_level"].values

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    xtr, xte, ytr, yte = train_test_split(
        x, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    grid = GridSearchCV(
        RandomForestClassifier(random_state=42, class_weight="balanced"),
        {
            "n_estimators": [100, 150],
            "max_depth": [8, 12],
            "min_samples_split": [2, 5],
        },
        cv=3,
        scoring="f1_weighted",
        n_jobs=-1,
    )
    grid.fit(xtr, ytr)
    best = grid.best_estimator_
    pred = best.predict(xte)
    proba = best.predict_proba(xte)

    high_idx = list(le.classes_).index("高风险")
    yte_bin = (yte == high_idx).astype(int)
    pred_bin = (pred == high_idx).astype(int)
    proba_high = proba[:, high_idx]

    metrics = {
        "accuracy": round(accuracy_score(yte, pred), 4),
        "f1_weighted": round(f1_score(yte, pred, average="weighted"), 4),
        "auc_high": round(roc_auc_score(yte_bin, proba_high), 4),
        "best_params": str(grid.best_params_),
        "report": classification_report(yte, pred, target_names=le.classes_),
    }

    imp = pd.Series(best.feature_importances_, index=feature_cols).sort_values(ascending=True)
    return best, metrics, imp, xte, yte, pred, proba_high, yte_bin, le


def make_charts(df, stats, metrics, imp, yte, pred, proba_high, yte_bin, le) -> list[Path]:
    paths: list[Path] = []

    # 图1 风险等级分布
    counts = [stats["risk_counts"][k] for k in RISK_ORDER]
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.bar(RISK_ORDER, counts, color=[RISK_COLORS[k] for k in RISK_ORDER])
    cn(ax, "图1 患者健康风险等级分布", "风险等级", "人数")
    for i, v in enumerate(counts):
        pct = v / stats["rows"] * 100
        ax.text(i, v + 80, f"{pct:.1f}%", ha="center", fontproperties=FONT_PROP, fontsize=9)
    p = CHART_DIR / "图1_风险等级分布.png"
    save_fig(fig, p)
    paths.append(p)

    # 图2 年龄 vs BMI
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sample = df.sample(n=min(2500, len(df)), random_state=42)
    for level in RISK_ORDER:
        sub = sample[sample["risk_level"] == level]
        ax.scatter(sub["age"], sub["bmi"], alpha=0.4, s=16, c=RISK_COLORS[level], label=level)
    cn(ax, "图2 年龄与 BMI 分布（按风险等级着色）", "年龄", "BMI")
    ax.legend(prop=FONT_PROP, markerscale=1.5)
    p = CHART_DIR / "图2_年龄与BMI.png"
    save_fig(fig, p)
    paths.append(p)

    # 图3 吸烟×饮酒 高风险率
    rows = []
    for smoke in [0, 1]:
        for drink in [0, 1]:
            sub = df[(df["smoking"] == smoke) & (df["drinking"] == drink)]
            rate = (sub["risk_level"] == "高风险").mean() * 100 if len(sub) else 0
            rows.append({
                "smoking": "Non-smoker" if smoke == 0 else "Smoker",
                "drinking": "Non-drinker" if drink == 0 else "Drinker",
                "rate": rate,
            })
    heat_df = pd.DataFrame(rows).pivot(index="drinking", columns="smoking", values="rate")
    heat_df.index = ["Non-drinker", "Drinker"]
    fig, ax = plt.subplots(figsize=(5.5, 4))
    sns.heatmap(
        heat_df,
        annot=True,
        fmt=".1f",
        cmap="Reds",
        ax=ax,
        cbar_kws={"label": "High risk rate (%)"},
    )
    cn(ax, "图3 吸烟×饮酒交叉分析（高风险率%）", "Smoking", "Drinking")
    p = CHART_DIR / "图3_吸烟饮酒交叉.png"
    save_fig(fig, p)
    paths.append(p)

    # 图4 血压与血糖相关性
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    sample = df.sample(n=min(1500, len(df)), random_state=42)
    axes[0].scatter(sample["systolic_bp"], sample["glucose"], alpha=0.35, s=12, c="#2563eb")
    cn(axes[0], f"收缩压 vs 血糖 (r={stats['corr_sys_glu']})", "收缩压(mmHg)", "血糖")
    axes[1].scatter(sample["diastolic_bp"], sample["glucose"], alpha=0.35, s=12, c="#7c3aed")
    cn(axes[1], f"舒张压 vs 血糖 (r={stats['corr_dia_glu']})", "舒张压(mmHg)", "血糖")
    p = CHART_DIR / "图4_血压血糖相关性.png"
    save_fig(fig, p)
    paths.append(p)

    # 图5 混淆矩阵
    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    ConfusionMatrixDisplay.from_predictions(
        yte, pred, display_labels=le.classes_, ax=ax, cmap="Blues"
    )
    cn(ax, "图5 疾病风险等级预测混淆矩阵")
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontproperties(FONT_PROP)
    p = CHART_DIR / "图5_混淆矩阵.png"
    save_fig(fig, p)
    paths.append(p)

    # 图6 高风险 ROC
    fig, ax = plt.subplots(figsize=(6, 4.5))
    RocCurveDisplay.from_predictions(yte_bin, proba_high, ax=ax)
    cn(ax, f"图6 高风险识别 ROC（AUC={metrics['auc_high']}）")
    p = CHART_DIR / "图6_ROC曲线.png"
    save_fig(fig, p)
    paths.append(p)

    # 图7 特征重要性
    fig, ax = plt.subplots(figsize=(7, 4.5))
    imp.plot(kind="barh", ax=ax, color="#0d9488")
    cn(ax, "图7 关键特征重要性（随机森林）", "重要性", "特征")
    p = CHART_DIR / "图7_特征重要性.png"
    save_fig(fig, p)
    paths.append(p)

    return paths


def build_word(paths: list[Path], stats: dict, metrics: dict):
    doc = Document()
    add_title(doc, "23论文选题-学生在线回答提纲（患者健康风险分析·含图表）")
    add_p(doc, "方向：数据分析 + 机器学习 | 技术栈：" + TECH)

    add_h(doc, "1. 展示论文完整题目", 2)
    add_p(doc, f"《{TOPIC}》")

    add_h(doc, "2. 展示数据集来源（含网站）", 2)
    add_p(doc, "数据集来源平台：Kaggle")
    add_p(doc, f"数据集网址：{URL}")
    add_p(doc, "数据集名称：Synthetic Clinical Tabular Dataset（合成临床表格数据）")
    add_p(doc, f"本地目录：{PROJ.name} / synthetic_clinical_dataset.csv")

    add_h(doc, "3. 展示原始数据文件与有效字段", 2)
    rc = stats["risk_counts"]
    add_p(doc, (
        f"主数据文件 synthetic_clinical_dataset.csv —— 共 {stats['rows']:,} 条患者记录。\n"
        f"样本概况：平均年龄约 {stats['age_mean']} 岁，平均 BMI 约 {stats['bmi_mean']}，"
        f"平均血糖约 {stats['glucose_mean']} mg/dL；糖尿病占比约 {stats['diabetes_rate']}%，"
        f"高血压占比约 {stats['hypertension_rate']}%。\n"
        f"综合风险等级分布：低风险 {rc['低风险']:,} 人、中风险 {rc['中风险']:,} 人、"
        f"高风险 {rc['高风险']:,} 人。"
    ))
    add_p(doc, "原始字段说明：")
    add_bullets(doc, [
        "patient_id：患者编号",
        "age：年龄（连续变量）",
        "sex：性别（Male/Female）",
        "bmi：体质指数",
        "systolic_bp / diastolic_bp：收缩压 / 舒张压（mmHg）",
        "glucose：血糖（mg/dL）",
        "cholesterol：胆固醇",
        "creatinine：肌酐",
        "diabetes / hypertension：是否糖尿病 / 高血压（0/1）",
        "diagnosis：诊断（Normal/Pneumonia/Heart Failure/Sepsis 等）",
        "readmission_30d / mortality：30 天再入院 / 死亡（0/1）",
    ])
    add_p(doc, "特征工程派生字段（原始 Kaggle 数据不含生活方式，本项目确定性派生）：")
    add_bullets(doc, [
        "smoking / drinking：是否吸烟 / 饮酒（0/1，基于年龄、BMI、血压等概率派生，可复现）",
        "exercise_freq：运动频率（很少/偶尔/经常/每天）",
        "risk_level：疾病风险标签（低/中/高风险，综合诊断、死亡、再入院及慢病情况判定）",
    ])

    add_h(doc, "4. 数据分析的意义与行业问题（谁受益）", 2)
    add_p(doc, (
        "面向基层医疗机构与健康管理人员：分析年龄、性别、BMI、血压、胆固醇、血糖和生活方式等因素"
        "对患者健康风险的影响，建立疾病风险预测模型，为健康筛查、慢病管理和个性化干预提供依据。"
        "系统用 Pandas 清洗与特征工程、sklearn 三分类建模、Flask + ECharts 可视化看板，"
        "服务社区卫生、体检中心与健康管理岗位。"
    ))

    add_h(doc, "5. 软件项目开发的技术架构", 2)
    add_p(doc, (
        "数据层：CSV → Pandas 清洗与派生特征 → MySQL 入库\n"
        "分析层：Pandas 统计分析 + scikit-learn（GridSearchCV、随机森林多分类）\n"
        "服务层：Flask（注册/登录、患者列表检索翻页、风险预测接口、图表数据 API）\n"
        "展示层：ECharts（风险分布、年龄-BMI、吸烟饮酒交叉、血压血糖相关、混淆矩阵等≥5张）\n"
        f"技术栈：{TECH}"
    ))

    add_h(doc, "6. 核心功能说明", 2)
    add_p(doc, "① Pandas 数据处理：读取 CSV、派生 smoking/drinking/exercise_freq/risk_level、编码入库。")
    add_p(doc, "② 机器学习（多分类）：")
    add_p(doc, (
        f"模型：随机森林 + GridSearchCV；目标：预测 risk_level（低/中/高风险三分类）。\n"
        f"特征：年龄、性别、BMI、收缩压、舒张压、血糖、胆固醇、吸烟、饮酒、运动频率。\n"
        f"实验结果（测试集）：准确率≈{metrics['accuracy']*100:.2f}%，"
        f"加权 F1≈{metrics['f1_weighted']}，高风险识别 AUC≈{metrics['auc_high']}；"
        f"最优参数：{metrics['best_params']}"
    ))
    add_p(doc, "③ 四种核心分析 + 模型评估：")
    add_bullets(doc, [
        "风险等级分布：低/中/高风险人数与占比（图1）",
        "年龄 vs BMI：散点图按风险等级着色（图2）",
        "吸烟×饮酒：交叉热力图展示不同生活方式组合的高风险率（图3）",
        "血压与血糖相关性：收缩压/舒张压与血糖散点及相关系数（图4）",
        "模型评估：混淆矩阵（图5）、高风险 ROC（图6）、特征重要性（图7）",
    ])

    add_h(doc, "7. 图像绘制（对应分析结果）", 2)
    captions = [
        "图1 患者健康风险等级分布柱状图",
        "图2 年龄与 BMI 散点图（风险等级着色）",
        "图3 吸烟×饮酒交叉分析热力图",
        "图4 血压与血糖相关性散点图",
        "图5 疾病风险等级预测混淆矩阵",
        "图6 高风险识别 ROC 曲线",
        "图7 关键特征重要性条形图",
    ]
    add_bullets(doc, captions)

    doc.add_page_break()
    add_h(doc, "附图（真实数据生成）", 2)
    for cap, img in zip(captions, paths):
        add_p(doc, cap)
        if img.exists():
            doc.add_picture(str(img), width=Inches(6.2))
        doc.add_paragraph("")

    doc.save(OUT_DOCX)
    print("saved", OUT_DOCX)


def main():
    setup_font()
    print("loading data...")
    df, stats = load_data()
    print("training...")
    model, metrics, imp, xte, yte, pred, proba_high, yte_bin, le = train_model(df)
    print("metrics", metrics)
    paths = make_charts(df, stats, metrics, imp, yte, pred, proba_high, yte_bin, le)
    build_word(paths, stats, metrics)
    print("done")


if __name__ == "__main__":
    main()
