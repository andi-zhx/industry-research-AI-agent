# agent_system/workflows/industry_research.py
"""
行业研究主工作流（增强版）
支持六大研究维度，重点强化产业链分析

工作流程：
Phase 0: 定义 Agents
Phase 1: Planner（规划）- 基于六大维度设计研究蓝图
Phase 2: Researcher（并行研究）- 财务/政策/行业/产业链/商业模式
Phase 3: Analyst（综合分析）- 六维度综合分析
Phase 4: Writer（分章节并行写作）
Phase 5: Reviewer（终审）
"""

import os
import datetime
from typing import Dict, Any, List

from crewai import Agent, Task, Crew, Process

from config.runtime_env import setup_runtime_env
from config.network import setup_network
from config.llm import get_deepseek_llm

from agent_system.schemas.research_input import IndustryResearchInput

# ===== Prompts =====
from agent_system.prompts.planner_prompt import PLANNER_PROMPT
from agent_system.prompts.researcher_prompt import (
    RESEARCHER_FINANCE_PROMPT,
    RESEARCHER_POLICY_PROMPT,
    RESEARCHER_INDUSTRY_PROMPT,
    RESEARCHER_SUPPLY_CHAIN_PROMPT,
    RESEARCHER_BUSINESS_MODEL_PROMPT
)
from agent_system.prompts.analyst_prompt import ANALYST_PROMPT, SUPPLY_CHAIN_ANALYST_PROMPT
from agent_system.prompts.writer_prompt import (
    WRITER_PROMPT, 
    SUPPLY_CHAIN_WRITER_PROMPT,
    EXECUTIVE_SUMMARY_WRITER_PROMPT
)
from agent_system.prompts.reviewer_prompt import REVIEWER_PROMPT

# ===== Parsers =====
from agent_system.postprocess.planner_parser import parse_planner_output
from agent_system.postprocess.researcher_parser import parse_researcher_output
from agent_system.postprocess.analyst_parser import parse_analyst_output

# ===== Tools =====
from agent_system.tools.tools_custom import (
    stock_analysis,
    read_pdf,
    serper_tool,
    rag_tool,
    recall_tool
)

from memory_system.memory_manager import memory_manager

# ============================================================
# 初始化运行环境（只执行一次）
# ============================================================
setup_runtime_env()
setup_network()
llm = get_deepseek_llm()

