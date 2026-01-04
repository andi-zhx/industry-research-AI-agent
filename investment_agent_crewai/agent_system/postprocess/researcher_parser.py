# agent_system/postprocess/researcher_parser.py

import re
from typing import Optional, Dict


def extract_block(text: str, block_name: str) -> Optional[str]:
    """
    从【区块名】中提取内容（宽松匹配）
    """
    pattern = rf"【{block_name}】([\s\S]*?)(?=\n【|\Z)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return None


def parse_researcher_output(raw_text: str) -> Dict:
    """
    Researcher 输出解析（容错 + 稳定版）

    目标：
    - 不因区块缺失报错
    - 尽可能提取结构化信息
    """

    core_conclusion = extract_block(raw_text, "核心结论")

    facts_block = (
        extract_block(raw_text, "事实与数据支持")
        or extract_block(raw_text, "关键数据")
        or extract_block(raw_text, "数据要点")
    )

    impact_block = extract_block(raw_text, "对投资判断的影响")

    return {
        "raw_text": raw_text,

        # 允许为空，由 Analyst 统一提炼
        "core_conclusion": core_conclusion or "（Researcher 未显式给出核心结论）",

        # Researcher 最重要的产出：事实
        "facts_and_data": facts_block or "（未提取到结构化数据区块，需人工复核）",

        # 可选字段，供 Analyst / Writer 使用
        "investment_impact_hint": impact_block or ""
    }
