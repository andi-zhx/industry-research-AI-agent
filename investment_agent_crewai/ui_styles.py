# ui_styles.py
# 存放 CSS 样式代码和 HTML 头部动画代码 渲染函数
# 增强版：支持六大研究维度和产业链分析样式

import streamlit as st


def apply_custom_css():
    """应用全局 CSS 样式"""
    st.markdown("""
    <style>
    /* 专业浅色金融风格 CSS & 顶部动态海浪 */
    /* 全局字体与背景 - 浅色系 */
    .stApp {
        background-color: #F5F7F9; /* 极浅的灰蓝色背景 */
        color: #1F2937; /* 深灰字体 */
    }
    
    /* 标题样式 - 金融蓝 */
    h1, h2, h3 {
        color: #1E3A8A !important;
        font-family: 'Helvetica Neue', 'Microsoft YaHei', sans-serif;
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E5E7EB;
    }
    
    /* 卡片容器样式 - 白色背景+阴影 */
    .css-1r6slb0, .stContainer {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    /* 按钮样式 - 专业蓝 */
    .stButton > button {
        background-color: #2563EB;
        color: white;
        border-radius: 4px;
        border: none;
        height: 45px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #1D4ED8;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    
    /* 下载按钮样式 */
    .stDownloadButton > button {
        background-color: #059669;
        color: white;
        border-radius: 4px;
        border: none;
    }
    .stDownloadButton > button:hover {
        background-color: #047857;
    }

    /* 顶部动态海浪容器 */
    .wave-container {
        width: 100%;
        height: 120px;
        background: linear-gradient(90deg, #FFFFFF 0%, #EFF6FF 100%);
        position: relative;
        overflow: hidden;
        border-bottom: 2px solid #2563EB;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 40px;
    }
    
    .header-text {
        z-index: 10;
    }
    .header-title {
        font-size: 32px;
        font-weight: 800;
        color: #1E3A8A;
        letter-spacing: 1px;
    }
    .header-subtitle {
        font-size: 14px;
        color: #64748B;
        margin-top: 4px;
    }
    
    /* 简单的 CSS 动态波浪效果 */
    .ocean { 
        height: 80px;
        width: 100%;
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        overflow-x: hidden;
    }
    .wave {
        background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 800 88.7'%3E%3Cpath d='M800 56.9c-155.5 0-204.9-50-405.5-49.9-200 0-250 49.9-394.5 49.9v31.8h800v-.2-31.6z' fill='%232563EB' opacity='0.2'/%3E%3C/svg%3E");
        position: absolute;
        width: 200%;
        height: 100%;
        animation: wave 10s -3s linear infinite;
        transform: translate3d(0, 0, 0);
        opacity: 0.8;
    }
    .wave:nth-of-type(2) {
        bottom: 0;
        animation: wave 18s linear reverse infinite;
        opacity: 0.5;
    }
    .wave:nth-of-type(3) {
        bottom: 0;
        animation: wave 20s -1s linear infinite;
        opacity: 0.5;
    }
    @keyframes wave {
        0% {transform: translateX(0);}
        100% {transform: translateX(-50%);}
    }
    
    /* ============================================================ */
    /* 六大研究维度样式（新增） */
    /* ============================================================ */
    
    /* 维度标签样式 */
    .dimension-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem;
    }
    
    .dimension-1 { background: #DBEAFE; color: #1E40AF; }
    .dimension-2 { background: #D1FAE5; color: #065F46; }
    .dimension-3 { background: #FEF3C7; color: #B45309; }
    .dimension-4 { background: #EDE9FE; color: #5B21B6; }
    .dimension-5 { background: #FCE7F3; color: #BE185D; }
    .dimension-6 { background: #CFFAFE; color: #0E7490; }
    
    /* 产业链分析框样式 */
    .supply-chain-box {
        background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #E2E8F0;
        transition: all 0.3s ease;
    }
    
    .supply-chain-box:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }
    
    .supply-chain-box.upstream {
        border-left: 4px solid #EF4444;
    }
    
    .supply-chain-box.midstream {
        border-left: 4px solid #10B981;
    }
    
    .supply-chain-box.downstream {
        border-left: 4px solid #3B82F6;
    }
    
    .supply-chain-box.value-chain {
        border-left: 4px solid #F59E0B;
    }
    
    /* 产业链图示样式 */
    .supply-chain-flow {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        padding: 1.5rem;
        background: #FFFFFF;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .chain-node {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        text-align: center;
        min-width: 120px;
    }
    
    .chain-arrow {
        color: #9CA3AF;
        font-size: 1.5rem;
    }
    
    /* 指标卡片样式 */
    [data-testid="stMetricValue"] {
        color: #2563EB;
        font-weight: 700;
    }
    
    [data-testid="stMetricLabel"] {
        color: #64748B;
        font-weight: 500;
    }
    
    /* 表格样式增强 */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        background: #FFFFFF;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    
    th {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        padding: 0.75rem 1rem;
        text-align: left;
        font-weight: 600;
    }
    
    td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #E5E7EB;
    }
    
    tr:hover {
        background-color: #F8FAFC;
    }
    
    /* 引用块样式 */
    blockquote {
        border-left: 4px solid #2563EB;
        padding-left: 1rem;
        margin: 1rem 0;
        color: #64748B;
        font-style: italic;
        background: #F8FAFC;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
    }
    
    /* 代码块样式 */
    code {
        background-color: #F1F5F9;
        padding: 0.2rem 0.4rem;
        border-radius: 4px;
        font-family: 'Consolas', 'Monaco', monospace;
        color: #1E40AF;
    }
    
    /* 进度条样式 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #2563EB 0%, #7C3AED 100%);
    }
    
    /* 展开器样式 */
    .streamlit-expanderHeader {
        background: #F8FAFC;
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* 分割线样式 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #E5E7EB, transparent);
        margin: 1.5rem 0;
    }
    
    /* 响应式调整 */
    @media (max-width: 768px) {
        .wave-container {
            height: 80px;
            padding: 0 20px;
        }
        .header-title {
            font-size: 24px;
        }
        .supply-chain-flow {
            flex-direction: column;
        }
        .chain-arrow {
            transform: rotate(90deg);
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """渲染动态海浪头部"""
    st.markdown("""
    <div class="wave-container">
        <div class="header-text">
            <div class="header-title">FinSight AI Agent</div>
            <div class="header-subtitle">一级市场智能投研终端 | 六大研究维度 | 产业链深度分析</div>
        </div>
        <div style="width: 300px; height: 100%; position: relative;">
            <div class="ocean">
                <div class="wave"></div>
                <div class="wave"></div>
                <div class="wave"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_dimension_tags():
    """渲染六大研究维度标签"""
    st.markdown("""
    <div style="margin: 1rem 0;">
        <span class="dimension-tag dimension-1">① 行业定义与边界</span>
        <span class="dimension-tag dimension-2">② 市场规模与趋势</span>
        <span class="dimension-tag dimension-3">③ 产业链结构</span>
        <span class="dimension-tag dimension-4">④ 典型玩家与格局</span>
        <span class="dimension-tag dimension-5">⑤ 商业模式与变现</span>
        <span class="dimension-tag dimension-6">⑥ 政策/科技/环境</span>
    </div>
    """, unsafe_allow_html=True)


def render_supply_chain_flow():
    """渲染产业链流程图"""
    st.markdown("""
    <div class="supply-chain-flow">
        <div class="chain-node" style="background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);">
            🔼 上游<br><small>原材料/零部件</small>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-node" style="background: linear-gradient(135deg, #10B981 0%, #059669 100%);">
            ⏺️ 中游<br><small>制造/加工</small>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-node" style="background: linear-gradient(135deg, #3B82F6 0%, #2563EB 100%);">
            🔽 下游<br><small>应用/终端</small>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_supply_chain_box(title: str, content: str, chain_type: str = "upstream"):
    """渲染产业链分析框"""
    type_class = {
        "upstream": "upstream",
        "midstream": "midstream",
        "downstream": "downstream",
        "value": "value-chain"
    }.get(chain_type, "upstream")
    
    type_icon = {
        "upstream": "🔼",
        "midstream": "⏺️",
        "downstream": "🔽",
        "value": "💰"
    }.get(chain_type, "🔼")
    
    st.markdown(f"""
    <div class="supply-chain-box {type_class}">
        <h4 style="margin: 0 0 0.5rem 0; color: #1F2937;">
            {type_icon} {title}
        </h4>
        <p style="margin: 0; color: #64748B; line-height: 1.6;">
            {content}
        </p>
    </div>
    """, unsafe_allow_html=True)


def apply_custom_styles():
    """应用所有自定义样式（兼容旧版调用）"""
    apply_custom_css()
