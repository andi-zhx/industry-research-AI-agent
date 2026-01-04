# app.py 只做 UI + 调用 main
# ==========================================
# FinSight 投研系统 · 前端入口（Streamlit）
# 仅负责 UI + 参数收集 + 调用 main.py
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
import torch

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
    page_title="FinSight 智能投研",
    page_icon="📈",
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

# 侧边栏导航
with st.sidebar:
    st.subheader("功能导航")
    
    menu = st.radio(
        "请选择业务模块:",
        [
            "📊 行业深度研究",
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


# 功能模块实现
# 模块 1: 行业深度研究 
if menu == "📊 行业深度研究":
    st.subheader("📊 行业深度研究")
    st.caption("基于四级产业链图谱的深度行业分析与报告生成")
    
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
            
            # 3. 侧重点
            st.markdown("⚖️ **研究视角**")
            sel_focus_keys = st.multiselect("选择分析维度", list(config.REPORT_FOCUS_MAPPING.keys()), default=["VC/PE 投资价值分析"])
            focus_prompt = "\n".join([config.REPORT_FOCUS_MAPPING[k] for k in sel_focus_keys])
            
            # 4. 年份与知识库
            target_year = st.number_input("📅 目标年份", value=2025)
            
            
            # 3. 知识库管理 
            st.subheader("📚 研报知识库 (Knowledge Base)")
            
            # --- [新增功能] 扫描并显示已存在的文件 ---
            # 实时扫描文件夹下的 PDF
            existing_files = [f for f in os.listdir(config.KNOWLEDGE_BASE_DIR) if f.lower().endswith('.pdf')]
            
            if existing_files:
                # 使用下拉框展示现有文件
                selected_file = st.selectbox(
                    f"📂 已归档研报清单 (共 {len(existing_files)} 份)",
                    options=existing_files,
                    index=0,
                    help="这些文件已存储在服务器上，Agent 分析时会自动读取文件夹内的所有 PDF。"
                )
                
                # [可选优化] 显示选中文件的详细信息 (如文件大小、最后修改时间)
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

            # --- 文件上传区 (保持原有功能) ---
            uploaded_files = st.file_uploader("➕ 上传新研报 (PDF)", type=["pdf"], accept_multiple_files=True)

            if uploaded_files:
                for uploaded_file in uploaded_files:
                    save_path = os.path.join(config.KNOWLEDGE_BASE_DIR, uploaded_file.name)
                    
                    # 检查文件是否已存在，避免重复 save
                    if not os.path.exists(save_path):
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 【关键一步】触发 RAG 向量化
                        with st.spinner(f"正在学习 {uploaded_file.name} (向量化)..."):
                            kb_manager.ingest_pdf(save_path) # 调用我们写的引擎
                        
                        st.toast(f"✅ 已入库并学习: {uploaded_file.name}", icon="🧠")
                    else:
                        st.toast(f"ℹ️ 文件已存在: {uploaded_file.name}")
                # 上传成功后，强制刷新一下页面，让上面的下拉框能立即显示新文件        
                time.sleep(1)
                st.rerun()

            if st.button("🚀 生成深度研报", use_container_width=True):
                if not HAS_BACKEND:
                    st.error("无法调用后端，请检查 main.py")
                else:
                    with st.status("正在调用多智能体团队...", expanded=True):
                        st.write("🕵️‍♂️ Planner: 正在拆解产业链结构...")
                        st.write("🔍 Researcher: 正在检索宏观政策与微观数据...")
                        st.write("✍️ Writer: 正在撰写深度分析报告...")
                        try:
                            # 调用 main.py
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
                st.markdown(st.session_state.ind_report)
        else:
            st.info("👈 请在左侧配置参数并点击生成")

# ------------------------------------------
# 模块 2: 公司信息查询
# ------------------------------------------
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

# ------------------------------------------
# 模块 3: 智能会议纪要
# ------------------------------------------
elif menu == "📝 智能会议纪要":
    st.subheader("📝 智能会议纪要整理")
    
    folder_path = st.text_input("会议记录文件夹路径", "./knowledge_base/meetings")
    if st.button("开始整理"):
        if HAS_BACKEND:
            with st.spinner("正在聚合文档并提取 Action Items..."):
                res = main.run_meeting_minutes(folder_path)
                st.markdown(res)

# ------------------------------------------
# 模块 4: BP 解读
# ------------------------------------------
elif menu == "📑 BP 商业计划书解读":
    st.subheader("📑 商业计划书 (BP) 智能初筛")
    
    uploaded_bp = st.file_uploader("上传 BP (PDF)", type="pdf")
    if uploaded_bp and st.button("开始解读"):
        # 保存临时文件
        temp_path = os.path.join(config.KNOWLEDGE_BASE_DIR, uploaded_bp.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_bp.getbuffer())
            
        if HAS_BACKEND:
            with st.spinner("正在进行 SWOT 分析..."):
                res = main.run_bp_interpretation(temp_path)
                st.markdown(res)

# ------------------------------------------
# 模块 5: 财务报表分析
# ------------------------------------------
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

# ------------------------------------------
# 模块 6: 尽职调查 (DD)
# ------------------------------------------
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

# ------------------------------------------
# 模块 7: 财务估值建模
# ------------------------------------------
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

# ------------------------------------------
# 模块 8: IPO 路径与退出 (新增)
# ------------------------------------------
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

# ------------------------------------------
# 模块 9: 并购重组策略 (新增)
# ------------------------------------------
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

# ==========================================
# 页脚
# ==========================================
st.divider()
st.caption("© 2025 FinSight AI agent | 内部机密系统 | 禁止外传")