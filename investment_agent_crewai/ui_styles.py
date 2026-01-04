# 存放 CSS 样式代码和 HTML 头部动画代码 渲染函数

import streamlit as st

def apply_custom_css():
    """应用全局 CSS 样式"""
    st.markdown("""
    <style>
   # 专业浅色金融风格 CSS & 顶部动态海浪
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
        }
        .stButton > button:hover {
            background-color: #1D4ED8;
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
            height: 80px; /* wave height */
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
    </style>
        """, unsafe_allow_html=True)



def render_header():
    """渲染动态海浪头部"""
    st.markdown("""
    <div class="wave-container">
        <div class="header-text">
            <div class="header-title">FinSight AI agent</div>
            <div class="header-subtitle">一级市场智能投研终端</div>
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

