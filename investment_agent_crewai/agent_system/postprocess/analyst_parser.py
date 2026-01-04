# agent_system/postprocess/analyst_parser.py

from .base_parser import split_sections

REQUIRED_SECTIONS = [
    "投资逻辑总结",
    "关键对比与产业链缺口",
    "可制表的数据结构建议",
    "关键风险与不确定性"
]


def parse_analyst_output(text: str) -> dict:
    """
    Analyst 输出解析（Prompt v2 对齐版）
    """
    sections = split_sections(text)

    for section in REQUIRED_SECTIONS:
        if section not in sections:
            sections[section] = "（分析师未显式输出该区块，需人工复核或后续补充）"

    return sections