# ============================================================
# 主入口
# ============================================================
def run_industry_research(inputs: Dict | IndustryResearchInput) -> str:
    """
    行业深度研究主函数
    
    Args:
        inputs: 研究输入参数，包含 industry, province, target_year, focus
    
    Returns:
        str: 生成的研究报告内容
    """
    
    # ---------- 输入校验 ----------
    if isinstance(inputs, dict):
        inputs = IndustryResearchInput(**inputs)

    prompt_vars = inputs.model_dump()
    
    print(f"🚀 开始行业研究：{inputs.industry} | {inputs.province} | {inputs.target_year}")
    print(f"📋 研究侧重点：{inputs.focus}")

    # ============================================================
    # Phase 0: 定义 Agents
    # ============================================================
    
    # 规划师 Agent
    planner = Agent(
        role="Lead Research Planner",
        goal="基于六大研究维度，制定行业研究的完整逻辑框架与关键问题清单",
        backstory=(
            "你是一名一级市场投研总监，擅长从投资视角拆解行业。"
            "你的大纲必须服务于投资决策，而不是科普。"
            "你特别擅长产业链分析，能够清晰梳理上中下游结构。"
            "你熟悉六大研究维度：行业定义、市场规模、产业链结构、竞争格局、商业模式、政策环境。"
        ),
        llm=llm,
        verbose=True
    )

    # 研究员 Agent（通用）
    researcher = Agent(
        role="Senior Industry Data Researcher",
        goal="搜集关键年份的财务、政策、产业链与商业模式数据",
        backstory=(
            "你是一名高效研究员，只关心可验证的数据、数字与结论。"
            "避免长篇描述，优先结构化信息。"
            "你特别擅长产业链数据搜集，能够清晰区分上游、中游、下游。"
            "关键原则："
            "1. 抓大放小：重点找龙头的营收/净利/市值，以及核心政策KPI。"
            "2. 产业链视角：必须按上游/中游/下游分类整理数据。"
            "3. 拒绝冗余：不需要搜集过于细枝末节的技术参数，关注商业落地的核心指标。"
            "4. 拥有读取本地知识库的能力，只提取最关键的结论。"
        ),
        tools=[stock_analysis, serper_tool, read_pdf, rag_tool, recall_tool],
        llm=llm,
        verbose=True
    )
    
    # 产业链专项研究员 Agent
    supply_chain_researcher = Agent(
        role="Supply Chain Research Specialist",
        goal="深度梳理产业链上下游结构，识别各环节投资机会",
        backstory=(
            "你是一名产业链研究专家，专注于产业链深度分析。"
            "你能够清晰识别上游原材料、中游制造、下游应用各环节。"
            "你特别关注产业链价值分配、议价能力、投资机会。"
            "你熟悉各行业的产业链图谱，能够快速定位关键环节。"
        ),
        tools=[stock_analysis, serper_tool, read_pdf, rag_tool, recall_tool],
        llm=llm,
        verbose=True,
        max_iter=5,
        max_execution_time=2400
    )
    
    # 分析师 Agent
    analyst = Agent(
        role="Senior Investment Analyst",
        goal="基于六大研究维度，从数据中提炼核心投资结论",
        backstory=(
            "你是一名资深一级市场投资分析师。"
            "你关注比较、差异、趋势与产业链缺口。"
            "你特别擅长从产业链视角分析投资机会。"
            "你能够整合六大维度数据，形成投资决策建议。"
        ),
        tools=[rag_tool, recall_tool],
        llm=llm,
        verbose=True,
        max_iter=5,
        max_execution_time=2400
    )

    # 写作者 Agent
    writer = Agent(
        role="Professional Report Writer",
        goal="撰写专业、结构清晰的行业研究报告",
        backstory=(
            "你遵循：结论先行、段落自洽、表格辅助。"
            "你特别擅长产业链分析的写作，能够清晰呈现上中下游结构。"
            "拒绝空话与堆砌。"
            "时效性强：报告第一行注明日期。"
        ),
        llm=llm,
        verbose=True
    )

    # 审核员 Agent
    reviewer = Agent(
        role="Quality Assurance Reviewer",
        goal="确保逻辑一致性、数据完整性与产业链分析深度",
        backstory=(
            "你只做必要检查，不重写内容。"
            "你特别关注产业链分析是否完整、各环节是否覆盖。"
        ),
        llm=llm,
        verbose=True
    )

    # ============================================================
    # Phase 1: Planner（规划）
    # ============================================================
    print("\n📋 Phase 1: 规划研究蓝图...")
    
    plan_task = Task(
        description=PLANNER_PROMPT.format(**prompt_vars),
        expected_output="一份包含六大研究维度、三级目录、预设图表位置的详细大纲，产业链分析作为重点章节。",
        agent=planner
    )

    plan_crew = Crew(
        agents=[planner],
        tasks=[plan_task],
        process=Process.sequential,
        verbose=True
    )

    plan_raw = plan_crew.kickoff()
    plan_struct = parse_planner_output(str(plan_raw))
    
    print(f"✅ 规划完成，共 {len(plan_struct['chapters'])} 个章节")

    # ============================================================
    # Phase 2: Researcher（并行研究）- 增强版
    # ============================================================
    print("\n🔍 Phase 2: 数据研究（五维度并行）...")
    
    # 1. 财务数据研究任务
    finance_task = Task(
        description=RESEARCHER_FINANCE_PROMPT.format(**prompt_vars),
        agent=researcher,
        expected_output="一份包含5-8家龙头企业财务指标的原始财务数据列表，按产业链环节分类",
        async_execution=True
    )
    
    # 2. 政策研究任务
    policy_task = Task(
        description=RESEARCHER_POLICY_PROMPT.format(**prompt_vars),
        agent=researcher,
        expected_output="一份包含国家和省级政策的汇总表，标注对产业链各环节的影响",
        async_execution=True
    )
    
    # 3. 行业规模研究任务
    industry_task = Task(
        description=RESEARCHER_INDUSTRY_PROMPT.format(**prompt_vars),
        agent=researcher,
        expected_output="一份包含行业规模、增速、竞争格局的数据汇总",
        async_execution=True
    )
    
    # 4. 产业链专项研究任务（新增核心任务）
    supply_chain_task = Task(
        description=RESEARCHER_SUPPLY_CHAIN_PROMPT.format(**prompt_vars),
        agent=supply_chain_researcher,
        expected_output="一份完整的产业链深度分析报告，包含上游/中游/下游各环节详细数据",
        async_execution=True
    )
    
    # 5. 商业模式研究任务（新增）
    business_model_task = Task(
        description=RESEARCHER_BUSINESS_MODEL_PROMPT.format(**prompt_vars),
        agent=researcher,
        expected_output="一份包含收入结构、成本结构、盈利能力的商业模式分析",
        async_execution=True
    )

    # 汇总任务
    summary_task = Task(
        description="""
        作为首席研究员，汇总上述【财务】、【政策】、【行业】、【产业链】、【商业模式】五个维度的搜集结果。
        
        请将散落在各处的关键数据整理成一份结构化的"行业数据摘要"，去除重复信息，供分析师使用。
        
        特别注意：
        1. 产业链数据必须清晰区分上游、中游、下游
        2. 必须保留各环节的关键企业和财务数据
        3. 必须标注数据来源
        """,
        agent=researcher,
        expected_output="一份包含财务、政策、行业、产业链、商业模式五方面关键数据的完整调研纪要。",
        context=[finance_task, policy_task, industry_task, supply_chain_task, business_model_task],
        async_execution=False
    )

    research_crew = Crew(
        agents=[researcher, supply_chain_researcher],
        tasks=[finance_task, policy_task, industry_task, supply_chain_task, business_model_task, summary_task],
        process=Process.sequential,
        verbose=True
    )
    
    research_result = research_crew.kickoff()
    research_structs = [parse_researcher_output(str(research_result))]

    # 存入长期记忆
    memory_manager.save_insight(
        content=str(research_result),
        category="fact",
        metadata={
            "industry": inputs.industry,
            "province": inputs.province,
            "year": str(inputs.target_year),
            "source_agent": "Researcher",
            "dimensions": "finance,policy,industry,supply_chain,business_model"
        }
    )
    
    print("✅ 数据研究完成")

    # ============================================================
    # Phase 3: Analyst（综合分析）- 增强版
    # ============================================================
    print("\n📊 Phase 3: 综合分析...")
    
    analyst_task = Task(
        description=ANALYST_PROMPT.format(
            industry=inputs.industry,
            target_year=inputs.target_year,
            focus=inputs.focus,
            province=inputs.province,
            research_summary=research_structs
        ),
        expected_output="一份包含六维度综合分析、产业链投资机会矩阵、结构化对比数据的中间分析稿。",
        agent=analyst
    )

    analyst_crew = Crew(
        agents=[analyst],
        tasks=[analyst_task],
        process=Process.sequential,
        verbose=True
    )

    analysis_raw = analyst_crew.kickoff()
    analysis_struct = parse_analyst_output(str(analysis_raw))

    # 存入记忆
    memory_manager.save_insight(
        content=str(analysis_raw),
        category="conclusion",
        metadata={
            "industry": inputs.industry,
            "province": inputs.province,
            "year": str(inputs.target_year),
            "source_agent": "Analyst"
        }
    )
    
    print("✅ 综合分析完成")

    # ============================================================
    # Phase 4: Writer（分章节并行写作）- 增强版
    # ============================================================
    print("\n✍️ Phase 4: 报告撰写...")
    
    chapter_tasks = []
    
    for chapter in plan_struct["chapters"]:
        # 判断是否为产业链章节，使用专门的提示词
        chapter_title = chapter.get('title', '')
        
        if '产业链' in chapter_title:
            # 产业链专项章节
            task_prompt = SUPPLY_CHAIN_WRITER_PROMPT.format(
                industry=inputs.industry,
                target_year=inputs.target_year,
                province=inputs.province,
                supply_chain_data=str(research_structs),
                analysis_summary=analysis_struct
            )
        elif '摘要' in chapter_title or '要点' in chapter_title:
            # 执行摘要章节
            task_prompt = EXECUTIVE_SUMMARY_WRITER_PROMPT.format(
                industry=inputs.industry,
                target_year=inputs.target_year,
                focus=inputs.focus,
                province=inputs.province,
                analysis_summary=analysis_struct
            )
        else:
            # 通用章节
            task_prompt = WRITER_PROMPT.format(
                industry=inputs.industry,
                target_year=inputs.target_year,
                focus=inputs.focus,
                province=inputs.province,
                chapter_spec=chapter,
                global_outline=plan_struct["raw_text"],
                analysis_summary=analysis_struct
            )
        
        chapter_tasks.append(
            Task(
                description=task_prompt,
                expected_output=f"章节《{chapter['title']}》的Markdown内容，字数≥2000字。",
                agent=writer,
                async_execution=True
            )
        )
    
    # 主编统稿任务
    compile_task = Task(
        description="""
        你现在的身份是主编。
        上述所有章节已经由你的团队撰写完毕。
        
        请将所有章节的内容按逻辑顺序拼接成一篇完整的行业研究报告。
        
        要求：
        1. 保持Markdown格式，确保各章节标题层级（H1, H2, H3）正确
        2. 不要丢失任何内容
        3. 确保产业链分析章节内容完整
        4. 在报告开头添加报告日期和免责声明
        5. 在报告末尾添加数据来源说明
        """,
        agent=writer,
        expected_output="一篇完整的、拼接好的行业研究报告Markdown全文，字数≥15000字。",
        context=chapter_tasks,
        async_execution=False
    )
    
    writer_crew = Crew(
        agents=[writer],
        tasks=chapter_tasks + [compile_task],
        process=Process.sequential,
        verbose=True
    )
    
    draft_report = str(writer_crew.kickoff())

    # 存入记忆
    memory_manager.save_insight(
        content=draft_report,
        category="report_segment",
        metadata={
            "industry": inputs.industry,
            "province": inputs.province,
            "year": str(inputs.target_year),
            "source_agent": "Writer"
        }
    )
    
    print("✅ 报告撰写完成")

    # ============================================================
    # Phase 5: Reviewer（终审）
    # ============================================================
    print("\n🔍 Phase 5: 质量审核...")
    
    review_task = Task(
        description=REVIEWER_PROMPT.format(report=draft_report),
        expected_output="一份包含审核结论、问题清单和修改建议的评审纪要。",
        agent=reviewer
    )

    review_crew = Crew(
        agents=[reviewer],
        tasks=[review_task],
        process=Process.sequential,
        verbose=True
    )

    review_result = str(review_crew.kickoff())
    
    print("✅ 质量审核完成")

    # ============================================================
    # 最终组合：正文在前，审核意见在后
    # ============================================================
    
    # 添加报告头部
    report_header = f"""# {inputs.industry}行业深度研究报告

**研究区域**：{inputs.province}
**目标年份**：{inputs.target_year}
**报告日期**：{datetime.datetime.now().strftime('%Y年%m月%d日')}
**研究侧重点**：{inputs.focus}

---

> **免责声明**：本报告基于公开信息和数据分析，仅供参考，不构成投资建议。投资者据此操作，风险自担。

---

"""
    
    final_report_content = report_header + draft_report
    
    # 如果审核意见不是"通过"，则将其附在文末作为参考
    if "需修改" in review_result or "问题清单" in review_result:
        final_report_content += "\n\n" + "=" * 50 + "\n"
        final_report_content += "# 🔍 附录：专家评审意见 (Reviewer Feedback)\n"
        final_report_content += "> 注：以下是 AI 质检员对本文的改进建议，仅供参考。\n\n"
        final_report_content += review_result

    # ============================================================
    # 保存文件
    # ============================================================
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../../"))
    output_dir = os.path.join(project_root, "output")
    os.makedirs(output_dir, exist_ok=True)

    date_suffix = datetime.datetime.now().strftime("%Y%m%d")
    filename = f"{inputs.target_year}_{inputs.province}_{inputs.industry}_行业研究报告_{date_suffix}.md"
    file_path = os.path.join(output_dir, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(final_report_content)

    print(f"\n✅ 行业研究报告已生成：{file_path}")
    print(f"📊 报告字数：约 {len(final_report_content)} 字符")

    return final_report_content
