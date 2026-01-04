# tools_custom.py (赋予 Agent 查库能力)
# 修改您的工具定义，现在的工具不再是"读整个文件"，而是"去知识库里查"
# 使用 crewai.tools (点) 导入 BaseTool，BaseTool 是定义在主包 crewai 里的，不是扩展包 crewai_tools 里的
from crewai.tools import BaseTool
from crewai_tools import SerperDevTool
from agent_system.knowledge import kb_manager
import yfinance as yf
import akshare as ak  
from pypdf import PdfReader
import os
import re 
import numpy as np
import pandas as pd
import numpy_financial as npf 

# 升级版工具：支持直接输入中文公司名
# 初始化搜索工具
# search_tool 直接传给 Agent 的 tools 列表即可
serper_tool = SerperDevTool(n_results=5)


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
            info_df = ak.stock_individual_info_em(symbol=stock_code)
            info_dict = dict(zip(info_df['item'], info_df['value']))
            
            # 2. 获取主要财务指标 (营收、净利等)
            fin_df = ak.stock_financial_abstract(symbol=stock_code)
            
            # 3. 组装摘要数据
            summary = {
                "Company Code": stock_code,
                "Market": "A-Share (CN)",
                "Market Cap (总市值)": f"{info_dict.get('总市值')} 元",
                "PE Ratio (动态市盈率)": info_dict.get('市盈率(动)'),
                "Sector (行业)": info_dict.get('行业'),
                "Listing Date": info_dict.get('上市时间'),
                "Stock Name": "N/A"
            }

            # 4. 组装财务报表 (取最近4期数据)
            if not fin_df.empty:
                financials_str = fin_df.tail(4).to_string()
            else:
                financials_str = "Financial abstract data not available."
            
            return f"Analysis for A-Share {stock_code}:\nSummary: {summary}\n\nRecent Financials (Abstract):\n{financials_str}"

        except Exception as e:
            return f"AkShare Error for {stock_code}: {str(e)}"

    def _fetch_ticker_code(self, query: str) -> str:
        """
        利用搜索将"公司名"转换为"股票代码"
        """
        query = query.strip()
        
        if query in self._ticker_cache:
            return self._ticker_cache[query]

        if re.match(r'^\d{6}$', query):
            return query

        if re.match(r'^\d{6}\.(SS|SZ)$', query):
            clean_code = query.split('.')[0]
            self._ticker_cache[query] = clean_code
            return clean_code

        try:
            search_query = f"{query} 股票代码 stock ticker"
            result = serper_tool.run(search_query)
            
            match_a = re.search(r'(code|代码|ticker)[:\s]*(\d{6})', result, re.IGNORECASE)
            match_num = re.search(r'\b(60\d{4}|00\d{4}|30\d{4})\b', result)
            
            if match_a:
                code = match_a.group(2)
                self._ticker_cache[query] = code
                return code
            elif match_num:
                code = match_num.group(1)
                self._ticker_cache[query] = code
                return code
            
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
            
            real_ticker = self._fetch_ticker_code(ticker_or_name)
            
            if not real_ticker:
                return f"Error: Could not find ticker for '{ticker_or_name}'."

            if self._is_a_share(real_ticker):
                return self._fetch_a_share_data(real_ticker)
            
            else:
                stock = yf.Ticker(real_ticker)
                info = stock.info
                
                if not info or 'regularMarketPrice' not in info:
                     return f"Error: yfinance failed to get data for {real_ticker}."

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
            file_path = file_path.strip().strip('"').strip("'")
            base_dir = "knowledge_base"
            final_path = file_path
            
            if not os.path.exists(final_path):
                filename = os.path.basename(file_path)
                potential_path = os.path.join(base_dir, filename)
                
                if os.path.exists(potential_path):
                    final_path = potential_path
                else:
                    if os.path.exists(base_dir):
                        all_files = os.listdir(base_dir)
                        return f"Error: File '{filename}' not found. Available files in {base_dir}: {all_files}"
                    return f"Error: File not found at {file_path} (and {base_dir} folder missing)."

            reader = PdfReader(final_path)
            text = ""
            max_pages = 20 
            for i, page in enumerate(reader.pages):
                if i >= max_pages: break
                text += page.extract_text() + "\n"
                
            return f"--- Content of {final_path} (First {max_pages} pages) ---\n{text}"
            
        except Exception as e:
            return f"Error reading PDF: {str(e)}"


