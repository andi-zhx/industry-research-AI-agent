# agent_system/postprocess/base_parser.py
import re
from typing import Dict

def split_sections(text: str) -> Dict[str, str]:
    """
    通用结构块切分器：
    【标题】 -> 内容
    """
    pattern = r"【(.+?)】"
    matches = list(re.finditer(pattern, text))

    sections = {}
    for i, m in enumerate(matches):
        title = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[title] = text[start:end].strip()

    return sections
