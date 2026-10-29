# 合成临床指标数据集

本仓库只包含一份患者临床指标表格，供“基于临床指标数据的患者健康风险分析数据分析系统”使用。

- 文件名：`synthetic_clinical_dataset.csv`
- 来源：[Synthetic Clinical Tabular Dataset](https://www.kaggle.com/datasets/uom190346a/synthetic-clinical-tabular-dataset)（Kaggle）
- 记录数：10000 条
- 编码：UTF-8，逗号分隔

这是合成数据，不是真实患者病历。

## 字段说明

| 字段 | 含义 | 取值 |
| --- | --- | --- |
| patient_id | 患者编号 | 1001–11000 |
| age | 年龄 | 0–90 |
| sex | 性别 | Female 5111、Male 4773、Other 116 |
| bmi | 体质指数 | 15.00–50.00 |
| systolic_bp | 收缩压 | 90–180 |
| diastolic_bp | 舒张压 | 60–110 |
| glucose | 血糖 | 70.0–198.6 |
| cholesterol | 胆固醇 | 120.0–300.0 |
| creatinine | 肌酐 | 0.50–2.13 |
| diabetes | 是否糖尿病 | 0 否（8808），1 是（1192） |
| hypertension | 是否高血压 | 0 否（6955），1 是（3045） |
| diagnosis | 诊断 | Normal 5590、Pneumonia 2005、Heart Failure 1763、Sepsis 642 |
| readmission_30d | 30 天内是否再入院 | 0 否（8610），1 是（1390） |
| mortality | 是否死亡 | 0 否（9727），1 是（273） |

表中没有吸烟、饮酒、运动频率和风险等级。这些字段如需使用，应在分析程序中另行计算。
