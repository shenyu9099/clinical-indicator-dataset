# -*- coding: utf-8 -*-
"""
基于蓝莓开题/任务书版式，生成《基于临床指标数据的患者健康风险分析数据分析系统》开题报告与任务书。
方向：数据分析（数据获取→处理→持久化→分析→可视化→测试）
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from lxml import etree
from matplotlib.patches import FancyBboxPatch

ROOT = Path(r"i:\2027毕设")
PROJ = ROOT / "基于临床指标数据的患者健康风险分析数据分析系统的设计与实现"
SRC_KT = ROOT / "2022XXXX-XXXX姓名-野生蓝莓产量数据分析系统的设计与实现-开题报告.docx"
SRC_RW = ROOT / "2022XXXX-XXXX姓名-野生蓝莓产量数据分析系统的设计与实现-任务书.docx"
TOPIC = "基于临床指标数据的患者健康风险分析数据分析系统的设计与实现"
OUT_KT = PROJ / f"2022XXXX-XXXX姓名-{TOPIC}-开题报告.docx"
OUT_RW = PROJ / f"2022XXXX-XXXX姓名-{TOPIC}-任务书.docx"
ROADMAP_PNG = PROJ / "技术路线图.png"

TECH = "Python、Flask、Pandas、scikit-learn、MySQL、ECharts"
DATA_URL = "https://www.kaggle.com/datasets/uom190346a/synthetic-clinical-tabular-dataset"
DATA_NAME = "Synthetic Clinical Tabular Dataset"
_BOOKMARK_ID = 300
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
_CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REF_LEFT_INDENT = Pt(28.3)
REF_FIRST_INDENT = Pt(-28.2)
DATA_LABEL_INDENT = Pt(84)


def set_run_font(run, east="宋体", ascii_font="Times New Roman", size=12, bold=False):
    run.font.name = ascii_font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), east)
    run.font.size = Pt(size)
    run.bold = bold


def clear_cell(cell):
    tc = cell._tc
    for child in list(tc):
        if child.tag.endswith("}p"):
            tc.remove(child)


def add_text_run(paragraph, text, size=12, bold=False):
    run = paragraph.add_run(text)
    set_run_font(run, size=size, bold=bold)
    return run


def add_label_value_lines(cell, label: str, value: str, first_indent=True):
    """标签单独一行，内容另起一行并与上行内容左对齐。"""
    p_label = new_para(cell, first_indent=first_indent, line_spacing=1.5)
    add_text_run(p_label, label, size=12)
    p_val = new_para(cell, first_indent=False, line_spacing=1.5)
    pf = p_val.paragraph_format
    pf.left_indent = DATA_LABEL_INDENT
    pf.first_line_indent = Pt(0)
    add_text_run(p_val, value, size=12)


def write_dataset_info(cell, first_indent=True):
    add_label_value_lines(cell, "数据集名称：", f"{DATA_NAME}。", first_indent=first_indent)
    add_label_value_lines(cell, "数据集网址：", DATA_URL, first_indent=first_indent)


def strip_docx_comments(path: Path):
    """删除模板遗留批注（如“选择这项”）及批注关系。"""
    w = f"{{{_W_NS}}}"
    skip_files = {
        "word/comments.xml",
        "word/commentsExtended.xml",
        "word/commentsIds.xml",
        "word/commentsExtensible.xml",
    }
    comment_tags = (f"{w}commentRangeStart", f"{w}commentRangeEnd", f"{w}commentReference")

    with zipfile.ZipFile(path, "r") as zin:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename in skip_files:
                    continue
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    root = etree.fromstring(data)
                    for tag in comment_tags:
                        for el in root.findall(f".//{tag}"):
                            el.getparent().remove(el)
                    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                elif item.filename == "word/_rels/document.xml.rels":
                    root = etree.fromstring(data)
                    rel_tag = f"{{{_REL_NS}}}Relationship"
                    for rel in list(root.findall(rel_tag)):
                        if "comments" in (rel.get("Type") or ""):
                            root.remove(rel)
                    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                elif item.filename == "[Content_Types].xml":
                    root = etree.fromstring(data)
                    ct_tag = f"{{{_CT_NS}}}Override"
                    for node in list(root.findall(ct_tag)):
                        if "comments" in (node.get("PartName") or ""):
                            root.remove(node)
                    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
                zout.writestr(item, data)
    path.write_bytes(buf.getvalue())


def set_keep_with_next(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    keep = OxmlElement("w:keepNext")
    p_pr.append(keep)

def add_cite(paragraph, num: int, size=12):
    run = paragraph.add_run(f"[{num}]")
    set_run_font(run, size=size)
    run.font.superscript = True
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.underline = False

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("w:anchor"), f"ref{num}")
    hyperlink.set(qn("w:history"), "1")
    r_elem = run._r
    paragraph._p.remove(r_elem)
    rPr = r_elem.get_or_add_rPr()
    for tag in ("w:color", "w:u", "w:vertAlign"):
        for old in rPr.findall(qn(tag)):
            rPr.remove(old)
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    rPr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "none")
    rPr.append(u)
    vert = OxmlElement("w:vertAlign")
    vert.set(qn("w:val"), "superscript")
    rPr.append(vert)
    hyperlink.append(r_elem)
    paragraph._p.append(hyperlink)


def add_bookmark(paragraph, name: str):
    global _BOOKMARK_ID
    _BOOKMARK_ID += 1
    bid = str(_BOOKMARK_ID)
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), bid)
    start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd")
    end.set(qn("w:id"), bid)
    paragraph._p.insert(0, start)
    paragraph._p.append(end)


def new_para(cell, first_indent=True, line_spacing=1.5):
    p = cell.add_paragraph()
    pf = p.paragraph_format
    if line_spacing:
        pf.line_spacing = line_spacing
    if first_indent:
        pf.first_line_indent = Pt(24)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def write_plain_paras(cell, paragraphs, first_indent=True, line_spacing=1.5, size=12):
    clear_cell(cell)
    for text in paragraphs:
        p = new_para(cell, first_indent=first_indent, line_spacing=line_spacing)
        add_text_run(p, text, size=size)


def write_plain(cell, text, size=12, bold=False, first_indent=False, line_spacing=None):
    clear_cell(cell)
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if line_spacing:
        p.paragraph_format.line_spacing = line_spacing
    if first_indent:
        p.paragraph_format.first_line_indent = Pt(24)
    add_text_run(p, text, size=size, bold=bold)


def set_merged_plain(row, text, **kwargs):
    if isinstance(text, list):
        write_plain_paras(row.cells[0], text, **kwargs)
    else:
        write_plain(row.cells[0], text, **kwargs)


def write_rich_para(cell, parts, first_indent=True):
    p = new_para(cell, first_indent=first_indent, line_spacing=1.5)
    for part in parts:
        if isinstance(part, int):
            add_cite(p, part)
        else:
            add_text_run(p, part, size=12)
    return p


def make_roadmap_png(path: Path):
    """
    针对老师批注重画：框内写本课题专属内容，避免“随便放谁论文里都行”；
    删文献调研/论文撰写/课题完成；用数据保存不用数据持久化；起止圆角、四框对齐。
    """
    for fp in [r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\msyh.ttc"]:
        if Path(fp).exists():
            from matplotlib import font_manager as fm

            plt.rcParams["font.family"] = fm.FontProperties(fname=fp).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(9.2, 10.2), dpi=220)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    def box(cx, cy, w, h, text, rounded=False, fontsize=9.5):
        x0, y0 = cx - w / 2, cy - h / 2
        if rounded:
            r = min(w, h) * 0.45
            style = f"round,pad=0.02,rounding_size={r:.3f}"
            lw = 1.7
        else:
            style = "square,pad=0.015"
            lw = 1.4
        ax.add_patch(
            FancyBboxPatch(
                (x0, y0),
                w,
                h,
                boxstyle=style,
                linewidth=lw,
                edgecolor="black",
                facecolor="white",
                mutation_aspect=1.0,
            )
        )
        ax.text(cx, cy, text, ha="center", va="center", fontsize=fontsize, color="black", linespacing=1.2)
        return {"cx": cx, "cy": cy, "w": w, "h": h, "x0": x0, "y0": y0, "x1": x0 + w, "y1": y0 + h}

    def arrow(x1, y1, x2, y2):
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="-|>", color="black", lw=1.2, mutation_scale=13),
        )

    def vline(x, y1, y2):
        ax.plot([x, x], [y1, y2], color="black", lw=1.2)

    def hline(y, x1, x2):
        ax.plot([x1, x2], [y, y], color="black", lw=1.2)

    # 主线：本课题专属表述，换题后框文对不上
    b_start = box(50, 94, 22, 5.0, "确定课题", rounded=True, fontsize=11)
    b_data = box(50, 81, 28, 5.6, "获取合成临床指标数据\n(BMI/血压/血糖等)", fontsize=9)
    b_req = box(50, 68, 28, 5.6, "需求分析\n(风险筛查·等级预测)", fontsize=9)
    b_func = box(50, 55, 22, 5.0, "功能设计", fontsize=10.5)

    y4 = 38
    b_save = box(12.5, y4, 20, 7.2, "数据保存\nMySQL患者临床表", fontsize=8.8)
    b_proc = box(37.5, y4, 20, 7.2, "数据处理\n清洗派生风险标签\n吸烟/饮酒/运动", fontsize=8.5)
    b_ana = box(62.5, y4, 20, 7.2, "数据分析\n风险分布·交叉热力\n随机森林三分类", fontsize=8.5)
    b_vis = box(87.5, y4, 20, 7.2, "数据可视化\n柱状/散点/热力\n混淆矩阵·ROC", fontsize=8.5)

    b_test = box(50, 21, 30, 5.6, "系统测试\n检索·统计·风险预测接口", fontsize=9)
    b_end = box(50, 8, 22, 5.0, "系统完成", rounded=True, fontsize=11)

    arrow(50, b_start["y0"], 50, b_data["y1"])
    arrow(50, b_data["y0"], 50, b_req["y1"])
    arrow(50, b_req["y0"], 50, b_func["y1"])

    mid_top = (b_func["y0"] + b_save["y1"]) / 2
    vline(50, b_func["y0"], mid_top)
    hline(mid_top, 12.5, 87.5)
    arrow(12.5, mid_top, 12.5, b_save["y1"])
    arrow(37.5, mid_top, 37.5, b_proc["y1"])
    arrow(62.5, mid_top, 62.5, b_ana["y1"])
    arrow(87.5, mid_top, 87.5, b_vis["y1"])

    mid_bot = (b_save["y0"] + b_test["y1"]) / 2
    vline(12.5, b_save["y0"], mid_bot)
    vline(37.5, b_proc["y0"], mid_bot)
    vline(62.5, b_ana["y0"], mid_bot)
    vline(87.5, b_vis["y0"], mid_bot)
    hline(mid_bot, 12.5, 87.5)
    arrow(50, mid_bot, 50, b_test["y1"])
    arrow(50, b_test["y0"], 50, b_end["y1"])

    fig.tight_layout(pad=0.12)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white", pad_inches=0.1)
    plt.close(fig)


def insert_picture_in_cell(cell, image_path: Path, width_inch=4.6):
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.keep_together = True
    pf.space_before = Pt(6)
    pf.space_after = Pt(3)
    run = p.add_run()
    run.add_picture(str(image_path), width=Inches(width_inch))
    cap = cell.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run("图1  基于临床指标数据的患者健康风险分析数据分析系统技术路线图")
    set_run_font(r, size=10.5)



REFS = [
    "[1] 丁文祥,林晨旭,张彩云. 机器学习算法在有害藻华早期预警模型的应用进展[J/OL].海洋预报,1-25[2025-09-17].",
    "[2] 李华,古金本,陶毅. 基于机器学习预测FRP筋-混凝土粘结强度[J/OL].工业建筑,1-16[2025-09-17].",
    "[3] 刘博,黄昊辉,李奇蕴,等. 基于机器学习与粒子群算法的微结构辐射冷却性能优化研究[J/OL].化工学报,1-10[2025-09-17].",
    "[4] 曹庭伟,Xu,Yr.,等.基于机器学习和ENSO动力模式构建华南冬春季降水的预报模型[C]//中国气象学会.第36届中国气象学会年会摘要集——S17 东亚气候系统的变异机理及预测.中国民用航空飞行学院;,2025:21-25.",
    "[5] 郝斌,朱沁玲,李琦. 基于不同机器学习算法的水位异常值检测性能对比研究[J/OL].水利水电快报,1-7[2025-09-17].",
    "[6] 胡选成. 基于机器学习的互联网医疗平台医生推荐度预测分析[J].江苏商论,2025,(09):43-47.",
    "[7] 卢泓旭,王仁浚,高红均,等. 考虑温度与分时电价对工业负荷基线影响的机器学习预测方法[J/OL].南方电网技术,1-16[2025-09-17].",
    "[8] 陈厚霖,王加虎. 基于机器学习的平原城市圩区内涝积水快速模拟方法研究[J/OL].人民珠江,1-21[2025-09-17].",
    "[9] 陈威,钱琴芳,胡一飞,等. 基于机器学习的纺织品洗液沾色程度AI评估模型构建[J/OL].染整技术,1-10[2025-09-17].",
    "[10] 黄卓懿,彭龙,徐浩,等. 基于机器学习方法的操作系统优化研究综述[J/OL].计算机工程与科学,1-15[2025-09-17].",
    "[11] Vo T L, Vu T, Pham N T, et al. Machine learning-based models for prediction of in-hospital mortality in patients with dengue shock syndrome[J]. World journal of methodology,2025,15(3):101837.",
    "[12] Drăgoi L A, Nemeș M R. Electronic Pediatrician, a non-machine learning prototype artificial intelligence software for pediatric computer-assisted pathophysiologic diagnosis[J]. World journal of methodology,2025,15(3):100903.",
    "[13] Tomme L, Lengyel I, Vermeire H F, et al. Accelerating reaction rate predictions: a machine learning approach using a novel quantum chemical property for nucleophilic aromatic substitutions[J]. Machine Learning: Science and Technology,2025,6(3):035044.",
]

PURPOSE = [
    "1. 研究目的",
    "基层医疗与健康管理场景中，年龄、BMI、血压、血糖、胆固醇及生活方式等因素共同影响患者健康风险，但临床指标分散、风险等级划分依赖经验，难以形成可复用的量化分析流程。因此，本课题基于Kaggle公开的合成临床表格数据集（约10000条患者记录），设计并实现“基于临床指标数据的患者健康风险分析数据分析系统”。系统采用Pandas完成清洗与特征工程（派生吸烟、饮酒、运动频率及低/中/高风险标签），数据持久化至MySQL；利用Flask提供患者检索与风险预测接口；以前端ECharts展示风险等级分布、年龄与BMI散点、吸烟×饮酒交叉热力图、血压与血糖相关性等不少于5类图表；并构建随机森林多分类模型开展疾病风险等级预测。通过本系统，为社区卫生、体检中心与健康管理人员的筛查与慢病干预提供数据支撑。",
    "2. 研究意义",
    "通过本项目研究，计划完成一个功能完整、便于演示的患者健康风险分析系统。系统将具备数据管理、多维统计分析与机器学习预测等核心功能：用户可按年龄、性别、诊断等条件检索患者记录；通过ECharts柱状图查看低/中/高风险人数与占比，通过散点图观察年龄与BMI在不同风险等级上的分布，通过热力图分析吸烟与饮酒组合的高风险率，通过散点图展示收缩压/舒张压与血糖的相关关系，并通过混淆矩阵、ROC曲线与特征重要性图理解模型结果。系统将集成scikit-learn中的随机森林（RandomForestClassifier）多分类模型，以年龄、性别、BMI、收缩压、舒张压、血糖、胆固醇、吸烟、饮酒、运动频率等为输入特征，预测患者风险等级（低风险/中风险/高风险），并以准确率、加权F1值和AUC评估模型效果，为健康筛查与个性化干预提供量化依据。",
]

CONTENT = [
    "1.需求分析",
    f"本课题属数据分析方向。面向基层医疗机构与健康管理人员，建设患者健康风险分析数据分析系统。系统以{TECH}为技术栈，完成临床指标接入、清洗入库、多维统计分析、机器学习建模与ECharts可视化展示，支撑健康风险筛查与慢病管理决策。",
    "2.研究内容",
    "（1）数据获取",
    f"数据来源于Kaggle公开数据集{DATA_NAME}，数据集网址：{DATA_URL}。本地主数据文件为synthetic_clinical_dataset.csv，共约10000条患者记录，字段覆盖年龄、性别、BMI、收缩压、舒张压、血糖、胆固醇、肌酐、糖尿病、高血压、诊断、30天再入院与死亡等，为后续分析提供输入。",
    "（2）数据处理",
    "采用Pandas读取与清洗数据：处理缺失值与异常指标；统一性别等类别字段；确定性派生smoking（是否吸烟）、drinking（是否饮酒）、exercise_freq（运动频率）及risk_level（低/中/高风险，综合诊断、死亡、再入院与慢病情况判定）等特征，保证统计与建模输入规范一致。",
    "（3）数据持久化",
    "将清洗后的明细与聚合结果写入MySQL，支持患者列表检索、分页查询与历史追溯，保障数据完整性与系统高效访问。",
    "（4）数据分析",
    "风险等级分布分析：使用Pandas的value_counts统计低/中/高风险人数与占比，揭示样本风险结构。",
    "年龄与BMI分布分析：按风险等级分组绘制散点分布，观察不同风险人群在年龄—BMI平面上的聚集特征。",
    "吸烟×饮酒交叉分析：使用crosstab统计不同生活方式组合人数，并计算各组高风险率，识别高危生活方式组合。",
    "血压与血糖相关性分析：计算收缩压/舒张压与血糖的相关系数，并结合散点分布评估代谢指标关联。",
    "疾病风险等级预测分析：采用scikit-learn的RandomForestClassifier建立随机森林多分类模型，以年龄、性别、BMI、收缩压、舒张压、血糖、胆固醇、吸烟、饮酒、运动频率等为特征，预测risk_level（低/中/高风险）；使用train_test_split划分训练集与测试集，GridSearchCV调参，并以accuracy_score、f1_score（加权）和roc_auc_score评估，输出混淆矩阵、ROC曲线与特征重要性。",
    "（5）数据可视化",
    "风险等级分布柱状图：使用ECharts的bar函数展示低/中/高风险人数与占比。",
    "年龄与BMI散点图：使用ECharts的scatter函数按风险等级着色展示分布。",
    "吸烟×饮酒交叉热力图：使用ECharts的heatmap函数展示不同生活方式组合的高风险率。",
    "血压与血糖相关性散点图：使用ECharts的scatter函数展示收缩压/舒张压与血糖关系。",
    "模型评估结果展示：使用ECharts绘制混淆矩阵热力图、高风险ROC曲线及特征重要性条形图，并在页面表单中输出预测风险等级及各类别概率。",
    "（6）系统测试",
    "采用黑盒测试验证数据导入、患者检索、统计分析、模型预测与图表展示等模块，确保输入输出符合预期、系统可演示可运行。",
]

METHOD = [
    "1.主要研究方法",
    f"本项目基于Flask框架构建患者健康风险分析数据分析系统，结合MySQL数据库进行数据存储与管理，并利用前端技术（HTML、CSS、JavaScript）和ECharts可视化库实现交互式展示。系统对Kaggle数据集{DATA_NAME}中约10000条患者记录进行多维分析：通过柱状图分析风险等级分布，通过散点图分析年龄与BMI关系，通过热力图分析吸烟×饮酒交叉高风险率，通过散点图分析血压与血糖相关性，并通过混淆矩阵、ROC曲线与特征重要性图展示模型评估结果。在预测模块中，采用scikit-learn库中的RandomForestClassifier随机森林多分类模型，输入包括年龄、性别、BMI、收缩压、舒张压、血糖、胆固醇、吸烟、饮酒、运动频率等特征，预测患者风险等级（低风险/中风险/高风险），并以准确率、加权F1值和AUC等指标评估效果，通过页面表单输出预测类别与概率。系统整合Pandas数据处理、MySQL持久化、Flask接口服务与ECharts可视化，为健康筛查与慢病管理提供数据支撑。",
    "2.通用研究方法",
    "（1）文献研究法",
    "系统梳理临床风险预测、慢病管理与机器学习分类应用相关文献，明确指标口径与评估方法，为系统功能划分与模型选择提供依据。",
    "（2）功能分析法",
    "按数据获取、数据处理、数据持久化、数据分析、数据可视化、系统测试拆分功能模块，明确Flask接口、MySQL表结构、ECharts图表与RandomForestClassifier模型之间的输入输出关系，保证流程可核查、界面可演示。",
    "3.技术路线",
    "本设计按“数据获取→数据处理→数据持久化→数据分析→数据可视化→系统测试”组织实现过程，技术路线如图1所示。",
    "（1）数据获取：从Kaggle下载synthetic_clinical_dataset.csv，校验年龄、BMI、血压、血糖、诊断及再入院/死亡等字段，确认约10000条记录。",
    "（2）数据处理：使用Pandas的read_csv读取数据，处理缺失与异常值，派生smoking、drinking、exercise_freq与risk_level标签。",
    "（3）数据持久化：采用PyMySQL连接MySQL，将清洗后的患者明细与统计结果写入数据库，支持分页检索。",
    "（4）数据分析：使用value_counts、crosstab、corr等完成4项统计对比；使用RandomForestClassifier、GridSearchCV、train_test_split完成风险等级三分类建模。",
    "（5）数据可视化：Flask提供风险分布、年龄BMI、吸烟饮酒交叉、血压血糖相关及模型评估等接口，前端ECharts绘制柱状图、散点图、热力图、混淆矩阵、ROC曲线与特征重要性图。",
    "（6）系统测试：对数据导入、检索接口、统计图表、模型预测与页面展示进行黑盒测试，验证输入输出符合预期。",
]

RESULTS = [
    "1.完成《基于临床指标数据的患者健康风险分析数据分析系统的设计与实现》毕业设计说明书（含技术路线图）。",
    "2.完成基于临床指标数据的患者健康风险分析数据分析系统开发文档与一个可运行演示系统。系统从Kaggle获取Synthetic Clinical Tabular Dataset数据集（synthetic_clinical_dataset.csv，约10000条患者记录），使用Pandas完成缺失值处理、生活方式特征派生与风险等级标签（低/中/高风险）生成，并通过MySQL实现数据持久化。系统基于Flask框架与Pandas，集成ECharts组件，实现柱状图（风险等级分布）、散点图（年龄与BMI按风险着色）、热力图（吸烟×饮酒高风险率交叉）、散点图（血压与血糖相关性）及混淆矩阵、ROC曲线、特征重要性图等可视化分析，直观展示年龄、BMI、血压、血糖与生活方式等因素与健康风险的关系。同时，借助scikit-learn构建RandomForestClassifier随机森林多分类模型，并结合GridSearchCV调参开展疾病风险等级预测，输入特征包括年龄、性别、BMI、收缩压、舒张压、血糖、胆固醇、吸烟、饮酒、运动频率等，输出低风险/中风险/高风险及各类别概率，并以准确率、加权F1值和AUC评估模型效果。用户可检索患者列表、查看统计图表并输入临床指标获取风险预测结果。系统解决临床指标分散难对比、风险等级难量化和缺少交互分析工具等问题，为健康筛查与慢病管理提供数据支撑。",
]

SCHEDULE = [
    "1.选题、下达任务书        年   月  日-     年    月   日",
    "2.开题报告、撰写初稿      年   月  日-     年    月   日",
    "3.中期检查                年   月  日-     年    月   日",
    "4.论文（设计）完成        年   月  日-     年    月   日",
    "5.答辩申请及资料准备      年   月  日-     年    月   日",
    "6.毕业答辩                年   月  日-     年    月   日",
]

TASK_BODY = [
    "一、毕业设计主要内容",
    "1.设计与构建系统的整体概念和工程背景。",
    "基于临床指标数据的患者健康风险分析数据分析系统是面向基层医疗、体检中心与健康管理场景的Web综合平台，整合数据处理、统计分析、机器学习预测、持久化与可视化功能，核心是将分散的临床指标记录转化为可检索、可对照的健康风险研判信息。工程背景上，年龄、BMI、血压、血糖、胆固醇及生活方式等因素共同影响患者健康风险，但指标分散、风险等级划分多依赖经验，单机表格难以支撑多维对比与量化建模。系统依托Kaggle公开合成临床表格数据集（约10000条患者记录），旨在解决临床指标难系统对比、健康风险影响因素不清晰、缺少可演示分析平台等痛点，契合计算机专业技术赋能健康管理的工程导向。",
    "2.系统应解决的问题和主要工程。",
    "系统需解决三大问题：临床指标难系统对比；健康风险影响因素不清晰；缺少集统计、预测与可视化于一体的分析入口。主要工程：预处理：用Pandas清洗数据、派生吸烟/饮酒/运动频率及低/中/高风险标签；持久化：设计MySQL表结构，通过PyMySQL存储；分析：运用Pandas完成风险分布、年龄BMI、吸烟饮酒交叉、血压血糖相关四项统计，并用RandomForestClassifier结合GridSearchCV开展疾病风险等级三分类；可视化与Web：用ECharts生成柱状图、散点图、热力图及混淆矩阵、ROC曲线、特征重要性图，基于Flask搭建界面；测试：黑盒测试。",
    "3.主要理论与技术方向。",
    f"主要理论：描述性统计与机器学习分类理论；主要技术：{TECH}。其中Pandas负责清洗与统计，MySQL负责持久化，Flask负责Web服务，ECharts负责图表展示，scikit-learn的RandomForestClassifier负责疾病风险等级预测。",
    "二、毕业设计要求",
    "1.符合计算机科学与技术专业相关规范，包含需求分析、系统设计、系统实现、系统测试，正确绘制相关图示；",
    "2.数据分析方向应涵盖机器学习或深度学习，对数据集进行有效的分析，并通过数据可视化将分析结果展示；",
    "3.数据真实可靠，不少于5000条，数据来源：",
    DATA_URL,
    "4.正文文字要求6000字以上；",
    "5.符合学校本科生毕业论文撰写规范要求；",
    "6.毕业论文（设计）中引用的文献应以近期（原则上为近5年的文献数一般不少于总数的三分之一）发表的与论文工作直接有关的文献为主。参考文献数量10-12篇，其中外文文献为1-2篇。",
    "三、要求成果形式",
    "1.完成《基于临床指标数据的患者健康风险分析数据分析系统的设计与实现》的论文。",
    "2.本项目设计并实现了患者健康风险分析数据分析系统，涵盖数据处理、持久化、统计分析、机器学习预测与可视化等模块。采用Pandas对原始数据进行清洗与特征派生，通过PyMySQL将结果存入MySQL数据库。在数据分析方面，利用统计方法分析风险等级分布、年龄与BMI关系、吸烟饮酒交叉高风险率及血压血糖相关性，并借助RandomForestClassifier结合GridSearchCV开展低/中/高风险等级预测。可视化部分使用ECharts生成交互式图表，包括柱状图、散点图、热力图及混淆矩阵、ROC曲线、特征重要性图等，展示临床指标与健康风险的关系及模型评估结果。系统基于Flask框架构建，支持患者检索与风险预测，为健康筛查与慢病管理提供数据支持。",
]


def write_status_with_cites(cell):
    clear_cell(cell)
    write_rich_para(cell, ["1. 国内研究现状"])
    write_rich_para(
        cell,
        [
            "国内在医疗健康数据与机器学习应用方面进展较快。相关研究将机器学习用于环境监测预警",
            1,
            "、工程材料性能评估",
            2,
            "、多算法融合优化",
            3,
            "、气象预报建模",
            4,
            "以及异常检测",
            5,
            "等场景；面向互联网医疗服务与能源管理，也有医生推荐度预测",
            6,
            "与负荷基线预测",
            7,
            "等实践；城市内涝模拟",
            8,
            "、轻工质量控制",
            9,
            "和系统优化综述",
            10,
            "进一步丰富了方法体系。健康管理与慢病筛查领域，已有工作关注指标监测与风险提示，但面向多维临床指标的系统清洗、多维可视化与疾病风险等级量化建模仍有提升空间。",
        ],
    )
    write_rich_para(cell, ["2. 国外研究现状"])
    write_rich_para(
        cell,
        [
            "国外研究更强调临床数据挖掘与预后/风险预测建模。机器学习在临床预后判别",
            11,
            "、辅助决策系统",
            12,
            "以及科学计算加速",
            13,
            "等方向的应用，验证了特征工程与集成学习在复杂分类任务中的有效性，可为患者健康风险等级预测与解释分析提供方法参考。",
        ],
    )
    write_rich_para(cell, ["3. 发展趋势"])
    write_rich_para(
        cell,
        [
            "健康数据分析正朝可视化交互、可解释建模与决策支持一体化发展。本课题以临床指标与疾病风险等级为主线，构建“清洗—入库—分析—可视化”系统，符合数据分析方向培养要求与基层健康管理数字化趋势。",
        ],
    )


def write_refs_with_bookmarks(cell):
    clear_cell(cell)
    for i, ref in enumerate(REFS, start=1):
        p = cell.add_paragraph()
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.left_indent = REF_LEFT_INDENT
        p.paragraph_format.first_line_indent = REF_FIRST_INDENT
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        add_text_run(p, ref, size=12)
        add_bookmark(p, f"ref{i}")


def write_purpose(cell):
    clear_cell(cell)
    for idx, text in enumerate(PURPOSE):
        p = new_para(cell, first_indent=True, line_spacing=1.5)
        add_text_run(p, text, size=12)
        if idx == 1:
            write_dataset_info(cell, first_indent=True)


def write_task_body(cell):
    clear_cell(cell)
    for text in TASK_BODY:
        add_text_run(new_para(cell, first_indent=True, line_spacing=1.5), text, size=12)


def write_method_with_roadmap(cell, roadmap_path: Path):
    clear_cell(cell)
    for text in METHOD:
        p = new_para(cell, first_indent=True, line_spacing=1.5)
        add_text_run(p, text, size=12)
        if text.startswith("本设计按“数据获取"):
            set_keep_with_next(p)
            insert_picture_in_cell(cell, roadmap_path, width_inch=4.6)


def fill_kaiti(doc: Document):
    make_roadmap_png(ROADMAP_PNG)
    t = doc.tables[0]
    write_plain(t.rows[3].cells[1], TOPIC, size=12)
    write_purpose(t.rows[8].cells[0])
    write_status_with_cites(t.rows[10].cells[0])
    write_refs_with_bookmarks(t.rows[12].cells[0])
    set_merged_plain(t.rows[14], CONTENT, first_indent=True, line_spacing=1.5)
    write_method_with_roadmap(t.rows[16].cells[0], ROADMAP_PNG)
    set_merged_plain(t.rows[18], RESULTS, first_indent=True, line_spacing=1.5)
    set_merged_plain(t.rows[20], SCHEDULE, first_indent=True, line_spacing=1.5)


def fill_renwushu(doc: Document):
    t = doc.tables[0]
    write_plain(t.rows[3].cells[1], TOPIC, size=12)
    write_task_body(t.rows[8].cells[0])


def save_as(doc: Document, out: Path):
    tmp = out.with_suffix(".tmp.docx")
    if tmp.exists():
        tmp.unlink()
    doc.save(str(tmp))
    if out.exists():
        try:
            out.unlink()
        except PermissionError:
            alt = out.with_name(out.stem + "_新" + out.suffix)
            tmp.replace(alt)
            strip_docx_comments(alt)
            print("LOCKED, saved as", alt)
            return alt
    tmp.replace(out)
    strip_docx_comments(out)
    return out


def main():
    PROJ.mkdir(parents=True, exist_ok=True)
    kt = Document(str(SRC_KT))
    fill_kaiti(kt)
    p1 = save_as(kt, OUT_KT)

    rw = Document(str(SRC_RW))
    fill_renwushu(rw)
    p2 = save_as(rw, OUT_RW)

    for p in (p1, p2):
        text = "\n".join(c.text for t in Document(str(p)).tables for r in t.rows for c in r.cells[:1])
        bad = []
        if "按大数据技术方向" in text or "按数据分析方向：" in text:
            bad.append("模板提示语")
        if "synthetic-clinical" not in text and "kaggle.com" not in text.lower():
            if "开题" in p.name or "任务书" in p.name:
                bad.append("缺Kaggle")
        if "数据持久化" not in text and "开题" in p.name:
            bad.append("缺数据持久化")
        if "二、毕业设计要求" not in text and "任务书" in p.name:
            bad.append("任务书结构")
        if "毕业设计说明书" in text:
            bad.append("应写论文")
        if "随机森林" not in text and "开题" in p.name:
            bad.append("缺模型")
        print(p.name, "BAD=" + ",".join(bad) if bad else "CHECK_OK")


if __name__ == "__main__":
    main()
