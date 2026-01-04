# agent_system/workflows/industry_research.py
# | 层               | 职责   |
# | Prompt          | 思考路径 |
# | Expected Output | 交付标准 |
# | Agent           | 能力人格 |
# | Workflow        | 执行顺序 |

# 行业研究主工作流（Phase 1–5）
# Planner → Researcher → Analyst → Writer → Reviewer

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
    RESEARCHER_INDUSTRY_PROMPT
)
from agent_system.prompts.analyst_prompt import ANALYST_PROMPT
from agent_system.prompts.writer_prompt import WRITER_PROMPT
from agent_system.prompts.reviewer_prompt import REVIEWER_PROMPT

# ===== Parsers（当前可先返回 dict，占位）=====
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

    # ---------- 输入校验 ----------
    if isinstance(inputs, dict):
        inputs = IndustryResearchInput(**inputs)

    prompt_vars = inputs.model_dump()

    # ============================================================
    # Phase 0: 定义 Agents（只定义一次）
    # Agent Backstory = “你是谁、你长期的思维方式是什么”，系统层prompt
    # ============================================================

    planner = Agent(
        role="Lead Research Planner",
        goal="制定行业研究的完整逻辑框架与关键问题清单",
        backstory=(
            "你是一名一级市场投研总监，擅长从投资视角拆解行业。"
            "你的大纲必须服务于投资决策，而不是科普。"
            "擅长规划宏观、中观、微观的研究框架。内容包括宏观环境、上下游拆解、竞争格局（有数据对比）、重点标的深度财务分析、风险提示"
        ),
        llm=llm,
        verbose=True
    )

    researcher = Agent(
        role="Senior Industry Data Researcher",
        goal="搜集关键年份的财务、政策与产业数据",
        backstory=(
            "你是一名高效研究员，只关心可验证的数据、数字与结论。"
            "避免长篇描述，优先结构化信息。"
            "你是一名高效的数据挖掘专家。"
        "关键原则："
        "1. 抓大放小：重点找龙头的营收/净利/市值，以及核心政策KPI。"
        "2. 拒绝冗余：不需要搜集过于细枝末节的技术参数，关注商业落地的核心指标。"
        "3. 拥有读取本地知识库的能力，只提取最关键的结论。"
        ),
        tools=[stock_analysis, serper_tool, read_pdf, rag_tool, recall_tool],
        llm=llm,
        verbose=True
    )
    
    analyst = Agent(
        role="Investment Analyst",
        goal="从数据中提炼核心投资结论,基于现有数据进行对比，进行深度行业分析，产出核心结论",
        backstory="你关注比较、差异、趋势与产业链缺口。基于最新数据分析产业链缺口（包括业绩、市场、产品、技术、组织方面），关注当下市场格局和未来预测",
        tools=[rag_tool, recall_tool],
        llm=llm,
        verbose=True,
        max_iter=3, max_execution_time=1800
    )

    writer = Agent(
        role="Professional Report Writer",
        goal="撰写专业、结构清晰的行业研究报告",
        backstory=(
            "你遵循：结论先行、段落自洽、表格辅助。"
            "拒绝空话与堆砌。"
            "时效性强：报告第一行注明日期。"
        ),
        llm=llm,
        verbose=True
    ) 

    reviewer = Agent(
        role="Quality Assurance Reviewer",
        goal="确保逻辑一致性与数据完整性",
        backstory="你只做必要检查，不重写内容。",
        llm=llm,
        verbose=True
    )

    # ============================================================
    # Phase 1: Planner（规划）
    # ============================================================
    plan_task = Task(
        description=PLANNER_PROMPT.format(**prompt_vars),
        expected_output="一份包含三级目录、预设图表位置的详细大纲。", 
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

    # ============================================================
    # Phase 2: Researcher（并行研究）
    # ============================================================
    # 1. 定义三个异步子任务 (保持不变)
    finance_task = Task(
        description=RESEARCHER_FINANCE_PROMPT.format(**prompt_vars),
        agent=researcher,
        expected_output="一份包含3-5家龙头企业财务指标（营收/净利/PE等）的原始财务数据列表",
        async_execution=True  # ✅ 并行
    )
    
    policy_task = Task(
        description=RESEARCHER_POLICY_PROMPT.format(**prompt_vars),
        agent=researcher,
        expected_output="一份包含政策名称、发布时间、核心KPI数字的列表",
        async_execution=True  # ✅ 并行
    )
    
    industry_task = Task(
        description=RESEARCHER_INDUSTRY_PROMPT.format(**prompt_vars),
        agent=researcher,
        expected_output="一份包含行业产值、增速、技术壁垒数据的汇总",
        async_execution=True  # ✅ 并行
    )

    # 2. 【新增】定义一个同步的汇总任务
    # 它的作用是等待上面三个做完，并把结果打包
    summary_task = Task(
        description="""
        作为首席研究员，汇总上述【财务】、【政策】、【行业】三个维度的搜集结果。
        请将散落在各处的关键数据整理成一份结构化的“行业数据摘要”，去除重复信息，供分析师使用。
        """,
        agent=researcher,
        expected_output="一份包含财务、政策、行业三方面关键数据的完整调研纪要。",
        context=[finance_task, policy_task, industry_task], # 🔥 关键：指定上下文，强制等待这三个任务
        async_execution=False # ❌ 必须是同步 (默认就是False，这里显式写出来)
    )

    # 3. 将所有任务加入 Crew
    research_crew = Crew(
        agents=[researcher],
        # 注意顺序：并行任务在前，汇总任务在最后
        tasks=[finance_task, policy_task, industry_task, summary_task], 
        process=Process.sequential,
        verbose=True
    )
    
    # 4. 运行
    research_result = research_crew.kickoff()
    
    # 解析 (因为有了汇总任务，kickoff 返回的就是 summary_task 的结果，直接是字符串)
    research_structs = [parse_researcher_output(str(research_result))]

    # 假设 research_raw_results 是一个包含财务、政策、行业信息的长字符串
    # 【动作】将 Researcher 的成果存入长期记忆
    memory_manager.save_insight(
        content=str(research_result),
        category="fact", # 或者细分为 fact_finance, fact_industry
        metadata={
            "industry": inputs.industry,
            "province": inputs.province,
            "year": str(inputs.target_year),
            "source_agent": "Researcher"
        }
    )

    # ============================================================
    # Phase 3: Analyst（综合分析）
    # ============================================================
    analyst_task = Task(
        description=ANALYST_PROMPT.format(
            industry=inputs.industry,
            target_year=inputs.target_year,
            focus=inputs.focus,
            province=inputs.province,
            research_summary=research_structs
        ),
        expected_output="一份包含深度分析逻辑和结构化对比数据的中间分析稿。", 
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

    # 【动作】将分析师的核心观点存入记忆，供未来复用
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

    # ============================================================
    # Phase 4: Writer（分章节并行写作）
    # ============================================================
    chapter_tasks = []
    
    # 1. 创建并行的章节写作任务
    for chapter in plan_struct["chapters"]:
        chapter_tasks.append(
            Task(
                description=WRITER_PROMPT.format(
                    industry=inputs.industry,
                    target_year=inputs.target_year,
                    focus=inputs.focus,
                    province=inputs.province,
                    chapter_spec=chapter,
                    global_outline=plan_struct["raw_text"],
                    analysis_summary=analysis_struct
                ),
                expected_output=f"章节《{chapter['title']}》的Markdown内容。", 
                agent=writer,
                async_execution=True # ✅ 并行写作
            )
        )
    
    # 2. 【新增】创建一个“主编统稿”任务
    compile_task = Task(
        description="""
        你现在的身份是主编。
        上述所有章节已经由你的团队撰写完毕。
        请将所有章节的内容按逻辑顺序拼接成一篇完整的行业研究报告。
        保持Markdown格式，确保各章节标题层级（H1, H2, H3）正确，不要丢失任何内容。
        """,
        agent=writer,
        expected_output="一篇完整的、拼接好的行业研究报告Markdown全文。",
        context=chapter_tasks, # 🔥 关键：等待所有章节写完，并获取它们的内容
        async_execution=False  # ❌ 同步
    )
    
    # 3. 运行
    writer_crew = Crew(
        agents=[writer],
        # 将编译任务追加到列表末尾
        tasks=chapter_tasks + [compile_task], 
        process=Process.sequential, 
        verbose=True
    )
    
    # 4. 获取结果
    # kickoff() 现在返回的是 compile_task 的结果，即由于 AI 拼接好的全文
    draft_report = str(writer_crew.kickoff())

    # 【动作】将写好的正文存入，作为未来的“写作语料库”
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
    
    # ============================================================
    # Phase 5: Reviewer（终审） 将 Reviewer 的输出视为 "Audit Log" 而不是 "Final Content"
    # ============================================================
    # 修改：
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

    # ============================================================
    # 📝 最终组合：正文在前，审核意见在后
    # ============================================================
    
    # 构造最终报告内容
    final_report_content = draft_report
    
    # 如果审核意见不是“通过”，则将其附在文末作为参考
    if "需修改" in review_result or "问题清单" in review_result:
        final_report_content += "\n\n" + "="*50 + "\n"
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

    print(f"✅ 行业研究报告已生成（含评审意见）：{file_path}")

    # 返回给前端显示的也应该是完整内容
    return final_report_content

