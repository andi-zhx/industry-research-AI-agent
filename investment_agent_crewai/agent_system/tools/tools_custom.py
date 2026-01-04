# tools_custom.py (赋予 Agent 查库能力)
# 修改您的工具定义，现在的工具不再是“读整个文件”，而是“去知识库里查”
# 使用 crewai.tools (点) 导入 BaseTool，BaseTool 是定义在主包 crewai 里的，不是扩展包 crewai_tools 里的
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from agent_system.knowledge import kb_manager
import yfinance as yf
import akshare as ak  
# from langchain_community.tools import DuckDuckGoSearchRun
from pypdf import PdfReader
import os
import re 
import numpy as np
import pandas as pd
import numpy_financial as npf 

# 升级版工具：支持直接输入中文公司名
# 初始化搜索工具
# search_tool 直接传给 Agent 的 tools 列表即可
serper_tool = SerperDevTool(n_results=3)

# 如果你以后想加其他工具（比如读取 PDF、分析网页内容），也可以在这里实例化
# from crewai_tools import ScrapeWebsiteTool
# scrape_tool = ScrapeWebsiteTool()


class StockAnalysisTool(BaseTool):
    name: str = "Stock Fundamental Analysis"
    description: str = "Useful to get financial fundamentals. Input can be a **Company Name** (e.g., '比亚迪', 'NVDA') or Ticker."
    
    # 简单的内存缓存，避免重复搜索同一个公司代码
    _ticker_cache: dict = {}

    def _is_a_share(self, code: str) -> bool:
        """
        判断是否为 A 股代码 (6位数字)
        """
        return bool(re.match(r'^\d{6}$', code.strip()))

    def _fetch_a_share_data(self, stock_code: str) -> str:
        """
        【A股专用】使用 AkShare 获取精准财务数据
        """
        try:
            stock_code = stock_code.strip()
            
            # 1. 获取个股实时信息 (市值、PE、行业等)
            # 接口: 东方财富-个股信息
            info_df = ak.stock_individual_info_em(symbol=stock_code)
            # info_df 结构通常是 item, value 两列
            info_dict = dict(zip(info_df['item'], info_df['value']))
            
            # 2. 获取主要财务指标 (营收、净利等)
            # 接口: 财务摘要
            fin_df = ak.stock_financial_abstract(symbol=stock_code)
            
            # 3. 组装摘要数据
            summary = {
                "Company Code": stock_code,
                "Market": "A-Share (CN)",
                "Market Cap (总市值)": f"{info_dict.get('总市值')} 元",
                "PE Ratio (动态市盈率)": info_dict.get('市盈率(动)'),
                "Sector (行业)": info_dict.get('行业'),
                "Listing Date": info_dict.get('上市时间'),
                "Stock Name": "N/A" # AkShare这个接口有时不返回名字，但这不影响计算
            }

            # 4. 组装财务报表 (取最近4期数据)
            if not fin_df.empty:
                # 按照报告期排序，取最新的
                financials_str = fin_df.tail(4).to_string()
            else:
                financials_str = "Financial abstract data not available."
            
            return f"Analysis for A-Share {stock_code}:\nSummary: {summary}\n\nRecent Financials (Abstract):\n{financials_str}"

        except Exception as e:
            return f"AkShare Error for {stock_code}: {str(e)}"

    def _fetch_ticker_code(self, query: str) -> str:
        """
        利用搜索将“公司名”转换为“股票代码”
        """
        query = query.strip()
        
        # 0. 查缓存
        if query in self._ticker_cache:
            return self._ticker_cache[query]

        # 1. 如果输入已经是纯数字代码 (如 600519)，直接返回
        if re.match(r'^\d{6}$', query):
            return query

        # 2. 如果是 Yahoo 格式 (600519.SS)，去后缀转为纯数字 (为了传给 AkShare)
        if re.match(r'^\d{6}\.(SS|SZ)$', query):
            clean_code = query.split('.')[0]
            self._ticker_cache[query] = clean_code
            return clean_code

        # 3. 使用 Serper 搜索
        try:
            # 搜索词技巧
            search_query = f"{query} 股票代码 stock ticker"
            result = serper_tool.run(search_query)
            
            # A. 优先匹配 A股代码 (6位数字)
            match_a = re.search(r'(code|代码|ticker)[:\s]*(\d{6})', result, re.IGNORECASE)
            # 或者直接匹配 60/00/30 开头的6位数字
            match_num = re.search(r'\b(60\d{4}|00\d{4}|30\d{4})\b', result)
            
            if match_a:
                code = match_a.group(2)
                self._ticker_cache[query] = code
                return code
            elif match_num:
                code = match_num.group(1)
                self._ticker_cache[query] = code
                return code
            
            # B. 匹配美股/港股代码 (字母 或 数字.HK)
            # 简单匹配全大写字母 (如 NVDA, AAPL)
            match_us = re.search(r'\b[A-Z]{2,5}\b', result)
            if match_us:
                code = match_us.group(0)
                self._ticker_cache[query] = code
                return code
                
            return None
        except Exception:
            return None

    def _run(self, ticker_or_name: str) -> str:
        try:
            ticker_or_name = ticker_or_name.strip()
            
            # 步骤 1: 获取代码
            real_ticker = self._fetch_ticker_code(ticker_or_name)
            
            if not real_ticker:
                return f"Error: Could not find ticker for '{ticker_or_name}'."

            # 步骤 2: 路由分发
            
            # === 分支 A: A股 (走 AkShare) ===
            if self._is_a_share(real_ticker):
                return self._fetch_a_share_data(real_ticker)
            
            # === 分支 B: 美股/港股/其他 (走 yfinance) ===
            else:
                stock = yf.Ticker(real_ticker)
                info = stock.info
                
                # 容错：如果 info 为空，说明可能 yfinance 没找到
                if not info or 'regularMarketPrice' not in info:
                     return f"Error: yfinance failed to get data for {real_ticker}. It might be delisted or the ticker is wrong."

                summary = {
                    "Company": info.get('longName', real_ticker),
                    "Ticker": real_ticker,
                    "Price": info.get('currentPrice') or info.get('regularMarketPrice'),
                    "Market Cap": info.get('marketCap'),
                    "PE Ratio": info.get('trailingPE'),
                    "Forward PE": info.get('forwardPE'),
                    "Sector": info.get('sector'),
                    "Business Summary": info.get('longBusinessSummary')
                }
                
                if not stock.financials.empty:
                    financials = stock.financials.iloc[:, :2].to_string()
                else:
                    financials = "Financial data not available via API."
                    
                return f"Analysis for {real_ticker} (yfinance):\nSummary: {summary}\n\nRecent Financials:\n{financials}"

        except Exception as e:
            return f"Error analyzing {ticker_or_name}: {str(e)}"

