# app.py 只做 UI + 调用 main
# ==========================================
# FinSight 投研系统 · 前端入口（Streamlit）
# 增强版：支持六大研究维度，重点产业链分析
# ==========================================
# ----------- 运行时与网络（必须最先）-----------
from config.runtime_env import setup_runtime_env
from config.network import setup_network

setup_runtime_env()
setup_network()

# ----------- 基础依赖 -----------
import os
import time
from datetime import datetime

import streamlit as st
import pandas as pd
import numpy as np

# ----------- 项目内模块 -----------
import app_config as config
import ui_styles as ui

# 后端入口（Facade）
try:
    import main
    HAS_BACKEND = True
except ImportError as e:
    HAS_BACKEND = False
    BACKEND_ERROR = str(e)

# 知识库引擎（RAG--knowledge_engine.py）
try:
    from agent_system.knowledge import kb_manager
except ImportError:
    kb_manager = None  #容错

# ----------- 页面配置（必须第一个 Streamlit 调用）-----------
st.set_page_config(
    page_title="FinSight 智能投研 | 行业研究智能体",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------- 初始化目录 -----------
config.init_directories()

# ----------- UI 样式 -----------
ui.apply_custom_css()
ui.render_header()

# ----------- 后端状态提示 -----------
if not HAS_BACKEND:
    st.error(f"⚠️ 后端 main.py 未就绪：{BACKEND_ERROR}")

# ============================================================
# 侧边栏导航
# ============================================================
with st.sidebar:
    st.subheader("功能导航")
    
    menu = st.radio(
        "请选择业务模块:",
        [
            "📊 行业深度研究",
            "🔗 产业链专项分析",
            "🏢 公司信息查询",
            "📝 智能会议纪要",
            "📑 BP 商业计划书解读",
            "📈 财务报表深度分析",
            "⚖️ 尽职调查 (DD)",
            "💰 财务估值建模",
            "🚀 IPO 路径与退出测算",
            "🤝 并购重组策略 (M&A)"
        ],
        index=0
    )
    
    st.divider()
    st.info(f"系统状态: {'🟢 在线' if HAS_BACKEND else '🔴 离线'}\n\n日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示六大研究维度框架
    with st.expander("📚 研究维度框架", expanded=False):
        st.markdown("""
        **六大研究维度**
        
        ① 行业定义与边界
        ② 市场规模与趋势
        ③ 产业链结构 【重点】
        ④ 典型玩家与格局
        ⑤ 商业模式与变现
        ⑥ 政策/科技/环境
        """)


# ============================================================
# 模块 1: 行业深度研究（增强版）
# ============================================================
if menu == "📊 行业深度研究":
    st.subheader("📊 行业深度研究")
    st.caption("基于六大研究维度的深度行业分析，重点关注产业链结构与投资机会")
    
    col_input, col_display = st.columns([1, 2])
    
    with col_input:
        with st.container():
            st.markdown("#### 🎯 研究参数")
            
            # 1. 区域选择
            sel_province = st.selectbox("📍 目标区域", config.PROVINCE_LIST, index=config.PROVINCE_LIST.index("浙江省"))
            
            # 2. 产业链级联 (核心保留功能)
            st.markdown("🏭 **产业链定位**")
            l1 = st.selectbox("1️⃣ 核心赛道", list(config.INDUSTRY_TREE.keys()))
            l2 = st.selectbox("2️⃣ 细分领域", list(config.INDUSTRY_TREE[l1].keys()))
            l3 = st.selectbox("3️⃣ 关键环节", config.INDUSTRY_TREE[l1][l2])
            
            # 拼接最终 Topic
            final_topic = f"{l2} - {l3}" if l3 != "全产业链分析" else l2
            st.info(f"当前定位: {final_topic}")
            
            # 3. 六大研究维度配置（新增）
            st.markdown("📐 **研究维度配置**")
            with st.expander("选择研究维度", expanded=False):
                dim_industry_def = st.checkbox("① 行业定义与边界", value=True)
                dim_market_size = st.checkbox("② 市场规模与趋势", value=True)
                dim_supply_chain = st.checkbox("③ 产业链结构 【重点】", value=True)
                dim_competitive = st.checkbox("④ 典型玩家与格局", value=True)
                dim_business_model = st.checkbox("⑤ 商业模式与变现", value=True)
                dim_policy = st.checkbox("⑥ 政策/科技/环境影响", value=True)
            
            # 4. 产业链分析配置（新增）
            st.markdown("🔗 **产业链分析配置**")
            supply_chain_focus = st.checkbox("重点分析产业链", value=True, help="勾选后将对产业链进行深度分析")
            
            if supply_chain_focus:
                supply_chain_depth = st.select_slider(
                    "产业链分析深度",
                    options=["快速", "标准", "深度"],
                    value="深度"
                )
                st.markdown("""
                <small>
                产业链分析将包含：<br>
                🔼 上游：原材料、零部件、供应商<br>
                ⏺️ 中游：制造、加工、技术壁垒<br>
                🔽 下游：应用场景、终端客户<br>
                💰 价值链：利润分配、投资机会
                </small>
                """, unsafe_allow_html=True)
            
            # 5. 侧重点
            st.markdown("⚖️ **研究视角**")
            sel_focus_keys = st.multiselect(
                "选择分析维度", 
                list(config.REPORT_FOCUS_MAPPING.keys()), 
                default=["VC/PE 投资价值分析", "产业链深度分析"]
            )
            focus_prompt = "\n".join([config.REPORT_FOCUS_MAPPING[k] for k in sel_focus_keys])
            
            # 如果勾选了产业链重点，自动添加产业链分析提示
            if supply_chain_focus:
                focus_prompt += "\n\n【重点】请深度分析产业链上中下游结构，识别各环节投资机会，分析价值链分配。"
            
            # 6. 年份
            target_year = st.number_input("📅 目标年份", value=2025)
            
            # 7. 知识库管理 
            st.subheader("📚 研报知识库 (Knowledge Base)")
            
            existing_files = [f for f in os.listdir(config.KNOWLEDGE_BASE_DIR) if f.lower().endswith('.pdf')]
            
            if existing_files:
                selected_file = st.selectbox(
                    f"📂 已归档研报清单 (共 {len(existing_files)} 份)",
                    options=existing_files,
                    index=0,
                    help="这些文件已存储在服务器上，Agent 分析时会自动读取。"
                )
                
                if selected_file:
                    file_path = os.path.join(config.KNOWLEDGE_BASE_DIR, selected_file)
                    try:
                        file_stats = os.stat(file_path)
                        file_size_mb = file_stats.st_size / (1024 * 1024)
                        mod_time = datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M')
                        st.caption(f"📄 详情: {file_size_mb:.2f} MB | 上传时间: {mod_time}")
                    except:
                        pass
            else:
                st.info("ℹ️ 知识库当前为空，请上传研报。")

            uploaded_files = st.file_uploader("➕ 上传新研报 (PDF)", type=["pdf"], accept_multiple_files=True)

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    save_path = os.path.join(config.KNOWLEDGE_BASE_DIR, uploaded_file.name)
                    
                    if not os.path.exists(save_path):
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        if kb_manager:
                            with st.spinner(f"正在学习 {uploaded_file.name} (向量化)..."):
                                kb_manager.ingest_pdf(save_path)
                        
                        st.toast(f"✅ 已入库并学习: {uploaded_file.name}", icon="🧠")
                    else:
                        st.toast(f"ℹ️ 文件已存在: {uploaded_file.name}")
                time.sleep(1)
                st.rerun()

            if st.button("🚀 生成深度研报", use_container_width=True):
                if not HAS_BACKEND:
                    st.error("无法调用后端，请检查 main.py")
                else:
                    with st.status("正在调用多智能体团队...", expanded=True):
                        st.write("📋 Planner: 正在基于六大维度规划研究蓝图...")
                        st.write("🔍 Researcher: 正在搜集财务、政策、产业链数据...")
                        st.write("🔗 Supply Chain Analyst: 正在深度分析产业链结构...")
                        st.write("📊 Analyst: 正在进行六维度综合分析...")
                        st.write("✍️ Writer: 正在撰写深度分析报告...")
                        st.write("🔍 Reviewer: 正在进行质量审核...")
                        try:
                            res = main.run_investment_analysis(
                                final_topic, sel_province, str(target_year), focus_prompt
                            )
                            st.session_state.ind_report = res
                            st.success("研报生成完成！")
                        except Exception as e:
                            st.error(f"运行出错: {e}")

    with col_display:
        if 'ind_report' in st.session_state:
            with st.container():
                # 显示报告统计
                report_content = st.session_state.ind_report
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("报告字数", f"{len(report_content):,} 字符")
                with col2:
                    table_count = report_content.count("|") // 10
                    st.metric("数据表格", f"约 {table_count} 个")
                with col3:
                    st.metric("生成时间", datetime.now().strftime("%H:%M:%S"))
                
                st.divider()
                
                # 下载按钮
                st.download_button(
                    label="📥 下载 Markdown 报告",
                    data=report_content,
                    file_name=f"{target_year}_{sel_province}_{final_topic}_行业研究报告.md",
                    mime="text/markdown",
                    use_container_width=True
                )
                
                st.divider()
                
                # 显示报告内容
                st.markdown(report_content)
        else:
            # 显示研究维度框架
            st.info("👈 请在左侧配置参数并点击生成")
            
            st.markdown("### 📚 六大研究维度框架")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                | 维度 | 核心问题 |
                |------|----------|
                | ① 行业定义与边界 | 这行业到底包含什么？不包含什么？ |
                | ② 市场规模与趋势 | 现在多大？未来增长吗？为什么？ |
                | ③ 产业链结构 | 谁是上游、中游、下游？谁赚钱？ |
                | ④ 典型玩家与格局 | 龙头是谁？市占率如何？ |
                | ⑤ 商业模式与变现 | 谁付钱？怎么收费？毛利高吗？ |
                | ⑥ 政策/科技/环境 | 哪些政策在左右它？新科技有冲击吗？ |
                """)
            
            with col2:
                st.markdown("""
                ### 🔗 产业链分析重点
                
                **上游分析**
                - 原材料/核心零部件供应商
                - 上游集中度与"卡脖子"环节
                - 成本占比与价格传导机制
                
                **中游分析**
                - 核心制造/加工环节
                - 技术壁垒与国产化率
                - 产能分布与竞争格局
                
                **下游分析**
                - 终端应用场景
                - 需求驱动因素
                - 客户结构分析
                """)


# ============================================================
# 模块 2: 产业链专项分析（新增）
# ============================================================
elif menu == "🔗 产业链专项分析":
    st.subheader("🔗 产业链专项深度分析")
    st.caption("专注于产业链上中下游结构分析，识别各环节投资机会")
    
    col_input, col_display = st.columns([1, 2])
    
    with col_input:
        st.markdown("#### 🎯 产业链分析参数")
        
        # 行业选择
        industry_name = st.text_input(
            "研究行业",
            value="半导体",
            placeholder="如：人工智能、新能源汽车、生物医药"
        )
        
        sel_province = st.selectbox(
            "目标区域", 
            config.PROVINCE_LIST, 
            index=config.PROVINCE_LIST.index("浙江省")
        )
        
        target_year = st.number_input("目标年份", value=2025)
        
        st.markdown("#### 🔗 产业链层级配置")
        
        # 上游配置
        st.markdown("**🔼 上游分析重点**")
        upstream_focus = st.multiselect(
            "选择上游关注点",
            ["原材料供应", "核心零部件", "设备供应商", "技术授权", "资源开采"],
            default=["原材料供应", "核心零部件"]
        )
        
        # 中游配置
        st.markdown("**⏺️ 中游分析重点**")
        midstream_focus = st.multiselect(
            "选择中游关注点",
            ["核心制造", "封装测试", "系统集成", "代工服务", "技术研发"],
            default=["核心制造", "技术研发"]
        )
        
        # 下游配置
        st.markdown("**🔽 下游分析重点**")
        downstream_focus = st.multiselect(
            "选择下游关注点",
            ["消费电子", "汽车电子", "工业应用", "通信设备", "医疗设备", "其他应用"],
            default=["消费电子", "汽车电子"]
        )
        
        st.markdown("#### 📊 分析深度配置")
        
        include_value_chain = st.checkbox("包含价值链分析", value=True)
        include_risk = st.checkbox("包含风险分析", value=True)
        include_investment = st.checkbox("包含投资机会分析", value=True)
        
        if st.button("🚀 生成产业链分析报告", use_container_width=True):
            if not HAS_BACKEND:
                st.error("无法调用后端，请检查 main.py")
            else:
                # 构建产业链分析的focus
                supply_chain_focus = f"""
                【产业链专项分析任务】
                
                请对 {industry_name} 行业进行产业链深度分析：
                
                上游重点：{', '.join(upstream_focus)}
                中游重点：{', '.join(midstream_focus)}
                下游重点：{', '.join(downstream_focus)}
                
                分析要求：
                {'- 包含价值链分析' if include_value_chain else ''}
                {'- 包含风险分析' if include_risk else ''}
                {'- 包含投资机会分析' if include_investment else ''}
                
                请重点分析产业链各环节的投资价值和风险。
                """
                
                with st.status("正在进行产业链深度分析...", expanded=True):
                    st.write("🔗 正在梳理产业链结构...")
                    st.write("🔼 正在分析上游环节...")
                    st.write("⏺️ 正在分析中游环节...")
                    st.write("🔽 正在分析下游环节...")
                    st.write("💰 正在分析价值链分配...")
                    try:
                        res = main.run_investment_analysis(
                            industry_name, sel_province, str(target_year), supply_chain_focus
                        )
                        st.session_state.supply_chain_report = res
                        st.success("产业链分析完成！")
                    except Exception as e:
                        st.error(f"运行出错: {e}")
    
    with col_display:
        if 'supply_chain_report' in st.session_state:
            report_content = st.session_state.supply_chain_report
            
            # 显示报告统计
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("报告字数", f"{len(report_content):,} 字符")
            with col2:
                st.metric("分析环节", "上游/中游/下游")
            with col3:
                st.metric("生成时间", datetime.now().strftime("%H:%M:%S"))
            
            st.divider()
            
            # 下载按钮
            st.download_button(
                label="📥 下载产业链分析报告",
                data=report_content,
                file_name=f"{target_year}_{sel_province}_{industry_name}_产业链分析报告.md",
                mime="text/markdown",
                use_container_width=True
            )
            
            st.divider()
            st.markdown(report_content)
        else:
            st.info("👈 请在左侧配置参数并点击生成")
            
            st.markdown("""
            ### 🔗 产业链分析说明
            
            产业链专项分析将深度剖析行业的上中下游结构：
            
            **上游产业链**
            - 原材料/核心零部件供应商分析
            - 上游市场集中度与"卡脖子"环节
            - 成本占比与价格传导机制
            - 国产化率与进口依赖度
            
            **中游产业链**
            - 核心制造/加工环节分析
            - 技术壁垒与核心技术掌握情况
            - 产能分布与区域竞争格局
            - 毛利率水平与盈利能力
            
            **下游产业链**
            - 终端应用场景分析
            - 各场景市场规模与增速
            - 需求驱动因素分析
            - 客户结构与集中度
            
            **价值链分析**
            - 利润在各环节的分配比例
            - 议价能力分析
            - 投资机会与价值洼地识别
            """)


# ============================================================
# 模块 3: 公司信息查询
# ============================================================
elif menu == "🏢 公司信息查询":
    st.subheader("🏢 公司全维信息查询")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        co_name = st.text_input("输入公司全称或代码", "例如：宁德时代 / 300750")
    with col2:
        st.write("")
        st.write("")
        btn_search = st.button("🔍 查询", use_container_width=True)
    
    if btn_search and HAS_BACKEND:
        with st.spinner("正在穿透工商信息与投融资记录..."):
            try:
                res = main.run_company_research(co_name)
                st.markdown(res)
            except Exception as e:
                st.error(f"查询失败: {e}")


# ============================================================
# 模块 4: 智能会议纪要
# ============================================================
elif menu == "📝 智能会议纪要":
    st.subheader("📝 智能会议纪要整理")
    
    folder_path = st.text_input("会议记录文件夹路径", "./knowledge_base/meetings")
    if st.button("开始整理"):
        if HAS_BACKEND:
            with st.spinner("正在聚合文档并提取 Action Items..."):
                res = main.run_meeting_minutes(folder_path)
                st.markdown(res)


# ============================================================
# 模块 5: BP 解读
# ============================================================
elif menu == "📑 BP 商业计划书解读":
    st.subheader("📑 商业计划书 (BP) 智能初筛")
    
    uploaded_bp = st.file_uploader("上传 BP (PDF)", type="pdf")
    if uploaded_bp and st.button("开始解读"):
        temp_path = os.path.join(config.KNOWLEDGE_BASE_DIR, uploaded_bp.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_bp.getbuffer())
            
        if HAS_BACKEND:
            with st.spinner("正在进行 SWOT 分析..."):
                res = main.run_bp_interpretation(temp_path)
                st.markdown(res)


# ============================================================
# 模块 6: 财务报表分析
# ============================================================
elif menu == "📈 财务报表深度分析":
    st.subheader("📈 财务报表深度诊断")
    
    uploaded_fin = st.file_uploader("上传财报 (PDF)", type="pdf")
    if uploaded_fin and st.button("深度分析"):
        temp_path = os.path.join(config.KNOWLEDGE_BASE_DIR, uploaded_fin.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_fin.getbuffer())
            
        if HAS_BACKEND:
            with st.spinner("CPA Agent 正在计算财务比率与排查雷区..."):
                res = main.run_financial_report_analysis(temp_path)
                st.markdown(res)


# ============================================================
# 模块 7: 尽职调查 (DD)
# ============================================================
elif menu == "⚖️ 尽职调查 (DD)":
    st.subheader("⚖️ 自动化尽职调查")
    
    c1, c2 = st.columns(2)
    target_comp = c1.text_input("目标公司名称")
    material_path = c2.text_input("尽调材料目录", config.KNOWLEDGE_BASE_DIR)
    
    if st.button("启动红旗测试 (Red Flag Check)"):
        if HAS_BACKEND:
            with st.spinner("正在交叉比对法律诉讼与内部材料..."):
                res = main.run_due_diligence(target_comp, material_path)
                st.markdown(res)


# ============================================================
# 模块 8: 财务估值建模
# ============================================================
elif menu == "💰 财务估值建模":
    st.subheader("💰 自动化估值建模 (DCF/Comps)")
    
    c1, c2 = st.columns(2)
    target_val = c1.text_input("目标公司")
    assumptions = c2.text_area("财务假设 (JSON格式)", '{"wacc": 0.12, "growth": 0.05, "cash_flows": [100, 120, 150]}')
    
    if st.button("构建模型"):
        if HAS_BACKEND:
            with st.spinner("正在进行蒙特卡洛模拟..."):
                res = main.run_financial_valuation(target_val, assumptions)
                st.markdown(res)


# ============================================================
# 模块 9: IPO 路径与退出
# ============================================================
elif menu == "🚀 IPO 路径与退出测算":
    st.subheader("🚀 IPO 可行性与退出回报测算")
    
    with st.container():
        col1, col2, col3 = st.columns(3)
        ipo_comp = col1.text_input("拟上市主体", "某科技公司")
        ipo_ind = col2.selectbox("所属行业", ["硬科技", "生物医药", "消费", "SaaS"])
        ipo_board = col3.selectbox("目标板块", ["科创板", "创业板", "北交所", "港股18C"])
        
        col4, col5 = st.columns(2)
        ipo_fin = col4.text_input("核心财务简述", "营收2亿，净利3000万，研发占比15%")
        
        if st.button("开始测算"):
            if HAS_BACKEND:
                with st.spinner("保荐人 Agent 正在对标上市条款..."):
                    res = main.run_ipo_exit_analysis(ipo_comp, ipo_fin, ipo_ind, ipo_board)
                    st.markdown(res)


# ============================================================
# 模块 10: 并购重组策略
# ============================================================
elif menu == "🤝 并购重组策略 (M&A)":
    st.subheader("🤝 并购重组交易架构设计")
    
    c1, c2, c3 = st.columns(3)
    ma_buyer = c1.text_input("收购方 (上市公司)", "A公司")
    ma_target = c2.text_input("标的方", "B项目")
    ma_role = c3.selectbox("我方角色", ["财务顾问", "并购基金LP", "定增投资人"])
    
    if st.button("设计交易方案"):
        if HAS_BACKEND:
            with st.spinner("正在设计定增/SPV/现金收购方案..."):
                res = main.run_ma_strategy(ma_buyer, ma_target, ma_role)
                st.markdown(res)


# ============================================================
# 页脚
# ============================================================
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.8em;">
    <p>FinSight AI Agent v2.0 | 基于 CrewAI 多智能体框架</p>
    <p>覆盖六大研究维度 | 重点产业链深度分析 | 支持投资决策</p>
    <p>© 2025 FinSight | 内部机密系统 | 禁止外传</p>
</div>
""", unsafe_allow_html=True)
