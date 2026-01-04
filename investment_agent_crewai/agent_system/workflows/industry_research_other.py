import os
# 允许 OpenMP 库重复加载
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
# [关键修改] 禁用 CrewAI 遥测，解决 Signal 报错
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
import numpy as np
import torch
import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from tools_custom import stock_analysis, read_pdf, serper_tool, calc_tool, meeting_tool, rag_tool


# 加载环境变量
load_dotenv()

# 强制设置 LiteLLM 底层超时 (虽然任务变轻了，但保留长超时防止万一)
os.environ["LITELLM_REQUEST_TIMEOUT"] = "600"

# 【设置代理】(请确保端口正确)（给 Serper/Google 用）
proxy_url = "http://127.0.0.1:15236" 
os.environ["http_proxy"] = proxy_url
os.environ["https_proxy"] = proxy_url
# 设置不走代理的名单（给 DeepSeek 用）,这样 DeepSeek 会直连，速度快且稳定；而 Serper 依然走上面的代理
os.environ["no_proxy"] = "api.deepseek.com,127.0.0.1,localhost"

# API Key
os.environ["SERPER_API_KEY"] = "a7f48f6305f192f8867f6bedb2d2c5d53c9e374a"

# DeepSeek 配置
deepseek_llm = LLM(
    model="openai/deepseek-chat", 
    base_url=os.getenv("DEEPSEEK_API_BASE"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    temperature=0.3,               
    timeout=1800,                  
    max_tokens=8000,
    max_retries=3  # 增加自动重试，防止网络抖动导致失败
)



# 公司信息查询 
def run_company_research(company_name):
    """
    功能：查询公司基本信息、投融资事件、高管背景
    """
    print(f"🚀 启动公司信息查询: {company_name}")
    
    info_agent = Agent(
        role='Corporate Investigator',
        goal='查询公司全维信息',
        backstory="你是一名商业侦探，擅长挖掘公司的工商信息、历史沿革和投融资记录。",
        tools=[serper_tool, stock_analysis], # 增加股票工具
        llm=deepseek_llm, verbose=True
    )
    
    task_search = Task(
        description=f"""
        请查询 '{company_name}' 的以下信息：
        1. 基本工商信息（成立时间、注册资本、实控人）。
        2. 历史投融资事件（融资轮次、投资方、金额）。
        3. 核心管理层背景。
        4. 如果是上市公司，查询最新股价、市值和PE。
        """,
        expected_output="一份包含公司概况、融资历史和财务摘要的详细报告。",
        agent=info_agent
    )
    
    crew = Crew(agents=[info_agent], tasks=[task_search], verbose=True)
    return crew.kickoff()


# 智能会议纪要
def run_meeting_minutes(folder_path):
    """
    功能：读取文件夹内的零散文件，整理成会议纪要
    """
    print(f"🚀 启动会议纪要整理: {folder_path}")
    
    secretary = Agent(
        role='Executive Secretary',
        goal='整理会议纪要与Action Items',
        backstory="你是一名高效的行政秘书。你能从混乱的速记和多个文档中提炼出会议的核心结论和待办事项。",
        tools=[meeting_tool], # 使用自定义的文件聚合工具
        llm=deepseek_llm, verbose=True
    )
    
    task_summarize = Task(
        description=f"""
        读取目录 '{folder_path}' 下的所有会议记录文件。
        1. 识别会议主题、参会人员、时间。
        2. 总结每个议题的核心讨论点。
        3. **重点提取**：所有 Action Items (待办事项)，包括责任人和截止时间。
        """,
        expected_output="一份结构化的会议纪要（包含摘要、详细内容、To-Do List）。",
        agent=secretary
    )
    
    crew = Crew(agents=[secretary], tasks=[task_summarize], verbose=True)
    return crew.kickoff()

# 商业计划书(BP)解读
def run_bp_interpretation(bp_file_path):
    """
    功能：解读 BP，提取 SWOT
    """
    print(f"🚀 启动 BP 解读: {bp_file_path}")
    
    vc_analyst = Agent(
        role='VC Investment Manager',
        goal='评估项目投资价值',
        backstory="你是一名挑剔的 VC 投资人。你需要快速阅读 BP，找出项目的亮点和致命弱点。",
        tools=[read_pdf],
        llm=deepseek_llm, verbose=True
    )
    
    task_review = Task(
        description=f"""
        阅读商业计划书 '{bp_file_path}'。
        1. 提炼核心：一句话介绍项目是做什么的。
        2. 市场分析：TAM/SAM/SOM 规模。
        3. 团队分析：核心成员背景是否匹配。
        4. **SWOT 分析**：列出优势、劣势、机会、威胁。
        5. 给出初步投资建议（Pass 还是 Continue）。
        """,
        expected_output="一份专业的项目初筛评估报告。",
        agent=vc_analyst
    )
    
    crew = Crew(agents=[vc_analyst], tasks=[task_review], verbose=True)
    return crew.kickoff()

# 财务报表深度分析
def run_financial_report_analysis(file_path):
    """
    功能：深度财报分析
    """
    print(f"🚀 启动财报分析: {file_path}")
    
    cpa_agent = Agent(
        role='Senior CPA',
        goal='识别财务造假风险与经营质量',
        backstory="你是一名经验丰富的注册会计师。你擅长通过财务比率分析发现企业经营的隐患。",
        tools=[read_pdf],
        llm=deepseek_llm, verbose=True
    )
    
    task_analyze = Task(
        description=f"""
        分析财务报告 '{file_path}'。
        1. 计算关键比率：流动比率、速动比率、毛利率、净利率、ROE。
        2. 趋势分析：对比去年同期数据，指出异常波动。
        3. **风险排查**：检查是否有存货积压、应收账款激增等“暴雷”信号。
        """,
        expected_output="一份深度财务诊断报告。",
        agent=cpa_agent
    )
    
    crew = Crew(agents=[cpa_agent], tasks=[task_analyze], verbose=True)
    return crew.kickoff()

# 尽职调查 (Due Diligence)
def run_due_diligence(company_name, material_folder):
    """
    功能：自动化尽调
    """
    print(f"🚀 启动尽职调查: {company_name}")
    
    dd_agent = Agent(
        role='Due Diligence Officer',
        goal='全方位风险扫描',
        backstory="你负责项目的法务和财务尽调初筛。你需要连接外部数据源并查阅内部资料，寻找红线问题。",
        tools=[serper_tool, meeting_tool], # 既搜网上的纠纷，也看本地提供的材料
        llm=deepseek_llm, verbose=True
    )
    
    task_dd = Task(
        description=f"""
        对 {company_name} 进行初步尽调。
        1. 法律风险：搜索是否有未决诉讼、行政处罚。
        2. 舆情风险：搜索近期的负面新闻。
        3. 内部材料核查：阅读 '{material_folder}' 中的文件，检查是否有逻辑矛盾。
        """,
        expected_output="一份尽职调查红旗报告 (Red Flag Report)。",
        agent=dd_agent
    )
    
    crew = Crew(agents=[dd_agent], tasks=[task_dd], verbose=True)
    return crew.kickoff()

# 财务估值建模
def run_financial_valuation(company_name, financials_json):
    """
    功能：DCF / 可比公司估值
    """
    print(f"🚀 启动估值建模: {company_name}")
    
    valuation_expert = Agent(
        role='Valuation Specialist',
        goal='构建精准的估值模型',
        backstory="你精通 DCF 现金流折现法和 Comparable Companies 法。你能根据给定的财务假设，计算出公司的合理估值区间。",
        tools=[calc_tool, serper_tool], # 用搜索找可比公司，用计算器算数
        llm=deepseek_llm, verbose=True
    )
    
    task_model = Task(
        description=f"""
        对 {company_name} 进行估值，财务假设如下：{financials_json}。
        1. **可比公司法**：搜索同行业上市公司的平均 PE/PS 倍数，估算市值。
        2. **DCF 法**：基于输入的现金流预测，调用计算工具得出估值。
        3. 综合两种方法，给出 Football Field 估值区间。
        """,
        expected_output="一份包含详细假设和计算过程的估值报告。",
        agent=valuation_expert
    )
    
    crew = Crew(agents=[valuation_expert], tasks=[task_model], verbose=True)
    return crew.kickoff()

# IPO 路径规划与退出测算
def run_ipo_exit_analysis(company_name, financials, industry, target_exchange):
    """
    功能：IPO 可行性与退出回报
    """
    print(f"🚀 [Module 8] 启动 IPO 分析: {company_name} -> {target_exchange}")
    
    sponsor = Agent(
        role='Sponsor Representative',
        goal='上市可行性诊断',
        backstory="""资深保代，精通各板块上市标准。
        需要周密规划以确保方案符合监管要求，其次要详细测算每种方案的收益率，收益率的影响因子有哪些（比如上市公司股价），并对各影响因子按乐观/中性/保守三种方案做预测。初创企业申请上市，可选项有北交所、港交所、创业板、科创板。我希望能在各个交易所/板块的上市标准中（比如收入利润、研发费用占比、发明专利数量等），能快速提炼出最差异化的部分。即，如果我要投资一家初创企业，我最应该关注企业的哪些经营和财务数据，可以让我最快速判断企业未来应该去哪个板块上市，能不能上市，我的退出路径是怎样的。最好是能够量化统计：按企业当前现状，以及成立至今所呈现出的发展趋势，再结合行业大环境，判断企业适合去哪个交易所哪个板块上市，分别按第几套标准。再量化测算，去不同交易所/不同板，按不同的标准，上市成功的概率分别是多大，分别可能要多少年能实现，分别需要企业未来几年关注哪些事项，优先发展/提升哪些环节，我作为投资人股东，投后工作的重点是什么。""",
        tools=[serper_tool], llm=deepseek_llm, verbose=True
    )
    
    pe_investor = Agent(
        role='PE Partner',
        goal='投资回报测算',
        backstory="""PE合伙人，关注退出路径和IRR。
        去不同交易所/不同板，不同的标准，再考虑目前企业排队数量，审核周期的情况下，分别可能要多少年，企业才能完成上市。再结合各板块/交易所的平均估值倍数，结合流动性，以及我方的持股比例、锁定周期，分析计算我方等到企业完成上市并且我方完全二级市场退出，各自方案下的irr是多少。有了这样的计算，我才能更好的决策，以终为始来看，站在退出的角度来看，我应不应该投这个企业，我投这个企业，预计什么时候能退出来，我能赚多少钱，能有多少的irr。进而，我再对比不同的拟投企业，横向对比各企业的irr，来驱动我作出更好的投资决策。梳理下所有的新三板公司，各公司都具体是什么产品，团队背景，收入水平，市值，是否有转板计划，等。他们适合转什么板，北交所、创业板、科创板。再统计下，历史上有哪些三板企业转板成功的，什么时候成功的，用的具体第几套标准；企业做对了哪些事，使得财务、业务数据上满足了上述标准。再分析讨论，他们转板成功，是否有大环境的因素。尝试总结共性规矩，总结5-10条。然后看，哪些条，可以复用到上面梳理出的三板公司里，进而，这个三板公司值得现在投一点。当然了，还要分析，能否投得进去，是否有交易机会。最后，顺着这个思路，可以再梳理下“先H后A”，H股公司分拆子公司回A，H股公司私有化回A，这三种方案，过往成功的企业有哪些。也要总结5-10条，然后再去套用，目前在港股的企业，有哪些是有投资价值和交易机会的""",
        tools=[calc_tool], llm=deepseek_llm, verbose=True
    )
    
    task1 = Task(
        description=f"分析 {company_name} ({financials}) 是否符合 {target_exchange} 上市条件。",
        expected_output="上市可行性诊断书。",
        agent=sponsor
    )
    task2 = Task(
        description=f"测算在 {target_exchange} 上市后的退出回报 (IRR)。",
        expected_output="退出回报测算表。",
        agent=pe_investor
    )
    
    crew = Crew(agents=[sponsor, pe_investor], tasks=[task1, task2], verbose=True)
    return crew.kickoff()

#并购重组策略 
def run_ma_strategy(listed_company, target_company, my_role):
    """
    功能：并购交易架构设计
    """
    print(f"🚀 启动并购策略: {listed_company} + {target_company}")
    
    ma_banker = Agent(
        role='M&A Banker',
        goal='设计交易架构',
        backstory="擅长设计复杂的并购重组方案（定增、现金、SPV）。",
        tools=[serper_tool], llm=deepseek_llm, verbose=True
    )
    
    task_structure = Task(
        description=f"为 {listed_company} 收购 {target_company} 设计交易方案。我方角色：{my_role}。对比定增、现金、SPV等路径的优劣。",
        expected_output="并购交易架构设计方案。",
        agent=ma_banker
    )
    
    crew = Crew(agents=[ma_banker], tasks=[task_structure], verbose=True)
    return crew.kickoff()