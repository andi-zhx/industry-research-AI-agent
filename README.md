# FinSight AI Agent - 行业研究智能体

> 基于多智能体协作的专业行业研究工具，覆盖六大研究维度，重点关注产业链深度分析

## 项目简介

FinSight AI Agent 是一个面向私募股权基金投资人的智能行业研究工具。通过多智能体协作（Multi-Agent Collaboration）架构，自动生成专业级的行业深度研究报告。

### 核心特性

- **六大研究维度**：覆盖行业定义、市场规模、产业链结构、竞争格局、商业模式、政策环境
- **产业链深度分析**：重点梳理上中下游产业链结构，识别各环节投资机会
- **多智能体协作**：Planner、Researcher、Analyst、Writer、Reviewer 五大智能体协同工作
- **知识库增强**：支持本地研报PDF向量化存储与检索（RAG）
- **专业报告输出**：生成15000字以上的深度研究报告，包含数据表格和投资建议

## 六大研究维度

| 维度 | 核心问题 | 常见工具 |
|------|----------|----------|
| ① 行业定义与边界 | 这行业到底包含什么？不包含什么？ | 行业协会定义/NAICS代码 |
| ② 市场规模与趋势 | 现在多大？未来增长吗？为什么？ | 中商/艾瑞/头豹等报告 |
| ③ 产业链结构 | 谁是上游、中游、下游？谁赚钱？ | 产业链图谱/案例图解 |
| ④ 典型玩家与格局 | 龙头是谁？市占率如何？ | 企业官网/招股书/行研报告 |
| ⑤ 商业模式与变现 | 谁付钱？怎么收费？毛利高吗？ | BM Canvas/收入结构表 |
| ⑥ 政策/科技/环境 | 哪些政策在左右它？新科技有冲击吗？ | 政策汇总/技术趋势分析 |

## 产业链分析框架

```
🔼 上游（原材料/零部件）
    ├── 原材料供应商
    ├── 核心零部件供应商
    ├── 设备供应商
    └── 成本占比与国产化率

⏺️ 中游（制造/加工）
    ├── 核心制造环节
    ├── 技术壁垒分析
    ├── 产能分布
    └── 竞争格局

🔽 下游（应用/终端）
    ├── 终端应用场景
    ├── 市场规模与增速
    ├── 需求驱动因素
    └── 客户结构分析

💰 价值链分析
    ├── 利润在各环节的分配
    ├── 议价能力分析
    └── 投资机会识别
```

## 快速开始

### 环境要求

- Python 3.10+
- OpenAI API Key 或兼容的 LLM API

### 安装依赖

```bash
cd investment_agent_crewai
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 或其他兼容API
SERPER_API_KEY=your_serper_key_here  # 用于网络搜索
```

### 启动应用

```bash
streamlit run app.py
```

## 项目结构

```
investment_agent_crewai/
├── app.py                      # Streamlit 前端入口
├── main.py                     # 后端入口（Facade）
├── app_config.py               # 配置文件（产业链树、省份列表等）
├── ui_styles.py                # UI样式模块
├── requirements.txt            # 依赖列表
│
├── agent_system/               # 智能体系统
│   ├── workflows/              # 工作流定义
│   │   └── industry_research.py  # 行业研究工作流
│   │
│   ├── prompts/                # 提示词模块
│   │   ├── planner_prompt.py   # 规划师提示词
│   │   ├── researcher_prompt.py # 研究员提示词
│   │   ├── analyst_prompt.py   # 分析师提示词
│   │   ├── writer_prompt.py    # 撰写员提示词
│   │   ├── reviewer_prompt.py  # 审核员提示词
│   │   └── supply_chain_prompt.py # 产业链分析提示词
│   │
│   ├── tools/                  # 工具模块
│   │   └── tools_custom.py     # 自定义工具（搜索、财务分析等）
│   │
│   ├── schemas/                # 数据模式
│   │   └── research_input.py   # 研究输入参数模式
│   │
│   ├── knowledge/              # 知识库模块
│   │   └── knowledge_engine.py # RAG知识库引擎
│   │
│   └── postprocess/            # 后处理模块
│       └── planner_parser.py   # 规划解析器
│
├── memory_system/              # 记忆系统
│   └── memory_manager.py       # 记忆管理器
│
├── config/                     # 配置模块
│   ├── llm.py                  # LLM配置
│   ├── network.py              # 网络配置
│   └── runtime_env.py          # 运行时环境配置
│
├── knowledge_base/             # 知识库存储目录
│
└── output/                     # 报告输出目录
```

## 智能体架构

### 五大智能体

1. **Planner（规划师）**
   - 基于六大研究维度制定研究蓝图
   - 识别关键研究问题和数据需求

2. **Researcher（研究员）**
   - 多源数据采集（网络搜索、知识库、财务数据）
   - 产业链信息搜集

3. **Analyst（分析师）**
   - 六维度综合分析
   - 产业链价值分析
   - 投资机会识别

4. **Writer（撰写员）**
   - 专业报告撰写
   - 产业链图谱描述
   - 数据表格生成

5. **Reviewer（审核员）**
   - 报告质量审核
   - 数据一致性检查
   - 投资逻辑验证

### 工具集

| 工具名称 | 功能描述 |
|----------|----------|
| SerperDevTool | 网络搜索 |
| SupplyChainSearchTool | 产业链专项搜索 |
| PolicySearchTool | 政策信息搜索 |
| MarketSizeSearchTool | 市场规模搜索 |
| CompanySearchTool | 企业信息搜索 |
| BusinessModelSearchTool | 商业模式搜索 |
| StockAnalysisTool | 股票财务分析 |
| RAGSearchTool | 本地知识库检索 |
| PDFReadTool | PDF文档读取 |
| FinancialCalculatorTool | 财务计算（IRR/NPV等） |

## 报告输出示例

生成的报告包含以下章节：

1. **执行摘要**
2. **行业定义与边界**
3. **市场规模与趋势**
4. **产业链深度分析**
   - 上游分析
   - 中游分析
   - 下游分析
   - 价值链分析
5. **竞争格局分析**
6. **商业模式分析**
7. **政策与技术环境**
8. **投资建议与风险提示**
9. **附录：数据来源与免责声明**

## 版本更新

### v2.0（当前版本）

- 新增六大研究维度框架
- 强化产业链深度分析能力
- 新增产业链专项分析模块
- 优化前端界面和用户体验
- 增加多个专项搜索工具
- 提升报告质量和专业度

### v1.0

- 基础行业研究功能
- 多智能体协作框架
- 知识库RAG支持

## 许可证

本项目仅供内部使用，禁止外传。

## 联系方式

如有问题，请联系项目维护者。