class PDFReadTool(BaseTool):
    name: str = "Read Local PDF Report"
    description: str = "Useful for reading the FULL content of a local PDF file. Input: filename or path."

    def _run(self, file_path: str) -> str:
        try:
            # --- 【关键修复逻辑】 ---
            # 1. 清理文件名中的多余引号（LLM有时候会多传引号）
            file_path = file_path.strip().strip('"').strip("'")
            
            # 2. 定义知识库默认目录
            base_dir = "knowledge_base"
            
            # 3. 智能寻找文件路径
            # 情况A: Agent给的是绝对路径或正确的相对路径，且文件存在 -> 直接用
            final_path = file_path
            
            if not os.path.exists(final_path):
                # 情况B: Agent只给了文件名，没给路径 -> 尝试拼接 knowledge_base
                # os.path.basename 确保只取文件名，防止 Agent 传了错误的路径前缀
                filename = os.path.basename(file_path)
                potential_path = os.path.join(base_dir, filename)
                
                if os.path.exists(potential_path):
                    final_path = potential_path
                else:
                    # 情况C: 还是找不到，列出目录下所有文件帮助排查
                    if os.path.exists(base_dir):
                        all_files = os.listdir(base_dir)
                        return f"Error: File '{filename}' not found. Available files in {base_dir}: {all_files}"
                    return f"Error: File not found at {file_path} (and {base_dir} folder missing)."

            # 4. 开始读取
            reader = PdfReader(final_path)
            text = ""
            max_pages = 20 
            for i, page in enumerate(reader.pages):
                if i >= max_pages: break
                text += page.extract_text() + "\n"
                
            return f"--- Content of {final_path} (First {max_pages} pages) ---\n{text}"
            
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

# 让 Agent 主动查阅“历史记忆”
class RecallHistoryTool(BaseTool):
    name: str = "Search Historical Insights"
    description: str = "Query the internal long-term memory for past facts, conclusions, or report segments. Useful for checking consensus or finding historical data."

    def _run(self, query: str) -> str:
        # 调用 memory_manager 进行搜索
        try:
            from memory_system.memory_manager import memory_manager
            # 这里可以搜索 fact 或 conclusion
            results = memory_manager.recall_memory(query, k=5)
            if not results:
                return "No relevant historical insights found."
                
            return f"Found specific historical insights:\n{results}"
        except Exception as e:
            return f"Memory recall failed: {str(e)}"


