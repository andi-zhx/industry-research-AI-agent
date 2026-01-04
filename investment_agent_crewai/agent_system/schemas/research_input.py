# agent_system/schemas/research_input.py

from typing import Optional
from pydantic import BaseModel

class IndustryResearchInput(BaseModel):
    industry: str
    target_year: int
    focus: str
    province: str

    # 可选项（为未来扩展准备）
    depth: Optional[str] = "深度"