class RecallHistoryTool(BaseTool):
    name: str = "Search Historical Insights"
    description: str = "Query the internal long-term memory for past facts, conclusions, or report segments. Useful for checking consensus or finding historical data."

    def _run(self, query: str) -> str:
        try:
            from memory_system.memory_manager import memory_manager
            results = memory_manager.recall_memory(query, k=5)
            if not results:
                return "No relevant historical insights found."
                
            return f"Found specific historical insights:\n{results}"
        except Exception as e:
            return f"Memory recall failed: {str(e)}"


class FinancialCalculatorTool(BaseTool):
    name: str = "Financial IRR & Sensitivity Calculator"
    description: str = "Useful for calculating IRR, NPV, Valuation Multiples and performing sensitivity analysis for M&A or IPO scenarios."

    def _run(self, query: str) -> str:
        try:
            scenarios = ["保守", "中性", "乐观"]
            exit_multiples = [15, 25, 40]
            net_profits = [1.5, 2.0, 3.0]
            investment_cost = 0.5
            years = 4
            
            results = []
            for i, scenario in enumerate(scenarios):
                exit_val = exit_multiples[i] * net_profits[i]
                my_share_val = exit_val * 0.10
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
                    reader = PdfReader(f_path)
                    text = ""
                    for page in reader.pages[:5]: text += page.extract_text()
                    aggregated_text += f"\n--- File: {f} ---\n{text}"
            return aggregated_text[:10000]
        except Exception as e:
            return f"Error reading files: {str(e)}"


class RAGSearchTool(BaseTool):
    name: str = "Search Local Knowledge Base"
    description: str = "Useful for finding specific details in local reports. Input should be a specific question."

    def _run(self, query: str) -> str:
        try:
            evidence = kb_manager.query_knowledge(query, n_results=5)
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


# ============================================================
# 新增工具：产业链专项搜索
# ============================================================
class SupplyChainSearchTool(BaseTool):
    name: str = "Supply Chain Industry Search"
    description: str = "Search for supply chain information of a specific industry. Input: industry name (e.g., '半导体', '新能源汽车'). Returns upstream, midstream, downstream analysis."

    def _run(self, industry: str) -> str:
        try:
            industry = industry.strip()
            
            # 构建多维度搜索查询
            queries = [
                f"{industry} 产业链 上游 原材料 供应商",
                f"{industry} 产业链 中游 制造 加工",
                f"{industry} 产业链 下游 应用 客户",
                f"{industry} 产业链图谱 全景图",
                f"{industry} 产业链 龙头企业 市场份额"
            ]
            
            all_results = []
            for query in queries:
                try:
                    result = serper_tool.run(query)
                    all_results.append(f"【查询: {query}】\n{result}\n")
                except:
                    continue
            
            if not all_results:
                return f"未找到 {industry} 行业的产业链信息"
            
            output = f"【{industry}】产业链搜索结果\n"
            output += "=" * 50 + "\n\n"
            output += "\n".join(all_results)
            
            return output
        except Exception as e:
            return f"产业链搜索失败: {str(e)}"


class PolicySearchTool(BaseTool):
    name: str = "Industry Policy Search"
    description: str = "Search for policy information of a specific industry. Input format: 'industry,province' (e.g., '半导体,浙江省'). Province is optional."

    def _run(self, query: str) -> str:
        try:
            parts = query.strip().split(',')
            industry = parts[0].strip()
            province = parts[1].strip() if len(parts) > 1 else ""
            
            queries = []
            if province:
                queries.append(f"{province} {industry} 产业政策 规划")
                queries.append(f"{province} {industry} 补贴 扶持政策")
                queries.append(f"{province} {industry} 十四五 发展规划")
            else:
                queries.append(f"{industry} 国家政策 产业规划")
                queries.append(f"{industry} 补贴政策 扶持措施")
            
            queries.append(f"{industry} 监管政策 行业规范")
            
            all_results = []
            for q in queries:
                try:
                    result = serper_tool.run(q)
                    all_results.append(f"【查询: {q}】\n{result}\n")
                except:
                    continue
            
            if not all_results:
                return f"未找到 {industry} 行业的政策信息"
            
            output = f"【{industry}】政策搜索结果"
            if province:
                output += f"（{province}）"
            output += "\n" + "=" * 50 + "\n\n"
            output += "\n".join(all_results)
            
            return output
        except Exception as e:
            return f"政策搜索失败: {str(e)}"