# 财务计算器 (用于估值建模和IPO测算)
class FinancialCalculatorTool(BaseTool):
    name: str = "Financial IRR & Sensitivity Calculator"
    description: str = "Useful for calculating IRR, NPV, Valuation Multiples and performing sensitivity analysis for M&A or IPO scenarios. Input should be a dictionary string with 'cash_flows' or 'sensitivity_params'."

    def _run(self, query: str) -> str:
        try:
            # 这是一个简化的模拟计算逻辑，实际可接收 JSON 参数进行复杂运算
            # 模拟：计算 IPO 退出回报
            # 假设输入包含: 投资额, 持有年限, 退出倍数, 净利润
            
            # 这里为了演示，我们硬编码一个标准的敏感性分析逻辑供 Agent 调用
            # 在真实产品中，Agent 会提取参数传进来
            
            # 场景：IPO 退出回报测算
            scenarios = ["保守", "中性", "乐观"]
            exit_multiples = [15, 25, 40] # PE倍数
            net_profits = [1.5, 2.0, 3.0] # 亿元 (上市年)
            investment_cost = 0.5 # 亿元
            years = 4
            
            results = []
            for i, scenario in enumerate(scenarios):
                exit_val = exit_multiples[i] * net_profits[i]
                my_share_val = exit_val * 0.10 # 假设持股 10%
                cash_flows = [-investment_cost] + [0]*(years-1) + [my_share_val]
                irr = npf.irr(cash_flows) * 100
                roi = (my_share_val - investment_cost) / investment_cost
                
                results.append(f"【{scenario}方案】\n"
                               f"  - 退出估值: {exit_val}亿\n"
                               f"  - IRR: {irr:.2f}%\n"
                               f"  - MOIC: {roi+1:.2f}x")
            
            return "\n".join(results)
        except Exception as e:
            return f"Calculation failed: {str(e)}"

# 文本聚合工具 (用于智能会议纪要，读取文件夹下所有文件)
class MeetingNotesAggregator(BaseTool):
    name: str = "Meeting Notes Reader"
    description: str = "Read and aggregate all text/pdf files in a specific folder for meeting minutes. Input: Folder path."

    def _run(self, folder_path: str) -> str:
        try:
            if not os.path.exists(folder_path): return "Folder not found."
            aggregated_text = ""
            for f in os.listdir(folder_path):
                f_path = os.path.join(folder_path, f)
                if f.endswith('.txt'):
                    with open(f_path, 'r', encoding='utf-8') as file:
                        aggregated_text += f"\n--- File: {f} ---\n{file.read()}"
                elif f.endswith('.pdf'):
                    # 简单调用 PDF 读取逻辑
                    reader = PdfReader(f_path)
                    text = ""
                    for page in reader.pages[:5]: text += page.extract_text()
                    aggregated_text += f"\n--- File: {f} ---\n{text}"
            return aggregated_text[:10000] # 限制长度防止 Token 爆炸
        except Exception as e:
            return f"Error reading files: {str(e)}"


# 强制引用链 (Citation Chain) 让 RAG 返回的数据携带元数据（Metadata），并强行要求 Agent 在输出时保留这些标记
class RAGSearchTool(BaseTool):
    name: str = "Search Local Knowledge Base"
    description: str = "Useful for finding specific details in local reports. Input should be a specific question, e.g., 'What is the gross margin of BYD in 2024?'"

    def _run(self, query: str) -> str:
        try:
            # 去向量数据库搜索
            evidence = kb_manager.query_knowledge(query, n_results=5)
            # 添加系统提示，强制 Agent 引用
            instruction = """
            【重要指令】：
            使用上述信息回答时，必须在句尾标注来源，格式为 [来源: 文件名]。
            如果信息中包含具体数字，必须保留原始上下文。
            """
            if not evidence:
                return "No relevant info found in local database."
            return f"{instruction}\n\n相关知识库内容:\n{evidence}"
        except Exception as e:
            return f"Error querying knowledge base: {str(e)}"


# 实例化工具
rag_tool = RAGSearchTool()
stock_analysis = StockAnalysisTool()
read_pdf = PDFReadTool()
calc_tool = FinancialCalculatorTool()
meeting_tool = MeetingNotesAggregator()
recall_tool = RecallHistoryTool()

