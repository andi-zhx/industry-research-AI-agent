# agent_system/postprocess/planner_parser.py
# Planner Parser 的职责：
# 把 Planner 的自然语言输出 → 稳定结构化
# 为后续 Agent 提供硬约束输入
# 在早期就发现“这份规划不可执行”并直接报错

# agent_system/postprocess/planner_parser.py
import re
from typing import List, Dict

def parse_planner_output(text: str) -> Dict:
    """
    将 Planner 的自然语言研究蓝图解析为稳定结构。
    【核心改进】：大幅增加容错性，关键字段匹配失败时使用默认值，不再抛出异常中断流程。
    """
    if not text:
        text = ""

    # 初始化默认结构
    result = {
        "raw_text": text,
        "total_word_target": 10000, # 默认值，防止报错
        "chapters": [],
        "tables": [],
        "parallel_chapters": [],
        "data_dependent_chapters": []
    }

    # =========================================================
    # 1️⃣ 提取「预期总字数」 (增加容错)
    # =========================================================
    # 匹配模式：允许 "预期总字数" 后有空格、冒号、中文冒号、甚至 "约" 字
    # 示例匹配： "预期总字数：12,000" / "**预期总字数**: 约 10000" / "预计字数：1万"
    total_word_match = re.search(r"(预期总字数|预计字数|总字数).*?[:：].*?(\d[\d,]*)", text)
    if total_word_match:
        try:
            num_str = total_word_match.group(2).replace(",", "")
            result["total_word_target"] = int(num_str)
        except:
            pass # 解析失败就用默认值 10000

    # =========================================================
    # 2️⃣ 按章节拆分（增强版正则）
    # =========================================================
    # 尝试多种分割模式
    # 模式 A: ## 第1章 (Markdown 标准)
    chapter_blocks = re.split(r"\n#+\s*第\d+章", text)
    
    # 如果分割失败（只有一段），尝试 模式 B: 第1章 (没有#号)
    if len(chapter_blocks) <= 1:
        chapter_blocks = re.split(r"\n\s*第\d+章", text)

    # 第一个 block 通常是“一、报告总体规划”等前置信息，跳过
    for block in chapter_blocks[1:]:
        if len(block.strip()) < 10: continue # 跳过过短的碎片
        try:
            chapter = _parse_single_chapter(block)
            result["chapters"].append(chapter)
            result["tables"].extend(chapter["tables"])
        except Exception as e:
            print(f"⚠️ [Parser Warning] 跳过一个无法解析的章节块: {str(e)}")
            continue

    # 保底：如果真的一个章节都没解出来（非常罕见），手动造一个默认章节，防止下游 crash
    if not result["chapters"]:
        result["chapters"].append({
            "title": "综合分析",
            "word_target": 2000,
            "research_questions": ["行业现状分析"],
            "data_sources": "公开网络数据",
            "tables": []
        })

    # =========================================================
    # 3️⃣ 提取并行/依赖信息 (弱约束，找不到就空着)
    # =========================================================
    try:
        parallel_match = re.search(r"并行写作章节.*?[:：]\s*(.*)", text, re.DOTALL)
        if parallel_match:
            # 取第一行，防止匹配到后面太多内容
            line = parallel_match.group(1).split('\n')[0]
            result["parallel_chapters"] = _split_list(line)

        data_dep_match = re.search(r"强依赖数据的章节.*?[:：]\s*(.*)", text, re.DOTALL)
        if data_dep_match:
            line = data_dep_match.group(1).split('\n')[0]
            result["data_dependent_chapters"] = _split_list(line)
    except:
        pass

    return result


# =========================================================
# 🔧 辅助函数
# =========================================================

def _parse_single_chapter(block: str) -> Dict:
    """
    解析单一章节内容 (宽容模式)
    """
    chapter = {
        "title": "未命名章节",
        "word_target": 1500,
        "research_questions": [],
        "data_sources": "",
        "tables": []
    }

    # 1. 章节标题
    # 取第一行非空文本作为标题
    lines = [l.strip() for l in block.strip().split('\n') if l.strip()]
    if lines:
        # 去掉可能的冒号或多余符号
        raw_title = lines[0].lstrip("：:").strip()
        # 有时候标题会带 "1. 行业概况"，去掉前面的数字
        chapter["title"] = re.sub(r"^[\d\.]+\s*", "", raw_title)

    # 2. 目标字数
    word_match = re.search(r"(目标字数|字数).*?[:：].*?(\d[\d,]*)", block)
    if word_match:
        try:
            chapter["word_target"] = int(word_match.group(2).replace(",", ""))
        except:
            pass

    # 3. 关键研究问题
    rq_match = re.search(
        r"关键研究问题.*?[:：](.*?)(数据与信息来源指引|表格规划|#|$)",
        block,
        re.DOTALL
    )
    if rq_match:
        chapter["research_questions"] = _split_list(rq_match.group(1))

    # 4. 数据来源
    ds_match = re.search(
        r"数据与信息来源指引.*?[:：](.*?)(表格规划|#|$)",
        block,
        re.DOTALL
    )
    if ds_match:
        chapter["data_sources"] = ds_match.group(1).strip()

    # 5. 表格规划 (最容易出错的地方，加重容错)
    # 匹配 "表 1-1" 或 "表格 1" 开头的段落
    table_blocks = re.findall(
        r"(表\s*[\d\-\.]+|表格\s*[\d\-\.]+).*?[:：](.*?)(?=表\s*[\d\-\.]+|表格\s*[\d\-\.]+|#|$)",
        block,
        re.DOTALL
    )

    for header, content in table_blocks:
        try:
            parsed_table = _parse_table(content)
            # 把表号拼进去方便阅读
            parsed_table["name"] = f"{header} {parsed_table['name']}"
            chapter["tables"].append(parsed_table)
        except:
            continue

    # 【重要】不再因为没有表格而报错
    
    return chapter


def _parse_table(text: str) -> Dict:
    """
    解析单个表格定义
    """
    table = {
        "name": "数据表",
        "purpose": "展示数据",
        "fields": []
    }

    # 提取名称
    name_match = re.search(r"表格名称.*?[:：](.*)", text)
    if name_match:
        table["name"] = name_match.group(1).strip()

    # 提取用途
    purpose_match = re.search(r"用途.*?[:：](.*)", text)
    if purpose_match:
        table["purpose"] = purpose_match.group(1).strip()

    # 提取字段
    fields_match = re.search(r"(核心字段|列名).*?[:：](.*)", text)
    if fields_match:
        table["fields"] = _split_list(fields_match.group(1))

    # 只要有字段就算成功，名称稍微宽容点
    if not table["fields"]:
        # 尝试看看有没有 markdown list
        potential_fields = _split_list(text)
        # 如果列表中包含 "同比" "占比" 等词，大概率是字段
        if len(potential_fields) >= 1:
             table["fields"] = potential_fields

    return table


def _split_list(text: str) -> List[str]:
    """
    将 - / 数字列表 / 换行 统一拆成 list
    """
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # 去掉行首的 "1.", "-", "*", "•" 等符号
        line = re.sub(r"^[\-\*\•\d\.\、]+", "", line).strip()
        if line:
            items.append(line)
    return items