class MarketSizeSearchTool(BaseTool):
    name: str = "Market Size Search"
    description: str = "Search for market size data of a specific industry. Input format: 'industry,region' (e.g., '半导体,中国'). Region is optional, defaults to China."

    def _run(self, query: str) -> str:
        try:
            parts = query.strip().split(',')
            industry = parts[0].strip()
            region = parts[1].strip() if len(parts) > 1 else "中国"
            
            queries = [
                f"{region} {industry} 市场规模 2024 2025",
                f"{industry} 市场规模 增速 CAGR",
                f"{industry} 行业规模 预测 趋势",
                f"{industry} 渗透率 市场空间"
            ]
            
            all_results = []
            for q in queries:
                try:
                    result = serper_tool.run(q)
                    all_results.append(f"【查询: {q}】\n{result}\n")
                except:
                    continue
            
            if not all_results:
                return f"未找到 {industry} 行业的市场规模数据"
            
            output = f"【{industry}】市场规模搜索结果（{region}）\n"
            output += "=" * 50 + "\n\n"
            output += "\n".join(all_results)
            
            return output
        except Exception as e:
            return f"市场规模搜索失败: {str(e)}"


class CompanySearchTool(BaseTool):
    name: str = "Industry Company Search"
    description: str = "Search for company information in a specific industry. Input format: 'industry,province' (e.g., '半导体,浙江省'). Province is optional."

    def _run(self, query: str) -> str:
        try:
            parts = query.strip().split(',')
            industry = parts[0].strip()
            province = parts[1].strip() if len(parts) > 1 else ""
            
            queries = []
            if province:
                queries.append(f"{province} {industry} 龙头企业 排名")
                queries.append(f"{province} {industry} 上市公司 名单")
            else:
                queries.append(f"{industry} 龙头企业 市场份额 排名")
                queries.append(f"{industry} 上市公司 龙头 对比")
            
            queries.append(f"{industry} 企业 营收 净利润 对比")
            queries.append(f"{industry} 独角兽 融资 估值")
            
            all_results = []
            for q in queries:
                try:
                    result = serper_tool.run(q)
                    all_results.append(f"【查询: {q}】\n{result}\n")
                except:
                    continue
            
            if not all_results:
                return f"未找到 {industry} 行业的企业信息"
            
            output = f"【{industry}】企业搜索结果"
            if province:
                output += f"（{province}）"
            output += "\n" + "=" * 50 + "\n\n"
            output += "\n".join(all_results)
            
            return output
        except Exception as e:
            return f"企业搜索失败: {str(e)}"


class BusinessModelSearchTool(BaseTool):
    name: str = "Business Model Search"
    description: str = "Search for business model and profitability information of a specific industry. Input: industry name."

    def _run(self, industry: str) -> str:
        try:
            industry = industry.strip()
            
            queries = [
                f"{industry} 商业模式 盈利模式",
                f"{industry} 收入结构 成本结构",
                f"{industry} 毛利率 净利率 对比",
                f"{industry} 龙头企业 财务分析"
            ]
            
            all_results = []
            for q in queries:
                try:
                    result = serper_tool.run(q)
                    all_results.append(f"【查询: {q}】\n{result}\n")
                except:
                    continue
            
            if not all_results:
                return f"未找到 {industry} 行业的商业模式信息"
            
            output = f"【{industry}】商业模式搜索结果\n"
            output += "=" * 50 + "\n\n"
            output += "\n".join(all_results)
            
            return output
        except Exception as e:
            return f"商业模式搜索失败: {str(e)}"


# 实例化工具
rag_tool = RAGSearchTool()
stock_analysis = StockAnalysisTool()
read_pdf = PDFReadTool()
calc_tool = FinancialCalculatorTool()
meeting_tool = MeetingNotesAggregator()
recall_tool = RecallHistoryTool()

# 新增工具实例
supply_chain_search = SupplyChainSearchTool()
policy_search = PolicySearchTool()
market_size_search = MarketSizeSearchTool()
company_search = CompanySearchTool()
business_model_search = BusinessModelSearchTool()
