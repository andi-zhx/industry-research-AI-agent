# agent_system/schemas/research_input.py
"""
行业研究输入模式定义
支持六大研究维度配置
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ResearchDimension(str, Enum):
    """六大研究维度枚举"""
    INDUSTRY_DEFINITION = "行业定义与边界"
    MARKET_SIZE = "市场规模与趋势"
    SUPPLY_CHAIN = "产业链结构"
    COMPETITIVE_LANDSCAPE = "典型玩家与格局"
    BUSINESS_MODEL = "商业模式与变现"
    POLICY_TECH_ENV = "政策/科技/环境影响"


class ReportDepth(str, Enum):
    """报告深度枚举"""
    QUICK = "快速报告"  # 约5000字
    STANDARD = "标准报告"  # 约10000字
    DEEP = "深度报告"  # 约15000字以上


class InvestorType(str, Enum):
    """投资者类型枚举"""
    VC = "VC风险投资"
    PE = "PE私募股权"
    INDUSTRIAL = "产业资本"
    GOVERNMENT = "政府引导基金"
    FAMILY_OFFICE = "家族办公室"


class IndustryResearchInput(BaseModel):
    """
    行业研究输入参数模型
    """
    
    # 基础参数（保持向后兼容）
    industry: str = Field(
        ..., 
        description="研究行业名称，如'半导体'、'新能源汽车'、'人工智能'"
    )
    province: str = Field(
        ..., 
        description="研究省份/区域，如'浙江省'、'上海市'、'全国'"
    )
    target_year: int = Field(
        default=2025, 
        description="目标研究年份"
    )
    focus: str = Field(
        default="产业链深度分析与投资机会识别", 
        description="研究侧重点"
    )
    
    # 原有可选项（保持兼容）
    depth: Optional[str] = Field(
        default="深度",
        description="报告深度（兼容旧版本）"
    )
    
    # 高级参数（新增）
    report_depth: Optional[ReportDepth] = Field(
        default=ReportDepth.DEEP,
        description="报告深度级别"
    )
    investor_type: Optional[InvestorType] = Field(
        default=InvestorType.PE,
        description="目标投资者类型"
    )
    
    # 研究维度配置（新增）
    dimensions: Optional[List[ResearchDimension]] = Field(
        default=None,
        description="需要覆盖的研究维度，默认覆盖全部六大维度"
    )
    
    # 产业链重点配置（新增）
    supply_chain_focus: bool = Field(
        default=True,
        description="是否重点分析产业链"
    )
    supply_chain_depth: str = Field(
        default="deep",
        description="产业链分析深度：quick/standard/deep"
    )
    
    # 企业分析配置（新增）
    min_companies: int = Field(
        default=5,
        description="最少分析企业数量"
    )
    include_unlisted: bool = Field(
        default=True,
        description="是否包含非上市企业"
    )
    
    # 输出配置（新增）
    include_tables: bool = Field(
        default=True,
        description="是否包含数据表格"
    )
    min_tables: int = Field(
        default=8,
        description="最少表格数量"
    )
    include_charts_suggestion: bool = Field(
        default=True,
        description="是否包含图表建议"
    )
    
    # 知识库配置（新增）
    use_local_kb: bool = Field(
        default=True,
        description="是否使用本地知识库"
    )
    use_memory: bool = Field(
        default=True,
        description="是否使用历史记忆"
    )
    
    def get_dimensions(self) -> List[ResearchDimension]:
        """获取研究维度列表"""
        if self.dimensions:
            return self.dimensions
        return [
            ResearchDimension.INDUSTRY_DEFINITION,
            ResearchDimension.MARKET_SIZE,
            ResearchDimension.SUPPLY_CHAIN,
            ResearchDimension.COMPETITIVE_LANDSCAPE,
            ResearchDimension.BUSINESS_MODEL,
            ResearchDimension.POLICY_TECH_ENV
        ]
    
    class Config:
        use_enum_values = True


class QuickResearchInput(BaseModel):
    """
    快速研究输入（简化版）
    """
    industry: str = Field(..., description="研究行业")
    province: str = Field(default="全国", description="研究区域")
    focus: str = Field(default="产业链分析", description="研究重点")
    
    def to_full_input(self) -> IndustryResearchInput:
        """转换为完整输入"""
        return IndustryResearchInput(
            industry=self.industry,
            province=self.province,
            focus=self.focus,
            report_depth=ReportDepth.QUICK
        )


class SupplyChainResearchInput(BaseModel):
    """
    产业链专项研究输入
    """
    industry: str = Field(..., description="研究行业")
    province: str = Field(default="全国", description="研究区域")
    target_year: int = Field(default=2025, description="目标年份")
    
    # 产业链层级
    upstream_focus: List[str] = Field(
        default=[],
        description="上游重点关注环节"
    )
    midstream_focus: List[str] = Field(
        default=[],
        description="中游重点关注环节"
    )
    downstream_focus: List[str] = Field(
        default=[],
        description="下游重点关注环节"
    )
    
    # 分析深度
    include_value_chain: bool = Field(
        default=True,
        description="是否包含价值链分析"
    )
    include_risk_analysis: bool = Field(
        default=True,
        description="是否包含风险分析"
    )
    include_investment_opportunity: bool = Field(
        default=True,
        description="是否包含投资机会分析"
    )
